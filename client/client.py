# client/client.py
import socket
import threading
import json
import time
import math
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import argparse
import os
import sys
import requests

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# REST API configuration
API_BASE_URL = os.environ.get('VIE_API_URL', 'http://localhost:8080/vie-webservice/api/vies')

# Ensure project root is on sys.path before importing project modules so
# running this file from the `client/` directory imports the top-level
# `entities` package (and `game`) instead of `client/entities`.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import SERVER_HOST, SERVER_PORT
from renderer import GameRenderer
# from entities.ball import Ball
# from entities.paddle import Paddle

# Network helper functions
def send_json(sock, data):
    try:
        msg = json.dumps(data) + "\n"
        sock.sendall(msg.encode())
    except Exception:
        pass

class VieEditor:
    """Sidebar widget for editing piece HP values via REST API"""
    def __init__(self, parent, game=None):
        self.game = game  # Reference to Game instance (for local mode)
        self.frame = tk.Frame(parent, bg="#2b2b2b", width=250)
        self.frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.frame.pack_propagate(False)
        
        # Title
        title = tk.Label(self.frame, text="Gestion des Vies", bg="#2b2b2b", fg="#ffffff", font=("Arial", 14, "bold"))
        title.pack(pady=(10, 5))
        
        # Refresh button
        self.refresh_btn = tk.Button(self.frame, text="🔄 Actualiser", command=self.load_pieces, bg="#3a3a3a", fg="#ffffff")
        self.refresh_btn.pack(pady=5, padx=10, fill=tk.X)
        
        # Scrollable frame for pieces
        canvas = tk.Canvas(self.frame, bg="#2b2b2b", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#2b2b2b")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=5)
        scrollbar.pack(side="right", fill="y")
        
        # Store piece entries: {lid: (libelle_label, entry_widget, data)}
        self.piece_entries = {}
        
        # Save all button
        self.save_btn = tk.Button(self.frame, text="💾 Sauvegarder Tout", command=self.save_all, bg="#4a7c59", fg="#ffffff", font=("Arial", 11, "bold"))
        self.save_btn.pack(side=tk.BOTTOM, pady=10, padx=10, fill=tk.X)
        
        # Status label
        self.status_label = tk.Label(self.frame, text="", bg="#2b2b2b", fg="#ffffff", font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, pady=5)
        
        # Delay auto-load until after mainloop starts to avoid segfault
        self.frame.after(100, self.load_pieces)
    
    def load_pieces(self):
        """Fetch pieces from REST API and populate the list"""
        try:
            response = requests.get(API_BASE_URL, timeout=5)
            response.raise_for_status()
        
            pieces = response.json()
            
            # Clear existing entries
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.piece_entries.clear()
            
            # Create entry for each piece
            for piece in pieces:
                lid = piece.get('lid')
                libelle = piece.get('libelle', '')
                hp = piece.get('nombreVieInitiale', 0)
                
                # Frame per piece
                piece_frame = tk.Frame(self.scrollable_frame, bg="#3a3a3a", relief=tk.RAISED, borderwidth=1)
                piece_frame.pack(fill=tk.X, padx=5, pady=5)
                
                # Libelle label
                lbl = tk.Label(piece_frame, text=libelle, bg="#3a3a3a", fg="#ffffff", font=("Arial", 10, "bold"), anchor="w")
                lbl.pack(fill=tk.X, padx=5, pady=(5, 2))
                
                # HP entry
                hp_frame = tk.Frame(piece_frame, bg="#3a3a3a")
                hp_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
                
                hp_label = tk.Label(hp_frame, text="HP:", bg="#3a3a3a", fg="#cccccc", font=("Arial", 9))
                hp_label.pack(side=tk.LEFT, padx=(0, 5))
                
                entry = tk.Entry(hp_frame, width=8, font=("Arial", 10))
                entry.insert(0, str(hp))
                entry.pack(side=tk.LEFT, padx=(0, 5))
                
                # Individual save button
                save_btn = tk.Button(hp_frame, text="💾", command=lambda l=lid: self.save_piece(l), bg="#4a7c59", fg="#ffffff", width=3)
                save_btn.pack(side=tk.LEFT)
                
                # Store reference
                self.piece_entries[lid] = (lbl, entry, piece)
            
            self.status_label.config(text=f"✓ {len(pieces)} pièces chargées", fg="#4a7c59")
            logger.info(f"Loaded {len(pieces)} pieces from API")
            
        except Exception as e:
            self.status_label.config(text=f"✗ Erreur: {str(e)[:30]}...", fg="#c94c4c")
            logger.error(f"Failed to load pieces: {e}")
    
    def save_piece(self, lid):
        """Save a single piece via PUT request"""
        if lid not in self.piece_entries:
            return
        
        lbl, entry, original_data = self.piece_entries[lid]
        try:
            new_hp = int(entry.get())
            if new_hp < 0:
                raise ValueError("HP cannot be negative")
            
            # Prepare PUT data
            data = {
                'libelle': original_data['libelle'],
                'nombreVieInitiale': new_hp
            }
            
            response = requests.put(f"{API_BASE_URL}/{lid}", json=data, timeout=5)
            response.raise_for_status()
            
            # Update stored data
            original_data['nombreVieInitiale'] = new_hp
            self.status_label.config(text=f"✓ {original_data['libelle']} mis à jour", fg="#4a7c59")
            logger.info(f"Updated piece {lid}: {original_data['libelle']} -> {new_hp} HP")
            
            # Refresh game HP values if game instance is available
            if self.game is not None:
                try:
                    self.game.refresh_hp_from_api()
                    logger.info("Game HP values refreshed after save")
                except Exception as e:
                    logger.error(f"Failed to refresh game HP: {e}")
            
        except ValueError as e:
            self.status_label.config(text="✗ Valeur HP invalide", fg="#c94c4c")
            logger.error(f"Invalid HP value for piece {lid}: {e}")
        except Exception as e:
            self.status_label.config(text=f"✗ Erreur sauvegarde: {str(e)[:20]}...", fg="#c94c4c")
            logger.error(f"Failed to save piece {lid}: {e}")
    
    def save_all(self):
        """Save all modified pieces"""
        success_count = 0
        error_count = 0
        
        for lid in self.piece_entries:
            lbl, entry, original_data = self.piece_entries[lid]
            try:
                new_hp = int(entry.get())
                if new_hp < 0:
                    raise ValueError("HP cannot be negative")
                
                data = {
                    'libelle': original_data['libelle'],
                    'nombreVieInitiale': new_hp
                }
                
                response = requests.put(f"{API_BASE_URL}/{lid}", json=data, timeout=5)
                response.raise_for_status()
                
                original_data['nombreVieInitiale'] = new_hp
                success_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to save piece {lid}: {e}")
        
        if error_count == 0:
            self.status_label.config(text=f"✓ {success_count} pièce(s) sauvegardée(s)", fg="#4a7c59")
        else:
            self.status_label.config(text=f"⚠ {success_count} OK, {error_count} erreur(s)", fg="#e6a23c")
        
        # Refresh game HP values if game instance is available
        if self.game is not None and success_count > 0:
            try:
                self.game.refresh_hp_from_api()
                logger.info("Game HP values refreshed after save all")
            except Exception as e:
                logger.error(f"Failed to refresh game HP: {e}")

class ClientApp:
    FRAME_RATE = 30
    FRAME_DT = 1.0 / FRAME_RATE

    def __init__(self, master, mode="network"):
        """
        mode: 'network' or 'local'
        - network: existing behavior (connects to server and sends commands)
        - local: runs `Game()` locally in-process and renders it; uses same renderer
        """
        self.master = master
        self.mode = mode
        self.master.title("Pong Client" + (" (Local)" if mode == "local" else ""))
        
        # Main container
        main_container = tk.Frame(master)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Game area (left/center) - create first
        game_area = tk.Frame(main_container)
        game_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.renderer = GameRenderer(game_area)
        # control frame below canvas
        self.ctrl_frame = tk.Frame(game_area)
        self.ctrl_frame.pack(fill=tk.X)
        self.new_game_btn = tk.Button(self.ctrl_frame, text="Nouvelle partie", command=lambda: self.send_control('new_game'))
        self.new_game_btn.pack(side=tk.LEFT, padx=6, pady=6)
        # Pause / Resume button
        self.pause_btn = tk.Button(self.ctrl_frame, text="Pause (P)", command=lambda: self.toggle_pause())
        self.pause_btn.pack(side=tk.LEFT, padx=6, pady=6)
        # Extra dimensions input (optional): supports even values like 2,4,6,8
        self.dims_label = tk.Label(self.ctrl_frame, text="Dimensions (2,4,6,8):")
        self.dims_label.pack(side=tk.LEFT, padx=(12,4))
        self.dims_entry = tk.Entry(self.ctrl_frame, width=6)
        self.dims_entry.pack(side=tk.LEFT, padx=(0,4))
        self.dims_apply = tk.Button(self.ctrl_frame, text="Appliquer", command=lambda: self.apply_dimensions())
        self.dims_apply.pack(side=tk.LEFT, padx=(0,6))
        # Trajectory selection buttons (for player 1 only, at game start)
        # self.trajectory_label = tk.Label(self.ctrl_frame, text="Traj:")
        # self.trajectory_label.pack(side=tk.LEFT, padx=(12,4))
        # self.traj_left_btn = tk.Button(self.ctrl_frame, text="Gauche", command=lambda: self.choose_trajectory('left'), width=7)
        # self.traj_left_btn.pack(side=tk.LEFT, padx=2)
        # self.traj_center_btn = tk.Button(self.ctrl_frame, text="Centre", command=lambda: self.choose_trajectory('center'), width=7)
        # self.traj_center_btn.pack(side=tk.LEFT, padx=2)
        # self.traj_right_btn = tk.Button(self.ctrl_frame, text="Droite", command=lambda: self.choose_trajectory('right'), width=7)
        # self.traj_right_btn.pack(side=tk.LEFT, padx=2)
        # overlay label for game over messages
        self.overlay_label = None
        self.sock = None
        self.player = None  # 1 or 2 as assigned by server (network mode)
        self.connected = False
        # paused state (client-side for UI; server authoritative in network mode)
        self.paused = False
        self.running = True
        self.state = {
            "width": 800,
            "height": 600,
            "ball": {},
            "paddles": [{}, {}],
            "scores": [0,0]
        }
        self.state_lock = threading.Lock()
        # command to send: 'left'/'right'/'stop' (network mode uses single cmd sent to server)
        self.current_cmd = "stop"
        self.key_pressed = set()

        # Local mode specific
        if self.mode == "local":
            # import Game lazily so network-only clients don't import/run game logic
            from game import Game
            self.game = Game()
            # commands per player index used by Game.update: 0 (top), 1 (bottom)
            self.local_commands = {0: "stop", 1: "stop"}
            # Create VieEditor with game reference (after game is initialized)
            self.vie_editor = VieEditor(main_container, game=self.game)
            # trajectory selection angle in degrees (default = down)
            self.traj_angle = 270.0
            self.traj_canvas_id = None
            self.waiting_trajectory = False
            # no sector restriction: player 1 may choose any launch angle
            # allow full-angle selection by default
            self.traj_min = 0.0
            self.traj_max = 360.0
            # pause handled locally in local mode
            self.paused = False
        else:
            self.game = None
            self.local_commands = None
            self.traj_angle = 270.0
            self.traj_canvas_id = None
            self.waiting_trajectory = False
            # no sector restriction: player 1 may choose any launch angle
            self.traj_min = 0.0
            self.traj_max = 360.0
            self.paused = False
            # Create VieEditor without game reference (network mode)
            self.vie_editor = VieEditor(main_container, game=None)

        # bind keys
        self.master.bind("<KeyPress>", self.on_key_press)
        self.master.bind("<KeyRelease>", self.on_key_release)

        # network connect if needed (run in background to avoid blocking GUI)
        if self.mode == "network":
            t_conn = threading.Thread(target=self.connect_to_server, daemon=True)
            t_conn.start()

        # start update/render loop
        self.last_render = time.time()
        self.master.after(int(self.FRAME_DT*1000), self.render_loop)

    def connect_to_server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Reduce latency for small packets and increase buffers
            try:
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            except Exception:
                pass
            s.connect((SERVER_HOST, SERVER_PORT))
            self.sock = s
            self.connected = True
            # wait for assign message (blocking read until newline)
            buffer = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                buffer += data
                if b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    try:
                        msg = json.loads(line.decode())
                        if msg.get("type") == "assign":
                            self.player = msg.get("player")
                            print("Assigned player:", self.player)
                            # start the background reader to receive state updates
                            t = threading.Thread(target=self.network_reader, daemon=True)
                            t.start()
                            break
                    except Exception:
                        continue
        except Exception as e:
            print("Failed to connect to server:", e)
            self.connected = False
            self.sock = None

    def network_reader(self):
        buffer = b""
        try:
            while self.running and self.sock:
                data = self.sock.recv(4096)
                if not data:
                    break
                buffer += data
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    try:
                        msg = json.loads(line.decode())
                        if msg.get("type") == "state":
                            st = msg.get("state")
                            with self.state_lock:
                                self.state = st
                    except Exception:
                        continue
        except Exception:
            pass
        finally:
            self.running = False
            try:
                if self.sock:
                    self.sock.close()
            except:
                pass

    def on_key_press(self, event):
        # Map keys based on assigned player
        key = event.keysym.lower()
        self.key_pressed.add(key)
        # toggle pause on 'p'
        if key == 'p':
            self.toggle_pause()
            return
        # If waiting for trajectory selection and this client is allowed to choose
        allowed = (self.mode == 'local') or (self.mode == 'network' and self.player == 1)
        # For local mode use the server-side game flag; for network use the client flag
        if self.mode == 'local':
            waiting = getattr(self.game, 'waiting_trajectory', False)
        else:
            waiting = getattr(self, 'waiting_trajectory', False)
        if waiting and allowed:
            # Rotate angle with left/right and confirm with Enter/Return
            if key in ('left', 'a'):
                self.traj_angle = (self.traj_angle - 5) % 360
                return
            if key in ('right', 'd'):
                self.traj_angle = (self.traj_angle + 5) % 360
                return
            if key in ('return', 'enter'):
                # confirm selection
                try:
                    angle = float(self.traj_angle)
                    self.choose_trajectory(angle)
                    # hide arrow
                    try:
                        if self.traj_canvas_id is not None:
                            self.renderer.canvas.delete(self.traj_canvas_id)
                            self.traj_canvas_id = None
                    except Exception:
                        pass
                except Exception:
                    pass
                return
        # Determine behavior for network vs local
        if self.mode == "network":
            cmd = "stop"
            # client players are assigned 1 or 2; we'll map 1->top(A/D) and 2->bottom(Left/Right)
            if self.player == 1:
                # player 1 (top) uses 'a'/'d'
                if 'a' in self.key_pressed or 'left' in self.key_pressed:
                    cmd = 'left'
                elif 'd' in self.key_pressed or 'right' in self.key_pressed:
                    cmd = 'right'
            elif self.player == 2:
                if 'left' in self.key_pressed or 'a' in self.key_pressed:
                    cmd = 'left'
                elif 'right' in self.key_pressed or 'd' in self.key_pressed:
                    cmd = 'right'
            else:
                if 'a' in self.key_pressed or 'left' in self.key_pressed:
                    cmd = 'left'
                elif 'd' in self.key_pressed or 'right' in self.key_pressed:
                    cmd = 'right'
            # if changed, send
            if cmd != self.current_cmd:
                self.current_cmd = cmd
                self.send_command(cmd)
        else:
            # local mode: control both players on same keyboard
            # Top player (index 0): 'a' / 'd'
            cmd0 = "stop"
            if 'a' in self.key_pressed:
                cmd0 = 'left'
            elif 'd' in self.key_pressed:
                cmd0 = 'right'
            # Bottom player (index 1): Left / Right arrows
            cmd1 = "stop"
            if 'left' in self.key_pressed:
                cmd1 = 'left'
            elif 'right' in self.key_pressed:
                cmd1 = 'right'
            self.local_commands[0] = cmd0
            self.local_commands[1] = cmd1

    def on_key_release(self, event):
        key = event.keysym.lower()
        if key in self.key_pressed:
            self.key_pressed.remove(key)
        # If we're in trajectory selection mode, ignore movement key releases
        allowed = (self.mode == 'local') or (self.mode == 'network' and self.player == 1)
        if getattr(self, 'waiting_trajectory', False) and allowed:
            return
        if self.mode == "network":
            # determine new cmd
            cmd = "stop"
            if 'a' in self.key_pressed or 'left' in self.key_pressed:
                cmd = 'left'
            elif 'd' in self.key_pressed or 'right' in self.key_pressed:
                cmd = 'right'
            if cmd != self.current_cmd:
                self.current_cmd = cmd
                self.send_command(cmd)
        else:
            # update local commands
            cmd0 = "stop"
            if 'a' in self.key_pressed:
                cmd0 = 'left'
            elif 'd' in self.key_pressed:
                cmd0 = 'right'
            cmd1 = "stop"
            if 'left' in self.key_pressed:
                cmd1 = 'left'
            elif 'right' in self.key_pressed:
                cmd1 = 'right'
            self.local_commands[0] = cmd0
            self.local_commands[1] = cmd1

    def send_command(self, cmd):
        # In network mode send to server, in local mode update local commands
        if self.mode == "network":
            if not self.connected or not self.sock:
                return
            try:
                data = {"type": "cmd", "cmd": cmd}
                send_json(self.sock, data)
            except Exception:
                pass
        else:
            # local mode doesn't send network messages; commands already stored in self.local_commands
            return

    def send_control(self, cmd):
        # send control messages to server, e.g. new_game
        # local mode: perform reset locally (cmd may be 'new_game')
        if self.mode == 'local':
            try:
                if cmd == 'new_game' and self.game:
                    self.game.reset_game()
                    # clear any previous local trajectory command so a new selection is required
                    try:
                        if isinstance(self.local_commands, dict) and 'trajectory' in self.local_commands:
                            del self.local_commands['trajectory']
                    except Exception:
                        pass
                    # reflect waiting state immediately on client side
                    self.waiting_trajectory = True
                    st = self.game.get_state()
                    with self.state_lock:
                        self.state = st
                    return
                if cmd == 'pause':
                    # toggle local pause
                    self.paused = not self.paused
                    # update button label
                    try:
                        self.pause_btn.config(text=("Reprendre (P)" if self.paused else "Pause (P)"))
                    except Exception:
                        pass
                    return
            except Exception:
                return
        # network mode: send control to server (optionally with value)
        if not self.connected or not self.sock:
            return
        try:
            data = {"type": "control", "cmd": cmd}
            send_json(self.sock, data)
        except Exception:
            pass

    def send_set_dimensions(self, value):
        """Send a control to set extra dimensions. In local mode this sets the env var
        and resets the game; in network mode it sends a control message to server.
        """
        # validate
        try:
            v = int(value)
        except Exception:
            return
        if v <= 0 or v % 2 != 0 or v not in (2,4,6,8):
            return
        if self.mode == 'local':
            # set env and reset local game
            os.environ['EXTRA_DIMENSIONS'] = str(v)
            try:
                if self.game:
                    self.game.reset_game()
                    st = self.game.get_state()
                    with self.state_lock:
                        self.state = st
            except Exception:
                return
        else:
            if not self.connected or not self.sock:
                return
            try:
                data = {"type": "control", "cmd": "set_dims", "value": v}
                send_json(self.sock, data)
            except Exception:
                pass

    def apply_dimensions(self):
        val = self.dims_entry.get().strip()
        if not val:
            return
        self.send_set_dimensions(val)

    def choose_trajectory(self, direction):
        """Player 1 chooses ball trajectory at game start: numeric degrees or labels.
        Direction may be float/int (degrees) or string like 'left'/'center'/'right'."""
        # normalize numeric types
        try:
            angle = None
            if isinstance(direction, (int, float)):
                angle = float(direction)
            else:
                # try parse string as float
                try:
                    angle = float(str(direction))
                except Exception:
                    angle = None
        except Exception:
            angle = None

        # ignore if we're not currently waiting for a selection
        # For local mode, consult the Game object's waiting_trajectory; otherwise use client flag
        if self.mode == 'local':
            waiting = getattr(self.game, 'waiting_trajectory', False)
        else:
            waiting = getattr(self, 'waiting_trajectory', False)
        if not waiting:
            return

        if self.mode == "local":
            # In local mode, add trajectory to local_commands so game.update() picks it up
            try:
                if angle is not None:
                    # clamp to allowed sector for player 1
                    if angle < self.traj_min:
                        angle = self.traj_min
                    if angle > self.traj_max:
                        angle = self.traj_max
                    self.local_commands['trajectory'] = angle
                    self.traj_angle = angle
                else:
                    # send label directly
                    self.local_commands['trajectory'] = direction
                logger.info("Local: player 1 chose trajectory: %s", direction)
                # Leave `self.game.waiting_trajectory` to the game loop so it can
                # read `self.local_commands['trajectory']` and apply the angle.
                # Only clear the client's waiting flag to hide the arrow.
                self.waiting_trajectory = False
            except Exception:
                pass
        else:
            # In network mode, send trajectory control to server
            if not self.connected or not self.sock:
                return
            try:
                val = angle if angle is not None else direction
                # if numeric, clamp before sending
                if isinstance(val, (int, float)):
                    if val < self.traj_min:
                        val = self.traj_min
                    if val > self.traj_max:
                        val = self.traj_max
                data = {"type": "control", "cmd": "trajectory", "value": val}
                send_json(self.sock, data)
                # avoid duplicate sends locally until server state arrives
                try:
                    self.waiting_trajectory = False
                except Exception:
                    pass
            except Exception:
                pass

    def toggle_pause(self):
        """Toggle pause: in local mode pause the local game loop; in network mode send pause control to server."""
        if self.mode == 'local':
            self.paused = not self.paused
            try:
                self.pause_btn.config(text=("Reprendre (P)" if self.paused else "Pause (P)"))
            except Exception:
                pass
        else:
            # optimistic toggle for UI while server processes request
            try:
                # flip local for immediate feedback
                self.paused = not self.paused
                self.pause_btn.config(text=("Reprendre (P)" if self.paused else "Pause (P)"))
            except Exception:
                pass
            # send pause toggle to server
            try:
                data = {"type": "control", "cmd": "pause"}
                send_json(self.sock, data)
            except Exception:
                pass

    def render_loop(self):
        if not self.running:
            return
        # render at ~60 fps using Tkinter after
        if self.mode == "network":
            with self.state_lock:
                st = dict(self.state)  # shallow copy
            self.renderer.draw_state(st)
            # update waiting flag from server state
            self.waiting_trajectory = bool(st.get('waiting_trajectory', False))
            # update paused state from server
            try:
                server_paused = bool(st.get('paused', False))
                if server_paused != self.paused:
                    self.paused = server_paused
                    try:
                        self.pause_btn.config(text=("Reprendre (P)" if self.paused else "Pause (P)"))
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            # local: step the game and draw
            # step the game and draw; game.update will handle waiting_trajectory
            try:
                if not getattr(self, 'paused', False):
                    self.game.update(self.FRAME_DT, self.local_commands)
            except Exception:
                pass
            try:
                st = self.game.get_state()
                self.waiting_trajectory = getattr(self.game, 'waiting_trajectory', False)
            except Exception:
                st = self.game.get_state()
            self.renderer.draw_state(st)
        # Draw/update trajectory arrow overlay if waiting and player 1
        allowed = (self.mode == 'local') or (self.mode == 'network' and self.player == 1)
        if getattr(self, 'waiting_trajectory', False) and allowed:
            try:
                ball = st.get('ball', {})
                bx = ball.get('x', self.renderer.width/2)
                by = ball.get('y', self.renderer.height/2)
                r = ball.get('radius', 8)
                length = max(30, r * 6)
                ang = math.radians(self.traj_angle)
                ex = bx + math.cos(ang) * length
                ey = by + math.sin(ang) * length
                # draw or update arrow
                if self.traj_canvas_id is None:
                    self.traj_canvas_id = self.renderer.canvas.create_line(bx, by, ex, ey, arrow=tk.LAST, fill="#FFFF66", width=3)
                else:
                    self.renderer.canvas.coords(self.traj_canvas_id, bx, by, ex, ey)
            except Exception:
                pass
        else:
            # remove arrow if present
            if self.traj_canvas_id is not None:
                try:
                    self.renderer.canvas.delete(self.traj_canvas_id)
                except Exception:
                    pass
                self.traj_canvas_id = None

        # overlay: show game over message for both local and network modes
        go = st.get('game_over') if st else None
        if go:
            winner = go.get('winner')
            king_color = go.get('king_color')
            text = f"Partie terminée! Vainqueur: {'Noir' if winner==0 else 'Blanc'} (le roi {king_color})"
            # When game is over, pause client updates so the game appears stopped
            try:
                self.paused = True
                try:
                    self.pause_btn.config(text="Partie terminée")
                except Exception:
                    pass
            except Exception:
                pass
            if self.overlay_label is None:
                self.overlay_label = tk.Label(self.renderer.canvas, text=text, bg="#000000", fg="#FFFFFF", font=("Arial", 18))
                self.overlay_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            else:
                self.overlay_label.config(text=text)
        else:
            if self.overlay_label is not None:
                try:
                    self.overlay_label.destroy()
                except Exception:
                    pass
                self.overlay_label = None
        self.master.after(int(self.FRAME_DT*1000), self.render_loop)

    def stop(self):
        self.running = False
        # when quitting, request a new game on the server (if connected)
        try:
            if self.mode == 'network' and self.connected and self.sock:
                try:
                    self.send_control('new_game')
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if self.sock:
                self.sock.close()
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pong client: choose local or network mode")
    parser.add_argument("--mode", choices=("local", "network"), default="network", help="Choose play mode")
    args = parser.parse_args()
    root = tk.Tk()
    app = ClientApp(root, mode=args.mode)
    try:
        root.protocol("WM_DELETE_WINDOW", lambda: (app.stop(), root.destroy()))
        root.mainloop()
    except KeyboardInterrupt:
        app.stop()

