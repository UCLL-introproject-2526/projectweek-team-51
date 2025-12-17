# network.py
import socket
import pickle

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "127.0.0.1" # REPLACE WITH YOUR SERVER IP
        self.port = 5555
        self.addr = (self.server, self.port)
        self.connected = self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            print("[NETWORK] Connected to server.")
            return True
        except Exception as e:
            print(f"[NETWORK] Connection failed: {e}")
            return False

    def send(self, data):
        """Sends local state and returns list of other players"""
        try:
            self.client.send(pickle.dumps(data))
            # Buffer size increased to 4096 to handle player lists
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            print(e)
            return []