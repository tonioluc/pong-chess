# server.py
import socket
import threading
import json
import time
import os
from game import Game

HOST = "0.0.0.0"
PORT = 9999  # change as needed

FRAME_RATE = 30.0
FRAME_DT = 1.0 / FRAME_RATE


def send_json(sock, data):
    try:
        msg = json.dumps(data) + "\n"
        sock.sendall(msg.encode())
    except Exception:
        pass


def recv_loop(conn, addr, player_number, commands_dict, controls_dict, stop_event):
    """
    Receives JSON messages delimited by newline from a client and updates commands_dict[player_number]
    Also listens for control messages (e.g., new_game) and sets controls_dict flags.
    """
    buffer = b""
    try:
        while not stop_event.is_set():
            data = conn.recv(4096)
            if not data:
                break
            buffer += data
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                try:
                    msg = json.loads(line.decode())
                    if not isinstance(msg, dict):
                        continue
                    mtype = msg.get("type")
                    if mtype == "cmd":
                        cmd = msg.get("cmd")
                        if cmd in ("left", "right", "stop"):
                            commands_dict[player_number] = cmd
                    elif mtype == "control":
                        # simple control protocol: {type: 'control', 'cmd': 'new_game'}
                        cmd = msg.get('cmd')
                        if cmd == 'new_game':
                            controls_dict['new_game'] = True
                            print(f"[+] Control from {addr}: new_game requested")
                        elif cmd == 'set_dims':
                            # expected message: {type: 'control', cmd: 'set_dims', value: <int>}
                            try:
                                val = int(msg.get('value'))
                                controls_dict['set_dims'] = val
                                print(f"[+] Control from {addr}: set_dims requested -> {val}")
                            except Exception:
                                print(f"[!] Invalid set_dims value from {addr}: {msg.get('value')}")
                        elif cmd == 'trajectory':
                            # trajectory choice from player 1 at game start
                            # expected message: {type: 'control', cmd: 'trajectory', value: <degrees>}
                            # Only accept trajectory from player 1 (top). Other players are ignored.
                            if player_number != 1:
                                print(f"[!] Trajectory control ignored from player {player_number} (only player 1 may set trajectory)")
                                continue
                            val = msg.get('value')
                            # Accept numeric values or legacy labels; do not clamp here
                            accepted = None
                            if isinstance(val, (int, float)):
                                try:
                                    accepted = float(val)
                                except Exception:
                                    accepted = None
                            else:
                                # try parse numeric string
                                try:
                                    accepted = float(str(val))
                                except Exception:
                                    # fallback to legacy labels
                                    if val in ('left', 'center', 'right'):
                                        accepted = val
                                    else:
                                        accepted = None
                            if accepted is not None:
                                controls_dict['trajectory'] = accepted
                                print(f"[+] Control from {addr}: trajectory requested -> {accepted}")
                            else:
                                print(f"[!] Invalid trajectory value from {addr}: {val}")
                        elif cmd == 'pause':
                            # Toggle or set pause state for the game loop. If a boolean 'value' is provided,
                            # use it; otherwise toggle the current paused state.
                            val = msg.get('value', None)
                            if isinstance(val, bool):
                                controls_dict['paused'] = val
                            else:
                                controls_dict['paused'] = not controls_dict.get('paused', False)
                            print(f"[+] Control from {addr}: pause toggled -> {controls_dict.get('paused')}")
                except Exception:
                    continue
    except Exception:
        pass
    finally:
        stop_event.set()
        try:
            conn.close()
        except:
            pass


def accept_two_clients(sock):
    conns = []
    addrs = []
    print("Server: waiting for 2 clients to connect...")
    while len(conns) < 2:
        try:
            conn, addr = sock.accept()
            print(f"[+] Client connected from {addr}")
        except Exception as e:
            print(f"[!] Error accepting connection: {e}")
            raise
        # Tune accepted connection sockets to reduce latency
        try:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        except Exception:
            pass
        conns.append(conn)
        addrs.append(addr)
        # send assignment (player number 1 or 2)
        assigned = {"type": "assign", "player": len(conns)}
        send_json(conn, assigned)
        print(f"[+] Assigned player {len(conns)} to {addr}")
    return conns, addrs


