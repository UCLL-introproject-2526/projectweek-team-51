import socket
import pickle

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # REPLACE '127.0.0.1' WITH THE SERVER IP IF PLAYING OVER INTERNET
        self.server = "127.0.0.1" 
        self.port = 5555
        self.addr = (self.server, self.port)
        self.connected = self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            print(f"[NETWORK] Connected to {self.server}")
            return True
        except Exception as e:
            print(f"[NETWORK] Connection failed: {e}")
            return False

    def send(self, data):
        """
        Sends the local player data dict to the server.
        Returns a list of data dicts for all connected players.
        """
        try:
            self.client.send(pickle.dumps(data))
            # 4096 buffer size to accommodate lists of players
            return pickle.loads(self.client.recv(4096)) 
        except socket.error as e:
            print(e)
            return []