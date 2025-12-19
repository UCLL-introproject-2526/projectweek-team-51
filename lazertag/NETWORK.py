import socket
import json
import threading
import SETTINGS

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.server = "localhost"
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
            self._reader = self.client.makefile("r", encoding="utf-8", newline="\n")
            self.connected = True
            self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
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
                    
                    # CRITICAL: Set my_id from server
                    your_id = msg.get("your_id")
                    if your_id is not None:
                        if not hasattr(SETTINGS, 'my_id') or SETTINGS.my_id != your_id:
                            SETTINGS.my_id = your_id
                            print(f"[NETWORK] My player ID: {your_id}")
                    
                    # Update scores
                    if SETTINGS.is_multiplayer:
                        scores = msg.get("scores", {})
                        if scores:
                            SETTINGS.team_kills['green'] = int(scores.get("0", 0))
                            SETTINGS.team_kills['orange'] = int(scores.get("1", 0))
                    
        except Exception:
            pass
        finally:
            self.connected = False

    def send(self, data):
        if not self.connected:
            return []

        # Send to server
        msg = {
            "type": "input",
            "x": float(data.get("x", 0)),
            "y": float(data.get("y", 0)),
            "angle": float(data.get("angle", 0)),
            "up": bool(data["keys"].get("w", False)),
            "down": bool(data["keys"].get("s", False)),
            "left": bool(data["keys"].get("a", False)),
            "right": bool(data["keys"].get("d", False)),
            "shoot": bool(data.get("is_shooting", False)),
            "weapon": str(data.get("weapon", "None"))
        }
        
        try:
            self.client.sendall((json.dumps(msg) + "\n").encode("utf-8"))
        except:
            self.connected = False
            return []

        # Get state
        with self._state_lock:
            state = self._latest_state
        
        return state.get("players", []) if state else []