def main():
    game = Game()
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Reduce latency for small packets (disable Nagle) and increase buffers
    try:
        server_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
    except Exception:
        pass
    server_sock.bind((HOST, PORT))
    server_sock.listen(2)
    print(f"[*] Server listening on {HOST}:{PORT}")
    print(f"[*] Waiting for client connections... (clients should connect to this IP on port {PORT})")

    conns, addrs = accept_two_clients(server_sock)
    stop_event = threading.Event()

    # commands from clients: default stop, keys are player_number 1 or 2
    commands = {1: "stop", 2: "stop"}
    # controls dict for requests like new_game
    controls = {"new_game": False}
    recv_threads = []
    for i, conn in enumerate(conns):
        player_number = i + 1
        t = threading.Thread(target=recv_loop, args=(conn, addrs[i], player_number, commands, controls, stop_event), daemon=True)
        t.start()
        recv_threads.append(t)

    print("Both clients connected, starting game loop.")
    last = time.time()
    try:
        while not stop_event.is_set():
            now = time.time()
            dt = now - last
            if dt < FRAME_DT:
                time.sleep(FRAME_DT - dt)
                continue
            last = now
            # convert commands (1/2) to game player indices (0/1)
            player_commands = {0: commands.get(1, "stop"), 1: commands.get(2, "stop")}
            # Check if trajectory control is pending and add it to player_commands
            if controls.get('trajectory') is not None:
                player_commands['trajectory'] = controls['trajectory']
                controls['trajectory'] = None
            # If paused, skip updating game logic; otherwise advance game
            if controls.get('paused'):
                result = None
            else:
                result = game.update(FRAME_DT, player_commands)
            # handle control requests (new game, set_dims)
            # If set_dims requested, apply it (set env var) and reset game
            if controls.get('set_dims') is not None:
                try:
                    val = int(controls.get('set_dims'))
                    # set environment variable for game creation
                    os.environ['EXTRA_DIMENSIONS'] = str(val)
                    print(f"[*] Applying EXTRA_DIMENSIONS={val} and resetting game")
                    game.reset_game()
                except Exception as e:
                    print(f"[!] Error applying set_dims: {e}")
                finally:
                    controls['set_dims'] = None
            if controls.get('new_game'):
                print('[*] New game requested, resetting game state')
                try:
                    game.reset_game()
                    # clear control flag
                    controls['new_game'] = False
                except Exception as e:
                    print(f"[!] Error resetting game: {e}")
            state = game.get_state()
            # include paused flag in broadcast so clients can update UI
            state['paused'] = bool(controls.get('paused', False))
            # Broadcast state to all connected clients. If a client send fails,
            # remove that connection but keep the server running for the others.
            msg = {"type": "state", "state": state}
            js = (json.dumps(msg) + "\n").encode()
            dead = []
            for i, conn in enumerate(list(conns)):
                try:
                    conn.sendall(js)
                except Exception:
                    print(f"Warning: client {i+1} disconnected during send, removing connection")
                    try:
                        conn.close()
                    except:
                        pass
                    dead.append(conn)
            # remove dead conns
            for d in dead:
                try:
                    conns.remove(d)
                except ValueError:
                    pass
            # If game ended, stop loop after broadcasting final state
            try:
                if state.get('game_over') is not None:
                    print('[*] Game over detected on server, stopping game loop.')
                    stop_event.set()
                    break
            except Exception:
                pass
            # if no clients left, stop the server loop
            if not conns:
                print("No clients left, stopping server loop.")
                stop_event.set()
                break
    except KeyboardInterrupt:
        print("Server shutting down (KeyboardInterrupt).")
    finally:
        stop_event.set()
        for conn in conns:
            try:
                conn.close()
            except:
                pass
        server_sock.close()
        print("Server closed.")

if __name__ == "__main__":
    main()

