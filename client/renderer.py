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
    def __init__(self, root, width=800, height=600, bg="#000000"):
        self.root = root
        self.width = width
        self.height = height
        self.bg = bg
        self.canvas = tk.Canvas(root, width=width, height=height, bg=bg, highlightthickness=0)
        self.canvas.pack()
        # store canvas ids
        self.ball_id = None
        self.paddle_ids = [None, None]
        self.score_text_ids = [None, None]
        self.board_bg_id = None
        self.grid_ids = []
        # pieces: mapping (col,row) -> (rect_id, text_id, hp_bg_id, hp_fg_id, hp_text_id)
        self.piece_items = {}

    def clear(self):
        self.canvas.delete("all")
        self.ball_id = None
        self.paddle_ids = [None, None]
        self.score_text_ids = [None, None]
        self.board_bg_id = None
        self.grid_ids = []
        self.piece_items = {}

    def draw_state(self, state):
        # state contains width/height/board/ball/paddles/pieces/scores
        w = state.get("width", self.width)
        h = state.get("height", self.height)
        board = state.get("board")
        ball_d = state.get("ball", {})
        paddles_d = state.get("paddles", [{}, {}])
        pieces = state.get("pieces", [])
        scores = state.get("scores", [0,0])

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
                self.board_bg_id = self.canvas.create_rectangle(bx, by, bx+bw, by+bh, fill="#222222", outline="#444444")
            else:
                self.canvas.coords(self.board_bg_id, bx, by, bx+bw, by+bh)
            # grid lines (create once if empty)
            if not self.grid_ids:
                for c in range(1, cols):
                    x = bx + c*cell
                    self.grid_ids.append(self.canvas.create_line(x, by, x, by+bh, fill="#555555"))
                for r in range(1, rows):
                    y = by + r*cell
                    self.grid_ids.append(self.canvas.create_line(bx, y, bx+bw, y, fill="#555555"))
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
            color = "#CCCCCC" if pc.get('color') == 'white' else "#333333"
            # draw rect
            if key not in self.piece_items:
                rect_id = self.canvas.create_rectangle(left, top, right, bottom, fill=color, outline=color)
                # unicode symbol centered
                symbol = PIECE_UNICODE.get((pc.get('type'), pc.get('color')), '?')
                text_color = "#000000" if pc.get('color') == 'white' else "#FFFFFF"
                text_id = self.canvas.create_text(left+cell/2, top+cell/2, text=symbol, fill=text_color, font=("Arial", max(8, int(cell*0.6))))
                # HP bar background and foreground
                hp = pc.get('hp', 1)
                max_hp = pc.get('max_hp', 1)
                bar_w = cell * 0.7
                bar_h = max(4, int(cell * 0.12))
                bar_left = left + (cell - bar_w)/2
                bar_top = bottom - bar_h - 4
                bar_right = bar_left + bar_w
                bar_bottom = bar_top + bar_h
                hp_bg_id = self.canvas.create_rectangle(bar_left, bar_top, bar_right, bar_bottom, fill="#222222", outline="#000000")
                # foreground width based on hp ratio
                ratio = max(0.0, min(1.0, hp / max_hp)) if max_hp > 0 else 0.0
                fg_right = bar_left + bar_w * ratio
                # color: green -> red based on ratio
                if ratio > 0.5:
                    fg_color = "#44DD44"
                elif ratio > 0.2:
                    fg_color = "#FFAA33"
                else:
                    fg_color = "#FF4444"
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
                    fg_color = "#44DD44"
                elif ratio > 0.2:
                    fg_color = "#FFAA33"
                else:
                    fg_color = "#FF4444"
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

        # Draw paddles
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
            if self.paddle_ids[i] is None:
                self.paddle_ids[i] = self.canvas.create_rectangle(left, top, right, bottom, fill=color, outline=color)
            else:
                self.canvas.coords(self.paddle_ids[i], left, top, right, bottom)
                self.canvas.itemconfig(self.paddle_ids[i], fill=color, outline=color)

        # Draw ball
        bx_ball = ball_d.get("x", w/2)
        by_ball = ball_d.get("y", h/2)
        r = ball_d.get("radius", 8)
        color = ball_d.get("color", "#FFFFFF")
        left = bx_ball - r
        top = by_ball - r
        right = bx_ball + r
        bottom = by_ball + r
        if self.ball_id is None:
            self.ball_id = self.canvas.create_oval(left, top, right, bottom, fill=color, outline=color)
        else:
            self.canvas.coords(self.ball_id, left, top, right, bottom)
            self.canvas.itemconfig(self.ball_id, fill=color, outline=color)

        # Ensure paddles and ball are on top of pieces/board: raise their canvas items
        try:
            if self.ball_id is not None:
                self.canvas.tag_raise(self.ball_id)
            for pid in self.paddle_ids:
                if pid is not None:
                    self.canvas.tag_raise(pid)
        except Exception:
            pass

        # Draw scores (top-left and bottom-left)
        top_score = scores[0]
        bottom_score = scores[1]
        if self.score_text_ids[0] is None:
            self.score_text_ids[0] = self.canvas.create_text(50, 30, text=str(top_score), fill="#FFFFFF", font=("Arial", 20))
        else:
            self.canvas.itemconfig(self.score_text_ids[0], text=str(top_score))
        if self.score_text_ids[1] is None:
            self.score_text_ids[1] = self.canvas.create_text(50, h-30, text=str(bottom_score), fill="#FFFFFF", font=("Arial", 20))
        else:
            self.canvas.itemconfig(self.score_text_ids[1], text=str(bottom_score))

