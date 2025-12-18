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
SHOT_COOLDOWN_SEC = 0.18
HITSCAN_MAX_RANGE = 1000.0
RESPAWN_TIME_SEC = 2.0
PLAYER_MAX_HEALTH = 100
DAMAGE_PER_HIT = 25

# World
WORLD_WIDTH = 1200
WORLD_HEIGHT = 800


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
        
        # Inputs (Booleans for animation)
        self.input_up = False
        self.input_down = False
        self.input_left = False
        self.input_right = False
        self.input_shoot = False
        
        # Orientation
        self.aim_angle_deg: float = 0.0
        self.last_dir_x = 1.0
        self.last_dir_y = 0.0
        
        # Combat State
        self._last_shot_time: float = 0.0
        self.alive: bool = True
        self.health: int = PLAYER_MAX_HEALTH
        self._respawn_at: Optional[float] = None
        self.hits: List[int] = [] # List of IDs this player shot in the current frame

    def update_inputs(self, up: bool, down: bool, left: bool, right: bool, shoot: bool, angle_deg: Optional[float] = None):
        self.input_up = bool(up)
        self.input_down = bool(down)
        self.input_left = bool(left)
        self.input_right = bool(right)
        self.input_shoot = bool(shoot)
        if angle_deg is not None:
            try:
                self.aim_angle_deg = float(angle_deg)
            except (TypeError, ValueError):
                pass

    def compute_move_direction(self) -> Tuple[float, float]:
        dx = 0.0
        dy = 0.0
        if self.input_left: dx -= 1.0
        if self.input_right: dx += 1.0
        if self.input_up: dy -= 1.0
        if self.input_down: dy += 1.0
        return normalize_vector(dx, dy)

    def try_consume_shot(self, now: float) -> bool:
        if (now - self._last_shot_time) >= SHOT_COOLDOWN_SEC:
            self._last_shot_time = now
            return True
        return False

    def compute_shoot_direction(self) -> Tuple[float, float]:
        rad = math.radians(self.aim_angle_deg)
        dir_x = math.cos(rad)
        dir_y = -math.sin(rad)
        dir_x, dir_y = normalize_vector(dir_x, dir_y)
        if dir_x == 0.0 and dir_y == 0.0:
            dir_x, dir_y = normalize_vector(self.last_dir_x, self.last_dir_y)
        if dir_x == 0.0 and dir_y == 0.0:
            dir_x, dir_y = 1.0, 0.0
        return dir_x, dir_y


