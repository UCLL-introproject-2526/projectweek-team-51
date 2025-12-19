import json
import math
import socket
import threading
import time

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9001
NETWORK_SEND_NEWLINE = "\n"

TICK_RATE_HZ = 60.0
PLAYER_RADIUS = 20.0
SHOT_COOLDOWN = 0.18
HIT_RANGE = 2000.0
RESPAWN_TIME = 2.0
MAX_HEALTH = 100
DAMAGE = 25

class GameServer:
    def __init__(self):
        self.clients = {} # {pid: socket_conn}
        self.players = {} # {pid: player_data_dict}
        self.lock = threading.Lock()
        self.next_id = 1
        self.next_team = 0
        self.scores = {0: 0, 1: 0}
        self.running = True

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((SERVER_HOST, SERVER_PORT))
        s.listen()
        print(f"[Server] Laser Tag Relay Server running on {SERVER_HOST}:{SERVER_PORT}")
        
        # This thread runs the broadcast loop
        threading.Thread(target=self.broadcast_loop, daemon=True).start()
        
        while self.running:
            try:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except: break

    def handle_client(self, conn, addr):
        pid = self.next_id
        self.next_id += 1
        
        with self.lock:
            team = self.next_team
            self.next_team = 1 - self.next_team
            team_name = "GREEN" if team == 0 else "ORANGE"
            # Initialize Player Data
            self.players[pid] = {
                "id": pid, "team": team,
                "x": 0, "y": 0, "angle": 0,
                "alive": True, "health": MAX_HEALTH,
                "keys": {}, "is_shooting": False, "hits": [], "weapon": "None",
                "last_shot": 0, "respawn_timer": 0
            }
            self.clients[pid] = conn
            print(f"[Server] Player {pid} ({team_name}) connected from {addr}")

        f = conn.makefile("r", encoding="utf-8", newline="\n")
        try:
            while self.running:
                line = f.readline()
                if not line: break
                try:
                    msg = json.loads(line)
                    if msg.get("type") == "input":
                        with self.lock:
                            if pid in self.players:
                                p = self.players[pid]
                                # 1. TRUST CLIENT POSITION
                                p["x"] = float(msg.get("x", p["x"]))
                                p["y"] = float(msg.get("y", p["y"]))
                                # FIX: Read "angle" not "aim_x"
                                p["angle"] = float(msg.get("angle", p["angle"]))
                                p["keys"] = {
                                    "w": msg.get("up", False), 
                                    "a": msg.get("left", False),
                                    "s": msg.get("down", False), 
                                    "d": msg.get("right", False)
                                }
                                p["is_shooting"] = msg.get("shoot", False)
                                p["weapon"] = str(msg.get("weapon", "None"))
                                
                                # 2. CHECK SHOOTING (Server Side Hit Reg)
                                self.check_shooting(p)
                except Exception as e:
                    print(f"[Server] Error parsing message from player {pid}: {e}")
        finally:
            print(f"[Server] Player {pid} disconnected")
            with self.lock:
                self.clients.pop(pid, None)
                self.players.pop(pid, None)
            conn.close()

    def check_shooting(self, p):
        now = time.perf_counter()
        if not p["alive"] or not p["is_shooting"]: return
        if (now - p["last_shot"]) < SHOT_COOLDOWN: return
        
        p["last_shot"] = now
        print(f"[Server] Player {p['id']} fired weapon")

        # Raycast using the TRUSTED positions
        rad = math.radians(p["angle"])
        dx = math.cos(rad)
        dy = -math.sin(rad)

        best_dist = HIT_RANGE
        victim = None

        for other in self.players.values():
            if other["id"] == p["id"]: continue
            if not other["alive"]: continue
            # Don't shoot teammates
            if other["team"] == p["team"]: continue
            
            # Simple Circle Hit
            tox, toy = other["x"] - p["x"], other["y"] - p["y"]
            dist_ray = tox * dx + toy * dy
            
            if dist_ray < 0 or dist_ray > best_dist: continue
            
            cx, cy = p["x"] + dx * dist_ray, p["y"] + dy * dist_ray
            dist_sq = (other["x"] - cx)**2 + (other["y"] - cy)**2
            
            if dist_sq < (PLAYER_RADIUS * PLAYER_RADIUS):
                best_dist = dist_ray
                victim = other

        if victim:
            attacker_team = "GREEN" if p["team"] == 0 else "ORANGE"
            victim_team = "GREEN" if victim["team"] == 0 else "ORANGE"
            print(f"[Server] HIT! {attacker_team} Player {p['id']} → {victim_team} Player {victim['id']}")
            victim["health"] -= DAMAGE
            p["hits"].append(victim["id"])
            if victim["health"] <= 0:
                victim["alive"] = False
                victim["health"] = 0
                victim["respawn_timer"] = now + RESPAWN_TIME
                self.scores[p["team"]] += 1
                print(f"[Server] KILL! Score: GREEN {self.scores[0]} - {self.scores[1]} ORANGE")

    def broadcast_loop(self):
        while self.running:
            time.sleep(1.0 / TICK_RATE_HZ)
            with self.lock:
                now = time.perf_counter()
                
                # Logic: Respawn
                for p in self.players.values():
                    if not p["alive"] and now > p["respawn_timer"]:
                        p["alive"] = True
                        p["health"] = MAX_HEALTH
                        print(f"[Server] Player {p['id']} respawned")
                
                # Prepare Payload
                public_players = []
                for p in self.players.values():
                    public_players.append({
                        "id": p["id"], "team": p["team"],
                        "x": round(p["x"], 2), "y": round(p["y"], 2), 
                        "angle": round(p["angle"], 2),
                        "alive": p["alive"], "health": p["health"],
                        "is_shooting": p["is_shooting"], "keys": p["keys"],
                        "hits": p["hits"], "weapon": p["weapon"]
                    })
                    p["hits"] = [] # Clear hits after packing

                # BASE PACKET (Without ID)
                base_state = {
                    "type": "state",
                    "players": public_players,
                    "scores": self.scores
                }
                
                # --- FIX: CREATE NEW DICT FOR EACH CLIENT (not shallow copy) ---
                dead_clients = []
                for pid, conn in list(self.clients.items()):
                    try:
                        # Create a NEW dict with your_id for this specific client
                        client_packet = {
                            "type": "state",
                            "players": public_players,
                            "scores": self.scores,
                            "your_id": pid  # Each client gets their own ID
                        }
                        
                        # Serialize and send
                        data = (json.dumps(client_packet, separators=(',', ':')) + "\n").encode("utf-8")
                        conn.sendall(data)
                    except Exception as e:
                        print(f"[Server] Failed to send to player {pid}: {e}")
                        dead_clients.append(pid)
                
                # Clean up dead connections
                for pid in dead_clients:
                    self.clients.pop(pid, None)
                    self.players.pop(pid, None)

if __name__ == "__main__":
    print("[Server] Starting Laser Tag Server...")
    print("[Server] Press Ctrl+C to stop")
    try:
        GameServer().start()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")