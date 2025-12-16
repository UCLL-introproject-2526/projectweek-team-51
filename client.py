import argparse
import json
import socket
import sys
import threading
import time
from typing import Optional, Tuple

import pygame


# DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_HOST = "tunel-sdrfyidxk.volodymyr-corporation.com"

DEFAULT_SERVER_PORT = 8001
NETWORK_SEND_NEWLINE = "\n"

# Visuals
BACKGROUND_COLOR = (18, 18, 18)
TEAM_COLORS = {
	0: (66, 135, 245),  # blue-ish
	1: (235, 64, 52),   # red-ish
}
PLAYER_OUTLINE_COLOR = (245, 245, 245)
BULLET_COLORS = {
	0: (120, 170, 255),
	1: (255, 140, 140),
}

# Default window until we get map size from server
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800
SEND_INPUTS_HZ = 60.0


class NetworkClient:
	def __init__(self, host: str, port: int):
		self.host = host
		self.port = port
		self.sock: Optional[socket.socket] = None
		self.reader = None
		self.writer_lock = threading.Lock()
		self.running = threading.Event()
		self.running.set()
		self.latest_state_lock = threading.Lock()
		self.latest_state: Optional[dict] = None

	def connect(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		self.sock.connect((self.host, self.port))
		self.reader = self.sock.makefile("r", encoding="utf-8", newline=NETWORK_SEND_NEWLINE)

	def close(self):
		self.running.clear()
		try:
			if self.reader:
				self.reader.close()
		except Exception:
			pass
		try:
			if self.sock:
				self.sock.close()
		except Exception:
			pass

	def send_json(self, obj: dict):
		if not self.sock:
			return
		data = json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + NETWORK_SEND_NEWLINE
		raw = data.encode("utf-8", errors="replace")
		with self.writer_lock:
			self.sock.sendall(raw)

	def start_reader(self):
		threading.Thread(target=self._reader_loop, name="net-reader", daemon=True).start()

	def _reader_loop(self):
		try:
			while self.running.is_set():
				line = self.reader.readline()
				if not line:
					break
				try:
					msg = json.loads(line)
				except json.JSONDecodeError:
					continue
				if isinstance(msg, dict) and msg.get("type") == "state":
					with self.latest_state_lock:
						self.latest_state = msg
		except Exception:
			pass
		finally:
			self.close()


def draw_circle(surface: pygame.Surface, color: Tuple[int, int, int], center: Tuple[int, int], radius: int, width: int = 0):
	pygame.draw.circle(surface, color, center, radius, width)


def main():
	parser = argparse.ArgumentParser(description="Minimal 2D Team Shooter Client")
	parser.add_argument("--host", type=str, default=DEFAULT_SERVER_HOST, help="Server host (default: 127.0.0.1)")
	parser.add_argument("--port", type=int, default=DEFAULT_SERVER_PORT, help="Server port (default: 50007)")
	args = parser.parse_args()

	pygame.init()
	window = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT))
	pygame.display.set_caption("Minimalistic 2D Team Shooter (Client)")
	clock = pygame.time.Clock()

	net = NetworkClient(args.host, args.port)
	try:
		net.connect()
	except OSError as e:
		print(f"Failed to connect to server at {args.host}:{args.port} -> {e}")
		pygame.quit()
		sys.exit(1)
	net.start_reader()

	# Input sending thread
	def input_sender():
		target_dt = 1.0 / SEND_INPUTS_HZ
		while net.running.is_set():
			keys = pygame.key.get_pressed()
			mx, my = pygame.mouse.get_pos()
			mouse_buttons = pygame.mouse.get_pressed()
			left_click = bool(mouse_buttons[0])
			msg = {
				"type": "input",
				"up": bool(keys[pygame.K_w] or keys[pygame.K_UP]),
				"down": bool(keys[pygame.K_s] or keys[pygame.K_DOWN]),
				"left": bool(keys[pygame.K_a] or keys[pygame.K_LEFT]),
				"right": bool(keys[pygame.K_d] or keys[pygame.K_RIGHT]),
				# allow shooting with Space or Left Mouse Button
				"shoot": bool(keys[pygame.K_SPACE] or left_click),
				# provide aim target in world/screen coordinates (no camera transform)
				"aim_x": int(mx),
				"aim_y": int(my),
			}
			try:
				net.send_json(msg)
			except Exception:
				break
			time.sleep(target_dt)

	threading.Thread(target=input_sender, name="input-sender", daemon=True).start()

	current_map_size = (DEFAULT_WIDTH, DEFAULT_HEIGHT)

	def maybe_update_window_size_from_state(state: dict):
		nonlocal window, current_map_size
		try:
			new_w = int(state.get("map", {}).get("width", DEFAULT_WIDTH))
			new_h = int(state.get("map", {}).get("height", DEFAULT_HEIGHT))
			if (new_w, new_h) != current_map_size and new_w > 200 and new_h > 200:
				current_map_size = (new_w, new_h)
				window = pygame.display.set_mode(current_map_size)
		except Exception:
			pass

	# Main render loop
	running = True
	while running and net.running.is_set():
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				running = False

		window.fill(BACKGROUND_COLOR)

		# Get latest state snapshot
		with net.latest_state_lock:
			state = dict(net.latest_state) if net.latest_state is not None else None

		if state is not None:
			maybe_update_window_size_from_state(state)
			# Draw players
			for p in state.get("players", []):
				x = int(p.get("x", 0))
				y = int(p.get("y", 0))
				size = int(p.get("size", 14))
				team = int(p.get("team", 0))
				color = TEAM_COLORS.get(team, (200, 200, 200))
				draw_circle(window, color, (x, y), size, 0)
				# outline
				draw_circle(window, PLAYER_OUTLINE_COLOR, (x, y), max(1, size), 2)
			# Draw bullets
			for b in state.get("bullets", []):
				x = int(b.get("x", 0))
				y = int(b.get("y", 0))
				team = int(b.get("team", 0))
				color = BULLET_COLORS.get(team, (220, 220, 220))
				draw_circle(window, color, (x, y), 4, 0)

		pygame.display.flip()
		clock.tick(60)

	net.close()
	pygame.quit()


if __name__ == "__main__":
	main()



