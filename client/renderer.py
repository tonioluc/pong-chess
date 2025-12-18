import tkinter as tk

PIECE_UNICODE = {
    ('K', 'white'): '\u2654',
    ('Q', 'white'): '\u2655',
    ('R', 'white'): '\u2656',
    ('B', 'white'): '\u2657',
    ('N', 'white'): '\u2658',
    ('P', 'white'): '\u2659',
    ('K', 'black'): '\u265A',
    ('Q', 'black'): '\u265B',
    ('R', 'black'): '\u265C',
    ('B', 'black'): '\u265D',
    ('N', 'black'): '\u265E',
    ('P', 'black'): '\u265F',
}


class GameRenderer:
    def __init__(self, root, width=800, height=600, bg="#1a1a2e"):
        self.root = root
        self.width = width
        self.height = height
        self.bg = bg
        self.canvas = tk.Canvas(root, width=width, height=height, bg=bg, highlightthickness=2, highlightbackground="#e94560")
        self.canvas.pack()
        # store canvas ids
        self.ball_id = None
        self.paddle_ids = [None, None]
        self.score_text_ids = [None, None]
        self.board_bg_id = None
        self.grid_ids = []
        # pieces: mapping (col,row) -> (rect_id, text_id, hp_bg_id, hp_fg_id, hp_text_id)
        self.piece_items = {}
        # power bar ids
        self.power_bg_id = None
        self.power_fg_id = None
        self.power_text_id = None
        self.power_glow_id = None

    def clear(self):
        self.canvas.delete("all")
        self.ball_id = None
        self.paddle_ids = [None, None]
        self.score_text_ids = [None, None]
        self.board_bg_id = None
        self.grid_ids = []
        self.piece_items = {}
        self.power_bg_id = None
        self.power_fg_id = None
        self.power_text_id = None
        self.power_glow_id = None

    def draw_state(self, state):
        # state contains width/height/board/ball/paddles/pieces/scores
        w = state.get("width", self.width)
        h = state.get("height", self.height)
        board = state.get("board")
        ball_d = state.get("ball", {})
        paddles_d = state.get("paddles", [{}, {}])
        pieces = state.get("pieces", [])
        scores = state.get("scores", [0,0])
        power = state.get("power", {})

        # power bar (top center)
        try:
            charge = max(0, int(power.get("charge", 0)))
            max_charge = max(1, int(power.get("max_charge", 10)))
            ready = bool(power.get("ready", False))
            active = bool(power.get("active", False))
            special_damage = int(power.get("special_damage", 1))
            remaining_damage = int(power.get("remaining_damage", 0))
            ratio = min(1.0, charge / max_charge) if max_charge > 0 else 0.0
            bar_w = w * 0.6
            bar_h = 14
            x0 = (w - bar_w) / 2
            y0 = 8
            x1 = x0 + bar_w
            y1 = y0 + bar_h
            # background
            if self.power_bg_id is None:
                self.power_bg_id = self.canvas.create_rectangle(x0, y0, x1, y1, fill="#0d1b2a", outline="#415a77", width=2)
            else:
                self.canvas.coords(self.power_bg_id, x0, y0, x1, y1)
                self.canvas.itemconfig(self.power_bg_id, fill="#0d1b2a", outline="#415a77")
            # foreground - en mode actif, afficher les dégâts restants
            if active and remaining_damage > 0:
                # Barre qui montre les dégâts restants
                active_ratio = remaining_damage / special_damage if special_damage > 0 else 0
                fg_w = bar_w * active_ratio
                fg_color = "#e63946"  # Rouge vif pour indiquer le mode actif
            else:
                fg_w = bar_w * ratio
                fg_color = "#fb8500" if ready else "#06d6a0"
            if self.power_fg_id is None:
                self.power_fg_id = self.canvas.create_rectangle(x0, y0, x0 + fg_w, y1, fill=fg_color, outline=fg_color)
            else:
                self.canvas.coords(self.power_fg_id, x0, y0, x0 + fg_w, y1)
                self.canvas.itemconfig(self.power_fg_id, fill=fg_color, outline=fg_color)
            # glow when ready or active
            if (ready or active) and self.power_glow_id is None:
                glow_col = "#e63946" if active else "#f4a261"
                self.power_glow_id = self.canvas.create_rectangle(x0 - 6, y0 - 4, x1 + 6, y1 + 4, outline=glow_col, width=2, dash=(4,2))
            elif ready or active:
                glow_col = "#e63946" if active else "#f4a261"
                self.canvas.coords(self.power_glow_id, x0 - 6, y0 - 4, x1 + 6, y1 + 4)
                self.canvas.itemconfig(self.power_glow_id, outline=glow_col)
            else:
                if self.power_glow_id is not None:
                    try:
                        self.canvas.delete(self.power_glow_id)
                    except Exception:
                        pass
                    self.power_glow_id = None
            # text label
            if active and remaining_damage > 0:
                label = f"⚡ PERÇANT! Dégâts restants: {remaining_damage}/{special_damage}"
                text_color = "#e63946"
            elif ready:
                label = f"⚡ PRÊT! Puissance: {charge}/{max_charge} (x{special_damage})"
                text_color = "#f4a261"
            else:
                label = f"Puissance: {charge}/{max_charge} (x{special_damage})"
                text_color = "#e0e1dd"
            if self.power_text_id is None:
                self.power_text_id = self.canvas.create_text(w/2, y0 + bar_h/2, text=label, fill=text_color, font=("Helvetica", 10, "bold"))
            else:
                self.canvas.coords(self.power_text_id, w/2, y0 + bar_h/2)
                self.canvas.itemconfig(self.power_text_id, text=label, fill=text_color)
        except Exception:
            pass

        # draw board
        if board:
            bx = board.get('x', 0)
            by = board.get('y', 0)
            bw = board.get('width', w)
            bh = board.get('height', h)
            cols = board.get('cols', 8)
            rows = board.get('rows', 8)
            cell = board.get('cell_size', bw/cols)
            # background
            if self.board_bg_id is None:
                self.board_bg_id = self.canvas.create_rectangle(bx, by, bx+bw, by+bh, fill="#16213e", outline="#0f3460", width=3)
            else:
                self.canvas.coords(self.board_bg_id, bx, by, bx+bw, by+bh)
            # grid lines (create once if empty)
            if not self.grid_ids:
                for c in range(1, cols):
                    x = bx + c*cell
                    self.grid_ids.append(self.canvas.create_line(x, by, x, by+bh, fill="#0f3460", dash=(4, 2)))
                for r in range(1, rows):
                    y = by + r*cell
                    self.grid_ids.append(self.canvas.create_line(bx, y, bx+bw, y, fill="#0f3460", dash=(4, 2)))
        else:
            bx = 0; by = 0; bw = w; bh = h; cell = bw/8

        # Draw pieces: each occupies a full cell (solid block + unicode symbol)
        existing = set(self.piece_items.keys())
        seen = set()
        for pc in pieces:
            col = pc.get('col')
            row = pc.get('row')
            x = pc.get('x')
            y = pc.get('y')
            size = pc.get('size', cell)
            left = bx + col*cell
            top = by + row*cell
            right = left + cell
            bottom = top + cell
            key = (col, row)
            seen.add(key)
            color = "#a8dadc" if pc.get('color') == 'white' else "#457b9d"
            # draw rect
            if key not in self.piece_items:
                rect_id = self.canvas.create_rectangle(left+2, top+2, right-2, bottom-2, fill=color, outline="#1d3557", width=2)
                # unicode symbol centered
                symbol = PIECE_UNICODE.get((pc.get('type'), pc.get('color')), '?')
                text_color = "#1d3557" if pc.get('color') == 'white' else "#f1faee"
                text_id = self.canvas.create_text(left+cell/2, top+cell/2, text=symbol, fill=text_color, font=("Helvetica", max(8, int(cell*0.55)), "bold"))
                # HP bar background and foreground
                hp = pc.get('hp', 1)
                max_hp = pc.get('max_hp', 1)
                bar_w = cell * 0.7
                bar_h = max(4, int(cell * 0.12))
                bar_left = left + (cell - bar_w)/2
                bar_top = bottom - bar_h - 4
                bar_right = bar_left + bar_w
                bar_bottom = bar_top + bar_h
                hp_bg_id = self.canvas.create_rectangle(bar_left, bar_top, bar_right, bar_bottom, fill="#2b2d42", outline="#8d99ae")
                # foreground width based on hp ratio
                ratio = max(0.0, min(1.0, hp / max_hp)) if max_hp > 0 else 0.0
                fg_right = bar_left + bar_w * ratio
                # color: cyan -> orange based on ratio
                if ratio > 0.5:
                    fg_color = "#06d6a0"
                elif ratio > 0.2:
                    fg_color = "#ffd166"
                else:
                    fg_color = "#ef476f"
                hp_fg_id = self.canvas.create_rectangle(bar_left, bar_top, fg_right, bar_bottom, fill=fg_color, outline=fg_color)
                # hp text (show current / max)
                try:
                    txt_color = "#000000" if ratio > 0.5 else "#FFFFFF"
                except Exception:
                    txt_color = "#FFFFFF"
                font_size = max(6, int(bar_h * 0.9))
                hp_text_id = self.canvas.create_text(bar_left + bar_w/2, bar_top + bar_h/2, text=f"{hp}/{max_hp}", fill=txt_color, font=("Arial", font_size))
                self.piece_items[key] = (rect_id, text_id, hp_bg_id, hp_fg_id, hp_text_id)
            else:
                rect_id, text_id, hp_bg_id, hp_fg_id, hp_text_id = self.piece_items[key]
                self.canvas.coords(rect_id, left, top, right, bottom)
                symbol = PIECE_UNICODE.get((pc.get('type'), pc.get('color')), '?')
                self.canvas.coords(text_id, left+cell/2, top+cell/2)
                self.canvas.itemconfig(rect_id, fill=color, outline=color)
                self.canvas.itemconfig(text_id, text=symbol)
                # update hp bar positions and size
                hp = pc.get('hp', 1)
                max_hp = pc.get('max_hp', 1)
                bar_w = cell * 0.7
                bar_h = max(4, int(cell * 0.12))
                bar_left = left + (cell - bar_w)/2
                bar_top = bottom - bar_h - 4
                bar_right = bar_left + bar_w
                bar_bottom = bar_top + bar_h
                self.canvas.coords(hp_bg_id, bar_left, bar_top, bar_right, bar_bottom)
                ratio = max(0.0, min(1.0, hp / max_hp)) if max_hp > 0 else 0.0
                fg_right = bar_left + bar_w * ratio
                if ratio > 0.5:
                    fg_color = "#06d6a0"
                elif ratio > 0.2:
                    fg_color = "#ffd166"
                else:
                    fg_color = "#ef476f"
                self.canvas.coords(hp_fg_id, bar_left, bar_top, fg_right, bar_bottom)
                self.canvas.itemconfig(hp_fg_id, fill=fg_color, outline=fg_color)
                # update hp text and position
                try:
                    txt_color = "#000000" if ratio > 0.5 else "#FFFFFF"
                    font_size = max(6, int(bar_h * 0.9))
                    self.canvas.coords(hp_text_id, bar_left + bar_w/2, bar_top + bar_h/2)
                    self.canvas.itemconfig(hp_text_id, text=f"{hp}/{max_hp}", fill=txt_color, font=("Arial", font_size))
                except Exception:
                    pass
        # remove any stale piece items
        for stale in (existing - seen):
            rect_id, text_id, hp_bg_id, hp_fg_id, hp_text_id = self.piece_items.pop(stale)
            try:
                self.canvas.delete(rect_id)
                self.canvas.delete(text_id)
                self.canvas.delete(hp_bg_id)
                self.canvas.delete(hp_fg_id)
                self.canvas.delete(hp_text_id)
            except Exception:
                pass

        # Draw paddles with rounded style
        for i in range(2):
            pd = paddles_d[i]
            px = pd.get("x", w/2)
            py = pd.get("y", 0 if i==0 else h)
            pw = pd.get("width", 120)
            ph = pd.get("height", 12)
            color = pd.get("color", "#FFFFFF")
            left = px - pw/2
            top = py - ph/2
            right = px + pw/2
            bottom = py + ph/2
            outline_color = "#f8f8f2" if i == 0 else "#282a36"
            if self.paddle_ids[i] is None:
                self.paddle_ids[i] = self.canvas.create_rectangle(left, top, right, bottom, fill=color, outline=outline_color, width=3)
            else:
                self.canvas.coords(self.paddle_ids[i], left, top, right, bottom)
                self.canvas.itemconfig(self.paddle_ids[i], fill=color, outline=outline_color)

        # Draw ball with glow effect
        bx_ball = ball_d.get("x", w/2)
        by_ball = ball_d.get("y", h/2)
        r = ball_d.get("radius", 8)
        # highlight ball when special shot is ready/active
        is_special_active = bool(ball_d.get("special_active", False))
        is_special_ready = bool(ball_d.get("special_ready", False))
        base_color = ball_d.get("color", "#FFFFFF")
        if is_special_active:
            color = "#ffb703"
            glow_color = "#fb8500"
        elif is_special_ready:
            color = "#ffd166"
            glow_color = "#f77f00"
        else:
            color = base_color
            glow_color = "#ff6b6b"
        left = bx_ball - r
        top = by_ball - r
        right = bx_ball + r
        bottom = by_ball + r
        if self.ball_id is None:
            self.ball_id = self.canvas.create_oval(left, top, right, bottom, fill=color, outline=glow_color, width=3)
        else:
            self.canvas.coords(self.ball_id, left, top, right, bottom)
            self.canvas.itemconfig(self.ball_id, fill=color, outline=glow_color)

        # Ensure paddles and ball are on top of pieces/board: raise their canvas items
        try:
            if self.ball_id is not None:
                self.canvas.tag_raise(self.ball_id)
            for pid in self.paddle_ids:
                if pid is not None:
                    self.canvas.tag_raise(pid)
        except Exception:
            pass

        # Draw scores (top-right and bottom-right with new style)
        top_score = scores[0]
        bottom_score = scores[1]
            # Scores are hidden by design; remove any existing score text items
        for i in range(2):
            if self.score_text_ids[i] is not None:
                try:
                    self.canvas.delete(self.score_text_ids[i])
                except Exception:
                    pass
                self.score_text_ids[i] = None

