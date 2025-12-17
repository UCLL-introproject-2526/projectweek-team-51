import json
import math
import random
import socket
import threading
import time
from typing import Dict, List, Optional, Tuple


# Network configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9001
NETWORK_SEND_NEWLINE = "\n"  # newline-delimited JSON messages

# Simulation configuration
TICK_RATE_HZ = 60.0
PLAYER_SPEED_UNITS_PER_SEC = 220.0
PLAYER_RADIUS = 16.0
BULLET_SPEED_UNITS_PER_SEC = 520.0
BULLET_RADIUS = 4.0
BULLET_FIRE_COOLDOWN_SEC = 0.18
BULLET_LIFETIME_SEC = 2.0

# World
WORLD_WIDTH = 1200
WORLD_HEIGHT = 800


def clamp(value: float, min_value: float, max_value: float) -> float:
	"""Clamp value between min_value and max_value."""
	return max(min_value, min(value, max_value))


def normalize_vector(x: float, y: float) -> Tuple[float, float]:
	length = math.hypot(x, y)
	if length <= 1e-6:
		return 0.0, 0.0
	return x / length, y / length


class Player:
	def __init__(self, player_id: int, team_index: int, x: float, y: float):
		self.player_id = player_id
		self.team_index = team_index  # 0 or 1
		self.x = x
		self.y = y
		self.size = PLAYER_RADIUS
		# inputs
		self.input_up = False
		self.input_down = False
		self.input_left = False
		self.input_right = False
		self.input_shoot = False
		# last aim target (screen/world coords from client; we treat as world coords)
		self.aim_target_x = x
		self.aim_target_y = y
		# last non-zero move direction (used for shooting direction)
		self.last_dir_x = 1.0
		self.last_dir_y = 0.0
		# rate limiting for shooting
		self._last_shot_time: float = 0.0

	def update_inputs(self, up: bool, down: bool, left: bool, right: bool, shoot: bool, aim_x: Optional[float] = None, aim_y: Optional[float] = None):
		self.input_up = bool(up)
		self.input_down = bool(down)
		self.input_left = bool(left)
		self.input_right = bool(right)
		self.input_shoot = bool(shoot)
		# update aim if provided
		if aim_x is not None and aim_y is not None:
			try:
				self.aim_target_x = float(aim_x)
				self.aim_target_y = float(aim_y)
			except (TypeError, ValueError):
				# ignore invalid aim values
				pass

	def compute_move_direction(self) -> Tuple[float, float]:
		dx = 0.0
		dy = 0.0
		if self.input_left:
			dx -= 1.0
		if self.input_right:
			dx += 1.0
		if self.input_up:
			dy -= 1.0
		if self.input_down:
			dy += 1.0
		return normalize_vector(dx, dy)

	def try_consume_shot(self, now: float) -> bool:
		if (now - self._last_shot_time) >= BULLET_FIRE_COOLDOWN_SEC:
			self._last_shot_time = now
			return True
		return False

	def compute_shoot_direction(self) -> Tuple[float, float]:
		# Prefer aiming toward the latest mouse target.
		dir_x, dir_y = normalize_vector(self.aim_target_x - self.x, self.aim_target_y - self.y)
		if dir_x == 0.0 and dir_y == 0.0:
			# Fall back to last movement direction
			dir_x, dir_y = normalize_vector(self.last_dir_x, self.last_dir_y)
		if dir_x == 0.0 and dir_y == 0.0:
			# As a final fallback, shoot to the right
			dir_x, dir_y = 1.0, 0.0
		return dir_x, dir_y


class Bullet:
	def __init__(self, owner_id: int, team_index: int, x: float, y: float, vx: float, vy: float, spawned_at: float):
		self.owner_id = owner_id
		self.team_index = team_index
		self.x = x
		self.y = y
		self.vx = vx
		self.vy = vy
		self.speed = math.hypot(vx, vy)
		self.spawned_at = spawned_at

	def is_expired(self, now: float) -> bool:
		return (now - self.spawned_at) > BULLET_LIFETIME_SEC


class GameState:
	def __init__(self):
		self.players: Dict[int, Player] = {}
		self.bullets: List[Bullet] = []
		self.lock = threading.Lock()
		self._next_team = 0

	def add_player(self, player_id: int) -> Player:
		# Assign team alternating 0/1
		team_index = self._next_team
		self._next_team = 1 - self._next_team
		# Spawn point per team (left/right)
		if team_index == 0:
			spawn_x = random.uniform(80.0, 200.0)
			spawn_y = random.uniform(80.0, WORLD_HEIGHT - 80.0)
		else:
			spawn_x = random.uniform(WORLD_WIDTH - 200.0, WORLD_WIDTH - 80.0)
			spawn_y = random.uniform(80.0, WORLD_HEIGHT - 80.0)
		player = Player(player_id, team_index, spawn_x, spawn_y)
		self.players[player_id] = player
		return player

	def remove_player(self, player_id: int):
		self.players.pop(player_id, None)


