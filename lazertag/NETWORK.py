import socket
import json
import threading
import SETTINGS

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # REPLACE '127.0.0.1' WITH THE SERVER IP IF PLAYING OVER INTERNET
        self.server = "0.0.0.0"
        self.port = 9001
        self.addr = (self.server, self.port)
        self.connected = False
        self._reader = None
        self._reader_thread = None
        self._state_lock = threading.Lock()
        self._latest_state = None
        self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            # Newline-delimited JSON reader
            self._reader = self.client.makefile("r", encoding="utf-8", newline="\n")
            self.connected = True
            # Start background reader for server state
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
                    break
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(msg, dict) and msg.get("type") == "state":
                    with self._state_lock:
                        self._latest_state = msg
                    # Update our client id from server if provided
                    your_id = msg.get("your_id")
                    if your_id is not None:
                        SETTINGS.my_id = your_id
                    scores = msg.get("scores")
                    if scores:
                        SETTINGS.team_kills['green'] = scores.get("0", 0)
                        SETTINGS.team_kills['orange'] = scores.get("1", 0)
        except Exception:
            pass
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
        if not self.connected:
            return []

        keys = data.get("keys", {})
        
        # 1. Send Local Data (Added 'weapon')
        msg = {
            "type": "input",
            "up": bool(keys.get("w", False)),
            "down": bool(keys.get("s", False)),
            "left": bool(keys.get("a", False)),
            "right": bool(keys.get("d", False)),
            "shoot": bool(data.get("is_shooting", False)),
            "aim_x": float(data.get("angle", 0.0)),
            "x": float(data.get("x", 0.0)),
            "y": float(data.get("y", 0.0)),
            "weapon": str(data.get("weapon", "None")) # <--- NEW: Send Weapon Name
        }
        self._send_json(msg)

        # 2. Receive Remote Data
        with self._state_lock:
            state = self._latest_state
        if not state:
            return []
        if "your_id" in state:
            SETTINGS.my_id = state["your_id"]
        players = state.get("players", [])
        out = []
        for p in players:
            try:
                team_idx = p.get("team", 0)
                team_str = "green" if team_idx == 0 else "orange"
                out.append({
                    "id": p.get("id"),
                    "team": team_str,
                    "x": p.get("x", 0.0),
                    "y": p.get("y", 0.0),
                    "angle": p.get("angle", 0.0),
                    "health": p.get("health", 100),
                    "is_shooting": p.get("is_shooting", False),
                    "keys": p.get("keys", {}),
                    "hits": p.get("hits", []),
                    "alive": p.get("alive", True),
                    "weapon": p.get("weapon", "None") # <--- NEW: Receive Weapon Name
                })
            except Exception:
                continue
        return out