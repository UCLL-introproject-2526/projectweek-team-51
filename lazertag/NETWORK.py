import socket
import json
import threading
import logging
import time
import SETTINGS

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.server = "game.volodymyr-corporation.com"
        self.port = 9001
        self.addr = (self.server, self.port)
        self.connected = False
        self._reader = None
        self._reader_thread = None
        self._state_lock = threading.Lock()
        self._latest_state = None
        self._last_send_time = 0.0
        self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            self._reader = self.client.makefile("r", encoding="utf-8", newline="\n")
            self.connected = True
            self._reader_thread = threading.Thread(target=self._reader_loop, name="net-reader", daemon=True)
            self._reader_thread.start()
            print(f"[NETWORK] Connected to {self.server}:{self.port}")
            return True
        except Exception as e:
            print(f"[NETWORK] Connection failed: {e}")
            self.connected = False
            return False

    def _reader_loop(self):
        try:
            while self.connected:
                line = self._reader.readline()
                if not line:
                    print("[NETWORK] Server closed connection")
                    break
                
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"[NETWORK] JSON decode error: {e}")
                    continue
                
                if isinstance(msg, dict) and msg.get("type") == "state":
                    with self._state_lock:
                        self._latest_state = msg
                    
                    # Get our player ID from server
                    your_id = msg.get("your_id")
                    if your_id is not None:
                        SETTINGS.my_id = your_id
                    
                    # Update scores from server
                    scores = msg.get("scores", {})
                    if scores:
                        SETTINGS.team_kills['green'] = scores.get("0", 0)
                        SETTINGS.team_kills['orange'] = scores.get("1", 0)
                    
                    # Check game won status
                    if msg.get("game_won"):
                        winner = msg.get("winner_team")
                        if winner == 0:
                            SETTINGS.game_winner = 'green'
                        elif winner == 1:
                            SETTINGS.game_winner = 'orange'
                        SETTINGS.game_won = True
                    
                    # Check if we died (our player is not alive)
                    if hasattr(SETTINGS, 'my_id'):
                        for p in msg.get("players", []):
                            if p.get("id") == SETTINGS.my_id:
                                if not p.get("alive", True):
                                    # We died - server will respawn us
                                    if not SETTINGS.player_states.get('dead', False):
                                        print("[NETWORK] You were killed!")
                                        SETTINGS.player_states['dead'] = True
                                else:
                                    # Update our position to match server (handles respawn)
                                    server_x = p.get("x", SETTINGS.player_pos[0])
                                    server_y = p.get("y", SETTINGS.player_pos[1])
                                    
                                    # Check if we were teleported (respawned)
                                    dx = abs(server_x - SETTINGS.player_pos[0])
                                    dy = abs(server_y - SETTINGS.player_pos[1])
                                    
                                    if dx > 200 or dy > 200:
                                        # Large position change = respawn
                                        print(f"[NETWORK] Respawned at ({int(server_x)}, {int(server_y)})")
                                        SETTINGS.player_pos[0] = server_x
                                        SETTINGS.player_pos[1] = server_y
                                        if hasattr(SETTINGS, 'player_rect'):
                                            SETTINGS.player_rect.centerx = server_x
                                            SETTINGS.player_rect.centery = server_y
                                        # Clear dead state
                                        SETTINGS.player_states['dead'] = False
                                break
                    
        except Exception as e:
            print(f"[NETWORK] Error in reader loop: {e}")
            logging.exception("Exception in network reader loop")
        finally:
            self.connected = False
            try:
                if self._reader:
                    self._reader.close()
            except Exception:
                pass
            try:
                self.client.close()
            except Exception:
                pass
            print("[NETWORK] Disconnected from server")

    def _send_json(self, obj: dict) -> bool:
        try:
            data = json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n"
            self.client.sendall(data.encode("utf-8", errors="replace"))
            return True
        except Exception as e:
            print(f"[NETWORK] Send failed: {e}")
            self.connected = False
            return False

    def send(self, data):
        """Send input to server and get latest game state"""
        if not self.connected:
            return []

        # Throttle sends to ~60Hz max
        now = time.time()
        if now - self._last_send_time < 0.015:  # ~60 FPS
            # Still return latest state even if we don't send
            with self._state_lock:
                state = self._latest_state
            if state:
                return self._parse_players(state)
            return []
        
        self._last_send_time = now
        
        keys = data.get("keys", {})
        
        # Send input in server format
        msg = {
            "type": "input",
            "up": bool(keys.get("w", False)),
            "down": bool(keys.get("s", False)),
            "left": bool(keys.get("a", False)),
            "right": bool(keys.get("d", False)),
            "shoot": bool(data.get("is_shooting", False)),
            "angle": float(data.get("angle", 0.0)),  # Send player facing angle
        }
        
        if not self._send_json(msg):
            return []

        # Get latest state
        with self._state_lock:
            state = self._latest_state
        
        if not state:
            return []
        
        return self._parse_players(state)

    def _parse_players(self, state):
        """Convert server player data to game format"""
        players = state.get("players", [])
        out = []
        
        for p in players:
            try:
                p_id = p.get("id")
                
                # Skip ourselves - we control our own player locally
                if hasattr(SETTINGS, 'my_id') and p_id == SETTINGS.my_id:
                    continue
                
                # Skip dead players
                if not p.get("alive", True):
                    continue
                
                team_idx = p.get("team", 0)
                team_str = "green" if team_idx == 0 else "orange"
                
                out.append({
                    "id": p_id,
                    "team": team_str,
                    "x": float(p.get("x", 0.0)),
                    "y": float(p.get("y", 0.0)),
                    "angle": float(p.get("angle", 0.0)),
                    "health": 100,  # Always full in this game mode
                    "alive": True,
                    "is_shooting": False,
                    "keys": {},
                    "hits": [],
                    "weapon": "Laser"
                })
            except Exception as e:
                print(f"[NETWORK] Error parsing player {p_id}: {e}")
                continue
        
        return out