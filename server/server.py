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
NETWORK_SEND_NEWLINE = "\n"

# Simulation configuration
TICK_RATE_HZ = 60.0
PLAYER_SPEED_UNITS_PER_SEC = 220.0
PLAYER_RADIUS = 16.0
BULLET_SPEED_UNITS_PER_SEC = 520.0
BULLET_RADIUS = 4.0
BULLET_FIRE_COOLDOWN_SEC = 0.18
BULLET_LIFETIME_SEC = 2.0
RESPAWN_DELAY_SEC = 2.0
WIN_SCORE = 20

# World - match your laser tag arena size
WORLD_WIDTH = 1760  # 22 tiles * 80
WORLD_HEIGHT = 1280  # 16 tiles * 80


def clamp(value: float, min_value: float, max_value: float) -> float:
	return max(min_value, min(value, max_value))


def normalize_vector(x: float, y: float) -> Tuple[float, float]:
	length = math.hypot(x, y)
	if length <= 1e-6:
		return 0.0, 0.0
	return x / length, y / length


class Player:
	def __init__(self, player_id: int, team_index: int, x: float, y: float):
		self.player_id = player_id
		self.team_index = team_index
		self.x = x
		self.y = y
		self.size = PLAYER_RADIUS
		self.angle = 0.0  # Track player facing direction
		self.alive = True
		self.respawn_time = 0.0
		self.kills = 0
		
		# inputs
		self.input_up = False
		self.input_down = False
		self.input_left = False
		self.input_right = False
		self.input_shoot = False
		
		# aim target
		self.aim_angle = 0.0  # Angle in degrees
		
		# last non-zero move direction
		self.last_dir_x = 1.0
		self.last_dir_y = 0.0
		
		# shooting
		self._last_shot_time: float = 0.0

	def update_inputs(self, up: bool, down: bool, left: bool, right: bool, shoot: bool, angle: Optional[float] = None):
		self.input_up = bool(up)
		self.input_down = bool(down)
		self.input_left = bool(left)
		self.input_right = bool(right)
		self.input_shoot = bool(shoot)
		
		if angle is not None:
			try:
				self.aim_angle = float(angle)
				self.angle = self.aim_angle
			except (TypeError, ValueError):
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
		if not self.alive:
			return False
		if (now - self._last_shot_time) >= BULLET_FIRE_COOLDOWN_SEC:
			self._last_shot_time = now
			return True
		return False

	def compute_shoot_direction(self) -> Tuple[float, float]:
		# Use the angle the player is facing
		rad = math.radians(self.angle)
		dir_x = math.cos(rad)
		dir_y = math.sin(rad)
		
		# Normalize just in case
		return normalize_vector(dir_x, dir_y)

	def respawn(self, now: float):
		"""Respawn player at their team spawn"""
		self.alive = True
		self.respawn_time = 0.0
		
		# Spawn with slight randomization to avoid stacking
		if self.team_index == 0:
			self.x = random.uniform(160.0, 320.0)
			self.y = random.uniform(160.0, WORLD_HEIGHT - 160.0)
		else:
			self.x = random.uniform(WORLD_WIDTH - 320.0, WORLD_WIDTH - 160.0)
			self.y = random.uniform(160.0, WORLD_HEIGHT - 160.0)

	def die(self, now: float):
		"""Kill this player"""
		self.alive = False
		self.respawn_time = now + RESPAWN_DELAY_SEC


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
		self.team_scores = {0: 0, 1: 0}  # Track kills per team
		self.game_won = False
		self.winner_team = None

	def add_player(self, player_id: int) -> Player:
		# Assign team alternating 0/1
		team_index = self._next_team
		self._next_team = 1 - self._next_team
		
		# Spawn point per team
		if team_index == 0:
			spawn_x = random.uniform(160.0, 320.0)
			spawn_y = random.uniform(160.0, WORLD_HEIGHT - 160.0)
		else:
			spawn_x = random.uniform(WORLD_WIDTH - 320.0, WORLD_WIDTH - 160.0)
			spawn_y = random.uniform(160.0, WORLD_HEIGHT - 160.0)
		
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
				player = self.game_state.add_player(player_id)
				team_name = "GREEN" if player.team_index == 0 else "ORANGE"
				print(f"[Server] Player {player_id} joined as {team_name} team from {addr}")
			
			with self._clients_lock:
				self._clients[player_id] = conn
			
			threading.Thread(
				target=self._client_reader_loop,
				name=f"client-{player_id}-reader",
				args=(conn,),
				daemon=True,
			).start()

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
					angle = msg.get("angle", None)
					
					with self.game_state.lock:
						player = self.game_state.players.get(player_id)
						if player:
							player.update_inputs(up, down, left, right, shoot, angle)
		except Exception as e:
			print(f"[Server] Error reading from player {player_id}: {e}")
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
		print(f"[Server] Player {player_id} disconnected")

	def _tick_loop(self):
		target_dt = 1.0 / TICK_RATE_HZ
		prev_time = time.perf_counter()
		accumulator = 0.0
		
		while self._running.is_set():
			now = time.perf_counter()
			accumulator += now - prev_time
			prev_time = now
			
			while accumulator >= target_dt:
				self._fixed_update(now, target_dt)
				accumulator -= target_dt
			
			self._broadcast_state(now)
			time.sleep(0.001)

	def _fixed_update(self, now: float, dt: float):
		with self.game_state.lock:
			# Check for game over
			if not self.game_state.game_won:
				if self.game_state.team_scores[0] >= WIN_SCORE:
					self.game_state.game_won = True
					self.game_state.winner_team = 0
					print("[Server] GREEN team wins!")
				elif self.game_state.team_scores[1] >= WIN_SCORE:
					self.game_state.game_won = True
					self.game_state.winner_team = 1
					print("[Server] ORANGE team wins!")
			
			# Handle respawns
			for player in self.game_state.players.values():
				if not player.alive and player.respawn_time > 0 and now >= player.respawn_time:
					player.respawn(now)
					print(f"[Server] Player {player.player_id} respawned")
			
			# Update living players
			for player in self.game_state.players.values():
				if not player.alive:
					continue
				
				# Movement
				move_dx, move_dy = player.compute_move_direction()
				if abs(move_dx) > 1e-6 or abs(move_dy) > 1e-6:
					player.last_dir_x = move_dx
					player.last_dir_y = move_dy
				
				player.x += move_dx * PLAYER_SPEED_UNITS_PER_SEC * dt
				player.y += move_dy * PLAYER_SPEED_UNITS_PER_SEC * dt
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
				
				# Hit detection
				hit = False
				for player in self.game_state.players.values():
					if not player.alive:
						continue
					if player.team_index == bullet.team_index:
						continue
					
					r_sum = player.size + BULLET_RADIUS
					dist_sq = (player.x - bullet.x) ** 2 + (player.y - bullet.y) ** 2
					
					if dist_sq <= (r_sum * r_sum):
						# Hit!
						player.die(now)
						
						# Award kill to shooter's team
						self.game_state.team_scores[bullet.team_index] += 1
						
						# Award kill to shooter
						shooter = self.game_state.players.get(bullet.owner_id)
						if shooter:
							shooter.kills += 1
						
						team_name = "GREEN" if bullet.team_index == 0 else "ORANGE"
						score_str = f"GREEN {self.game_state.team_scores[0]} - {self.game_state.team_scores[1]} ORANGE"
						print(f"[Server] Player {bullet.owner_id} ({team_name}) killed Player {player.player_id}! Score: {score_str}")
						
						hit = True
						break
				
				if not hit:
					active_bullets.append(bullet)
			
			self.game_state.bullets = active_bullets

	def _gather_state_snapshot(self, now: float) -> dict:
		with self.game_state.lock:
			players_payload = [
				{
					"id": p.player_id,
					"team": p.team_index,
					"x": round(p.x, 2),
					"y": round(p.y, 2),
					"angle": round(p.angle, 2),
					"alive": p.alive,
					"kills": p.kills,
				}
				for p in self.game_state.players.values()
			]
			
			bullets_payload = [
				{
					"x": round(b.x, 2),
					"y": round(b.y, 2),
					"vx": round(b.vx, 2),
					"vy": round(b.vy, 2),
					"team": b.team_index,
				}
				for b in self.game_state.bullets
			]
			
			state = {
				"type": "state",
				"t": round(now, 3),
				"map": {"width": WORLD_WIDTH, "height": WORLD_HEIGHT},
				"players": players_payload,
				"bullets": bullets_payload,
				"scores": {
					"0": self.game_state.team_scores[0],
					"1": self.game_state.team_scores[1],
				},
				"game_won": self.game_state.game_won,
				"winner_team": self.game_state.winner_team,
			}
		return state

	def _broadcast_state(self, now: float):
		state = self._gather_state_snapshot(now)
		broken_ids: List[int] = []
		
		with self._clients_lock:
			for player_id, conn in self._clients.items():
				# Add player-specific data
				player_state = state.copy()
				player_state["your_id"] = player_id
				
				try:
					conn.send_json(player_state)
				except Exception:
					broken_ids.append(player_id)
		
		for pid in broken_ids:
			self._disconnect_client(pid)


def main():
	server = GameServer(SERVER_HOST, SERVER_PORT)
	server.start()
	print("[Server] Laser Tag Server started!")
	print(f"[Server] Map size: {WORLD_WIDTH}x{WORLD_HEIGHT}")
	print(f"[Server] First team to {WIN_SCORE} kills wins!")
	try:
		while True:
			time.sleep(0.25)
	except KeyboardInterrupt:
		print("\n[Server] Shutting down...")
	finally:
		server.stop()


if __name__ == "__main__":
	main()