class GameState:
    def __init__(self):
        self.players: Dict[int, Player] = {}
        self.lock = threading.Lock()
        self._next_team = 0
        self.team_scores = {0: 0, 1: 0}

    def add_player(self, player_id: int) -> Player:
        team_index = self._next_team
        self._next_team = 1 - self._next_team
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
        self.reader = self.sock.makefile("r", encoding="utf-8", newline=NETWORK_SEND_NEWLINE)

    def send_json(self, obj: dict):
        data = json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + NETWORK_SEND_NEWLINE
        raw = data.encode("utf-8", errors="replace")
        with self.writer_lock:
            self.sock.sendall(raw)

    def close(self):
        try:
            self.reader.close()
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
        self._server_socket: Optional[socket.socket] = None

    def start(self):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen()

        threading.Thread(target=self._accept_loop, name="accept-loop", daemon=True).start()
        threading.Thread(target=self._tick_loop, name="tick-loop", daemon=True).start()

    def stop(self):
        self._running.clear()
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        with self._clients_lock:
            for conn in self._clients.values():
                conn.close()
            self._clients.clear()

    def _accept_loop(self):
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
            print(f"[Server] Client connected {addr}, ID={player_id}")

    def _allocate_player_id(self) -> int:
        new_id = self._next_player_id
        self._next_player_id += 1
        return new_id

    def _client_reader_loop(self, conn: ClientConnection):
        player_id = conn.player_id
        try:
            while self._running.is_set():
                line = conn.reader.readline()
                if not line: break
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError: continue
                
                if isinstance(msg, dict) and msg.get("type") == "input":
                    # --- Read Input Data ---
                    client_x = msg.get("x")
                    client_y = msg.get("y")
                    print(f"[Server] ID {player_id} sent: {msg}")

                    up = bool(msg.get("up", False))
                    down = bool(msg.get("down", False))
                    left = bool(msg.get("left", False))
                    right = bool(msg.get("right", False))
                    shoot = bool(msg.get("shoot", False))
                    aim_angle = msg.get("aim_x", None) # Angle in degrees

                    with self.game_state.lock:
                        player = self.game_state.players.get(player_id)
                        if player:
                            player.update_inputs(up, down, left, right, shoot, aim_angle)
                            # Note: We do NOT set player.x/y from client_x/y to prevent cheating.
                            # The server simulates position based on inputs.
        except Exception:
            pass
        finally:
            self._disconnect_client(player_id)

    def _disconnect_client(self, player_id: int):
        with self._clients_lock:
            conn = self._clients.pop(player_id, None)
        with self.game_state.lock:
            self.game_state.remove_player(player_id)
        if conn: conn.close()
        print(f"[Server] Client {player_id} disconnected")

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
            for player in self.game_state.players.values():
                player.hits.clear() # Reset hit confirmations for this tick

                # Respawn Logic
                if not player.alive:
                    if player._respawn_at is not None and now >= player._respawn_at:
                        if player.team_index == 0:
                            player.x = random.uniform(80.0, 200.0)
                            player.y = random.uniform(80.0, WORLD_HEIGHT - 80.0)
                        else:
                            player.x = random.uniform(WORLD_WIDTH - 200.0, WORLD_WIDTH - 80.0)
                            player.y = random.uniform(80.0, WORLD_HEIGHT - 80.0)
                        player.alive = True
                        player.health = PLAYER_MAX_HEALTH
                        player._respawn_at = None
                    continue

                # Movement Logic
                move_dx, move_dy = player.compute_move_direction()
                if abs(move_dx) > 1e-6 or abs(move_dy) > 1e-6:
                    player.last_dir_x = move_dx
                    player.last_dir_y = move_dy
                player.x += move_dx * PLAYER_SPEED_UNITS_PER_SEC * dt
                player.y += move_dy * PLAYER_SPEED_UNITS_PER_SEC * dt
                player.x = clamp(player.x, player.size, WORLD_WIDTH - player.size)
                player.y = clamp(player.y, player.size, WORLD_HEIGHT - player.size)

                # Shooting Logic
                if player.input_shoot and player.try_consume_shot(now):
                    dir_x, dir_y = player.compute_shoot_direction()
                    origin_x = player.x + dir_x * (player.size + 1.0)
                    origin_y = player.y + dir_y * (player.size + 1.0)
                    
                    closest_t = None
                    closest_victim: Optional[Player] = None
                    
                    # Check hits against all other players
                    for other in self.game_state.players.values():
                        if other.player_id == player.player_id: continue
                        if other.team_index == player.team_index: continue # No Friendly Fire
                        if not other.alive: continue
                        
                        hit_t = self._ray_hits_circle(origin_x, origin_y, dir_x, dir_y, other.x, other.y, other.size)
                        if hit_t is None or hit_t > HITSCAN_MAX_RANGE: continue
                        
                        if closest_t is None or hit_t < closest_t:
                            closest_t = hit_t
                            closest_victim = other
                    
                    # Apply Damage
                    if closest_victim is not None:
                        closest_victim.health -= DAMAGE_PER_HIT
                        player.hits.append(closest_victim.player_id) # Record hit for client
                        
                        if closest_victim.health <= 0:
                            closest_victim.health = 0
                            closest_victim.alive = False
                            closest_victim._respawn_at = now + RESPAWN_TIME_SEC
                            self.game_state.team_scores[player.team_index] += 1

    def _gather_state_snapshot(self, now: float) -> dict:
        with self.game_state.lock:
            # --- CONSTRUCTING THE RESPONSE JSON ---
            players_payload = [
                {
                    "id": p.player_id,
                    "team": p.team_index,
                    "x": round(p.x, 3),
                    "y": round(p.y, 3),
                    "angle": round(p.aim_angle_deg, 2),
                    "alive": p.alive,
                    "health": p.health,          # Health (0-100)
                    "is_shooting": p.input_shoot,# Shooting Boolean
                    "keys": {                    # Movement Keys
                        "w": p.input_up,
                        "a": p.input_left,
                        "s": p.input_down,
                        "d": p.input_right
                    },
                    "hits": p.hits               # Who they shot this frame
                }
                for p in self.game_state.players.values()
            ]
            scores_payload = {"green": self.game_state.team_scores.get(0, 0), "orange": self.game_state.team_scores.get(1, 0)}
        
        return {
            "type": "state",
            "t": now,
            "players": players_payload,
            "scores": scores_payload,
        }

    def _broadcast_state(self, now: float):
        base_state = self._gather_state_snapshot(now)
        broken_ids = []
        with self._clients_lock:
            for player_id, conn in self._clients.items():
                try:
                    state = dict(base_state)
                    state["your_id"] = player_id
                    conn.send_json(state)
                except Exception:
                    broken_ids.append(player_id)
        for pid in broken_ids:
            self._disconnect_client(pid)

    @staticmethod
    def _ray_hits_circle(ox: float, oy: float, dx: float, dy: float, cx: float, cy: float, radius: float) -> Optional[float]:
        fx = cx - ox
        fy = cy - oy
        t = fx * dx + fy * dy
        if t < 0: return None
        closest_x = ox + dx * t
        closest_y = oy + dy * t
        dist_sq = (closest_x - cx) ** 2 + (closest_y - cy) ** 2
        if dist_sq > (radius * radius): return None
        return t - math.sqrt(max(0.0, (radius * radius) - dist_sq))

if __name__ == "__main__":
    GameServer(SERVER_HOST, SERVER_PORT).start()
    try:
        while True: time.sleep(0.25)
    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")