class ClientConnection:
	def __init__(self, sock: socket.socket, address: Tuple[str, int], player_id: int):
		self.sock = sock
		self.address = address
		self.player_id = player_id
		self.writer_lock = threading.Lock()
		# Buffered reader for newline-delimited JSON
		self.reader = self.sock.makefile("r", encoding="utf-8", newline=NETWORK_SEND_NEWLINE)

	def send_json(self, obj: dict):
		data = json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + NETWORK_SEND_NEWLINE
		raw = data.encode("utf-8", errors="replace")
		with self.writer_lock:
			self.sock.sendall(raw)

	def close(self):
		try:
			self.reader.close()
		except Exception:
			pass
		try:
			self.sock.close()
		except Exception:
			pass


class GameServer:
	def __init__(self, host: str, port: int):
		self.host = host
		self.port = port
		self.game_state = GameState()
		self._clients: Dict[int, ClientConnection] = {}
		self._clients_lock = threading.Lock()
		self._next_player_id = 1
		self._running = threading.Event()
		self._running.set()
		self._tick_thread: Optional[threading.Thread] = None
		self._accept_thread: Optional[threading.Thread] = None
		self._server_socket: Optional[socket.socket] = None

	def start(self):
		self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._server_socket.bind((self.host, self.port))
		self._server_socket.listen()

		self._accept_thread = threading.Thread(target=self._accept_loop, name="accept-loop", daemon=True)
		self._accept_thread.start()

		self._tick_thread = threading.Thread(target=self._tick_loop, name="tick-loop", daemon=True)
		self._tick_thread.start()

	def stop(self):
		self._running.clear()
		if self._server_socket:
			try:
				self._server_socket.close()
			except Exception:
				pass
		# Close all clients
		with self._clients_lock:
			for conn in list(self._clients.values()):
				conn.close()
			self._clients.clear()

	def _accept_loop(self):
		assert self._server_socket is not None
		print(f"[Server] Listening on {self.host}:{self.port}")
		while self._running.is_set():
			try:
				client_sock, addr = self._server_socket.accept()
				client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
			except OSError:
				break
			player_id = self._allocate_player_id()
			conn = ClientConnection(client_sock, addr, player_id)
			with self.game_state.lock:
				self.game_state.add_player(player_id)
			with self._clients_lock:
				self._clients[player_id] = conn
			threading.Thread(
				target=self._client_reader_loop,
				name=f"client-{player_id}-reader",
				args=(conn,),
				daemon=True,
			).start()
			print(f"[Server] Client connected {addr}, assigned player_id={player_id}")

	def _allocate_player_id(self) -> int:
		new_id = self._next_player_id
		self._next_player_id += 1
		return new_id

	def _client_reader_loop(self, conn: ClientConnection):
		player_id = conn.player_id
		try:
			while self._running.is_set():
				line = conn.reader.readline()
				if not line:
					break
				try:
					msg = json.loads(line)
				except json.JSONDecodeError:
					continue
				if not isinstance(msg, dict):
					continue
				if msg.get("type") == "input":
					up = bool(msg.get("up", False))
					down = bool(msg.get("down", False))
					left = bool(msg.get("left", False))
					right = bool(msg.get("right", False))
					shoot = bool(msg.get("shoot", False))
					aim_x = msg.get("aim_x", None)
					aim_y = msg.get("aim_y", None)
					with self.game_state.lock:
						player = self.game_state.players.get(player_id)
						if player:
							player.update_inputs(up, down, left, right, shoot, aim_x, aim_y)
				# ignore other message types
		except Exception:
			pass
		finally:
			self._disconnect_client(player_id)

	def _disconnect_client(self, player_id: int):
		with self._clients_lock:
			conn = self._clients.pop(player_id, None)
		with self.game_state.lock:
			self.game_state.remove_player(player_id)
		if conn:
			try:
				conn.close()
			except Exception:
				pass
		print(f"[Server] Client {player_id} disconnected")

	def _tick_loop(self):
		target_dt = 1.0 / TICK_RATE_HZ
		prev_time = time.perf_counter()
		accumulator = 0.0
		while self._running.is_set():
			now = time.perf_counter()
			accumulator += now - prev_time
			prev_time = now
			# Run fixed-step updates
			while accumulator >= target_dt:
				self._fixed_update(now, target_dt)
				accumulator -= target_dt
			# Send latest state after an update step
			self._broadcast_state(now)
			# Sleep briefly to avoid busy loop
			time.sleep(0.001)

	def _fixed_update(self, now: float, dt: float):
		with self.game_state.lock:
			# Update players
			for player in self.game_state.players.values():
				move_dx, move_dy = player.compute_move_direction()
				if abs(move_dx) > 1e-6 or abs(move_dy) > 1e-6:
					player.last_dir_x = move_dx
					player.last_dir_y = move_dy
				player.x += move_dx * PLAYER_SPEED_UNITS_PER_SEC * dt
				player.y += move_dy * PLAYER_SPEED_UNITS_PER_SEC * dt
				# Keep inside world bounds
				player.x = clamp(player.x, player.size, WORLD_WIDTH - player.size)
				player.y = clamp(player.y, player.size, WORLD_HEIGHT - player.size)
				# Shooting
				if player.input_shoot and player.try_consume_shot(now):
					dir_x, dir_y = player.compute_shoot_direction()
					start_x = player.x + dir_x * (player.size + BULLET_RADIUS + 1.0)
					start_y = player.y + dir_y * (player.size + BULLET_RADIUS + 1.0)
					vx = dir_x * BULLET_SPEED_UNITS_PER_SEC
					vy = dir_y * BULLET_SPEED_UNITS_PER_SEC
					self.game_state.bullets.append(
						Bullet(player.player_id, player.team_index, start_x, start_y, vx, vy, now)
					)
			# Update bullets
			active_bullets: List[Bullet] = []
			for bullet in self.game_state.bullets:
				if bullet.is_expired(now):
					continue
				bullet.x += bullet.vx * dt
				bullet.y += bullet.vy * dt
				# Out of bounds
				if bullet.x < -10 or bullet.x > WORLD_WIDTH + 10 or bullet.y < -10 or bullet.y > WORLD_HEIGHT + 10:
					continue
				# Collisions with players (opposite team)
				hit = False
				for player in self.game_state.players.values():
					if player.team_index == bullet.team_index:
						continue
					r_sum = player.size + BULLET_RADIUS
					if (player.x - bullet.x) ** 2 + (player.y - bullet.y) ** 2 <= (r_sum * r_sum):
						# "Respawn" the player to their team spawn
						if player.team_index == 0:
							player.x = random.uniform(80.0, 200.0)
							player.y = random.uniform(80.0, WORLD_HEIGHT - 80.0)
						else:
							player.x = random.uniform(WORLD_WIDTH - 200.0, WORLD_WIDTH - 80.0)
							player.y = random.uniform(80.0, WORLD_HEIGHT - 80.0)
						hit = True
						break
				if not hit:
					active_bullets.append(bullet)
			self.game_state.bullets = active_bullets

	def _gather_state_snapshot(self, now: float) -> dict:
		# Note: only include fields necessary for rendering/logic on the client
		with self.game_state.lock:
			players_payload = [
				{
					"id": p.player_id,
					"team": p.team_index,
					"x": round(p.x, 3),
					"y": round(p.y, 3),
					"size": p.size,
				}
				for p in self.game_state.players.values()
			]
			bullets_payload = [
				{
					"x": round(b.x, 3),
					"y": round(b.y, 3),
					"vx": round(b.vx, 3),
					"vy": round(b.vy, 3),
					"speed": round(b.speed, 3),
					"team": b.team_index,
				}
				for b in self.game_state.bullets
			]
		state = {
			"type": "state",
			"t": now,
			"map": {"width": WORLD_WIDTH, "height": WORLD_HEIGHT},
			"players": players_payload,
			"bullets": bullets_payload,
		}
		return state

	def _broadcast_state(self, now: float):
		state = self._gather_state_snapshot(now)
		# Broadcast to all clients; remove broken connections
		broken_ids: List[int] = []
		with self._clients_lock:
			for player_id, conn in self._clients.items():
				try:
					conn.send_json(state)
				except Exception:
					broken_ids.append(player_id)
		for pid in broken_ids:
			self._disconnect_client(pid)


def main():
	server = GameServer(SERVER_HOST, SERVER_PORT)
	server.start()
	try:
		while True:
			time.sleep(0.25)
	except KeyboardInterrupt:
		print("\n[Server] Shutting down...")
	finally:
		server.stop()


if __name__ == "__main__":
	main()



