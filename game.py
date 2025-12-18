# game.py
import time
import math
import logging
import os
import json
import requests
from entities.ball import Ball
from entities.paddle import Paddle


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# REST API configuration
API_BASE_URL = os.environ.get('VIE_API_URL', 'http://localhost:8080/vie-webservice/api/vies')

# Chessboard-style board: 8x8 cells. Pieces occupy full cells (no gaps).
# Paddles sit just outside the pawn rows (between pawns and center area).
COLS = 8
ROWS = 8
HIT_COOLDOWN = 0.12  # seconds during which a piece won't take another hit
# Power-up configuration defaults (overridable via power_config.json)
POWER_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'power_config.json')
DEFAULT_POWER_CONFIG = {
    "charge_max": 10,          # hits required to charge the special shot
    "charge_per_hit": 1,       # charge gained per HP removed
    "special_damage": 3        # HP removed by the empowered hit
}


class Game:
    WIDTH = 800
    HEIGHT = 600

    def __init__(self):
        # determine board dimensions: support optional reduced "dimensions"
        # via environment variable EXTRA_DIMENSIONS (2,4,6,8). When set we
        # reduce the number of columns to that value and use 4 rows so that
        # layout becomes compact: majors row, pawns row, pawns row, majors row.
        raw_dims = os.environ.get('EXTRA_DIMENSIONS')
        try:
            if raw_dims is not None:
                dims = int(raw_dims)
                if dims in (2, 4, 6, 8):
                    # active columns used to place pieces (centered within 8 columns)
                    self.active_cols = dims
                else:
                    self.active_cols = COLS
            else:
                self.active_cols = COLS
        except Exception:
            self.active_cols = COLS
        # Board grid remains full 8x8 for spacing consistency
        self.cols = COLS
        self.rows = ROWS

        # compute board geometry to fit inside WIDTH x HEIGHT with margins
        margin = 20
        board_w = self.WIDTH - margin * 2
        board_h = self.HEIGHT - margin * 2
        # base cell for the default 8x8 board -- keep this spacing for all dims
        base_cell = min(board_w / COLS, board_h / ROWS)
        # Use the base cell size (same spacing as 8x8) for every dimension so
        # reduced columns keep the same grid spacing as dimension 8
        cell_size = max(8, int(base_cell))
        # board width follows number of active columns so reduced-dimensions
        # produce a narrower board while keeping the same cell spacing
        board_pixel_w = cell_size * self.active_cols
        board_pixel_h = cell_size * ROWS
        board_x0 = (self.WIDTH - board_pixel_w) / 2
        board_y0 = (self.HEIGHT - board_pixel_h) / 2
        self.board = {
            "cols": self.active_cols,
            "rows": ROWS,
            "cell_size": cell_size,
            "x": board_x0,
            "y": board_y0,
            "width": board_pixel_w,
            "height": board_pixel_h,
        }

        # paddles: index 0 = top player, index 1 = bottom player
        # place paddles just outside the pawn rows
        # Adjust paddle size: for very reduced boards (2 cols) make paddles
        # much smaller so the ball can pass easily. Also reduce the ball radius.
        if self.active_cols == 2:
            pad_w = max(int(cell_size * 0.9), int(cell_size))
            pad_h = max(3, int(cell_size * 0.08))
            ball_radius = max(3, int(cell_size * 0.10))
        else:
            pad_w = cell_size * 1.75
            pad_h = cell_size * 0.25
            ball_radius = max(6, int(cell_size * 0.2))
        # top paddle: below row 1 (rows 0 and 1 belong to top player's pieces)
        top_paddle_y = board_y0 + cell_size * 2 + pad_h/2 + 4
        # bottom paddle: above the bottom pawn row (rows -2)
        bottom_paddle_y = board_y0 + cell_size * (self.rows - 2) - pad_h/2 - 4
        center_x = self.WIDTH / 2
        self.paddles = [
            Paddle(x=center_x, y=top_paddle_y, width=pad_w, height=pad_h, color="#bd93f9"),
            Paddle(x=center_x, y=bottom_paddle_y, width=pad_w, height=pad_h, color="#f1fa8c")
        ]
        # ball placed at board center
        self.ball = Ball(x=self.WIDTH/2, y=self.HEIGHT/2, radius=ball_radius, color="#ff79c6", speed=350)
        # power-up: charging bar that empowers the next hit
        self.power_config_path = POWER_CONFIG_PATH
        self.power_config = self._load_power_config()
        self._reset_power_state(reload_config=False)
        self.scores = [0, 0]  # index 0 = top player, index 1 = bottom player
        self.last_update = time.time()
        # pieces: will be loaded from JSON DB (no hard-coded data in code)
        self.pieces = []
        # db template path (original data that must NOT be overwritten)
        self.template_path = os.path.join(os.path.dirname(__file__), 'db_template.json')
        # current game state path (per-game file). We'll create a new game file at startup
        self.state_dir = os.path.dirname(__file__)
        self.db_path = None
        # HP map will be set when loading from template/state
        self.hp_map = {}
        # create a new per-game file from template and load it
        try:
            self._create_new_game_from_template()
        except Exception:
            # fallback to old behavior if template missing
            self.db_path = os.path.join(os.path.dirname(__file__), 'db.json')
            if os.path.exists(self.db_path):
                try:
                    self._load_db()
                except Exception:
                    self._init_pieces()
            else:
                self._init_pieces()
                try:
                    self._write_db()
                except Exception:
                    pass
        # game over flag
        self.game_over = None
        # waiting_trajectory: True if player 1 (top) must choose ball trajectory
        # before the game starts moving the ball
        self.waiting_trajectory = True
        self.pending_trajectory = None  # will be set by player 1 (values: 'left', 'center', 'right')

    def reset_ball(self, toward_bottom=True):
        # direction_down True means ball moves downward (toward bottom player)
        self.ball.reset(self.WIDTH/2, self.HEIGHT/2, direction_down=toward_bottom)
    
    def refresh_hp_from_api(self):
        """Reload HP values from REST API and update existing pieces"""
        try:
            response = requests.get(API_BASE_URL, timeout=5)
            response.raise_for_status()
            vies_data = response.json()
            logger.debug("Refreshing HP from API: %s", vies_data)
            
            # Build new hp_map from API response
            new_hp_map = {}
            for vie in vies_data:
                libelle = vie.get('libelle', '')
                if '(' in libelle and ')' in libelle:
                    piece_type = libelle.split('(')[1].split(')')[0]
                    new_hp_map[piece_type] = vie.get('nombreVieInitiale', 1)
            
            logger.info("HP map refreshed from API: %s", new_hp_map)
            
            # Update hp_map
            self.hp_map = new_hp_map
            
            # Update max_hp and current hp for all existing pieces
            for piece in self.pieces:
                piece_type = piece.get('type')
                if piece_type in new_hp_map:
                    new_max_hp = new_hp_map[piece_type]
                    piece['max_hp'] = new_max_hp
                    # Always reset current hp to new max value
                    piece['hp'] = new_max_hp
            
            # Save updated state
            try:
                self._write_db()
            except Exception as e:
                logger.error("Failed to save after HP refresh: %s", e)
            
            logger.info("All pieces updated with new HP values")
            return True
            
        except Exception as e:
            logger.error("Failed to refresh HP from API: %s", e)
            return False

    def _init_pieces(self):
        # full major piece order for 8 columns
        majors_full = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        # Fetch HP values from REST API
        try:
            response = requests.get(API_BASE_URL, timeout=5)
            response.raise_for_status()
            vies_data = response.json()
            logger.debug("Raw API response: %s", vies_data)
            # Build hp_map from API response: extract piece type from libelle
            # Expected format: "Tour (R)", "Cavalier (N)", etc.
            self.hp_map = {}
            for vie in vies_data:
                libelle = vie.get('libelle', '')
                # Extract piece type from parentheses
                if '(' in libelle and ')' in libelle:
                    piece_type = libelle.split('(')[1].split(')')[0]
                    self.hp_map[piece_type] = vie.get('nombreVieInitiale', 1)
                    logger.debug("Parsed piece: %s -> %d HP", piece_type, vie.get('nombreVieInitiale', 1))
                else:
                    logger.warning("Skipping invalid libelle format: '%s' (expected format: 'Name (X)')", libelle)
            logger.info("HP map loaded from REST API: %s", self.hp_map)
        except Exception as e:
            logger.error("Failed to load HP values from REST API: %s. Using defaults.", e)
            # Fallback to default values
            self.hp_map = {'P': 2, 'N': 4, 'R': 5, 'B': 5, 'Q': 8, 'K': 10}
        # choose central slice of majors_full according to active columns
        start = (len(majors_full) - self.active_cols) // 2
        majors = majors_full[start:start + self.active_cols]
        # create default pieces layout with hp values; use relative columns
        # (0..active_cols-1) so the pieces map into the active area drawn by
        # the renderer which uses board['cols'] == active_cols.
        for c in range(self.active_cols):
            m = majors[c]
            col_rel = c
            # top majors (row 0)
            self.pieces.append({"type": m, "color": "black", "col": col_rel, "row": 0, "hp": self.hp_map.get(m, 1), "max_hp": self.hp_map.get(m, 1), "last_hit": 0.0})
            # top pawns (row 1)
            self.pieces.append({"type": 'P', "color": "black", "col": col_rel, "row": 1, "hp": self.hp_map.get('P', 1), "max_hp": self.hp_map.get('P', 1), "last_hit": 0.0})
            logger.debug("Init pawn black at relative col=%d row=%d", col_rel, 1)
            # bottom pawns (row ROWS-2)
            self.pieces.append({"type": 'P', "color": "white", "col": col_rel, "row": ROWS - 2, "hp": self.hp_map.get('P', 1), "max_hp": self.hp_map.get('P', 1), "last_hit": 0.0})
            logger.debug("Init pawn white at relative col=%d row=%d", col_rel, ROWS - 2)
            # bottom majors (row ROWS-1)
            self.pieces.append({"type": m, "color": "white", "col": col_rel, "row": ROWS - 1, "hp": self.hp_map.get(m, 1), "max_hp": self.hp_map.get(m, 1), "last_hit": 0.0})

    def _apply_trajectory(self):
        """Apply player 1's chosen trajectory to the ball's initial velocity."""
        # Base speed downward (toward player 2)
        base_speed = 350
        trajectory = self.pending_trajectory
        # trajectory may be 'left'/'right'/'center' or a numeric angle in degrees
        try:
            if isinstance(trajectory, (int, float)):
                angle = math.radians(float(trajectory))
            else:
                # try parse numeric string
                try:
                    angle = math.radians(float(trajectory))
                except Exception:
                    if trajectory == 'left':
                        angle = math.radians(225)
                    elif trajectory == 'right':
                        angle = math.radians(315)
                    else:
                        angle = math.radians(270)
        except Exception:
            angle = math.radians(270)
        
        self.ball.dx = math.cos(angle) * base_speed
        self.ball.dy = math.sin(angle) * base_speed
        logger.info("Ball trajectory chosen by player 1: %s, velocity=(%.1f, %.1f)", trajectory, self.ball.dx, self.ball.dy)

    def _write_db(self):
        # Write game state to local JSON file (for game persistence)
        # HP values are managed via REST API, not stored here
        try:
            data = {
                'hp_map': self.hp_map,
                'scores': self.scores,
                'pieces': self.pieces
            }
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.exception('Failed to write DB: %s', e)

    def _load_db(self):
        # Load game state from local JSON file
        with open(self.db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Fetch current HP values from REST API
        try:
            response = requests.get(API_BASE_URL, timeout=5)
            response.raise_for_status()
            vies_data = response.json()
            logger.debug("Raw API response: %s", vies_data)
            # Build hp_map from API response
            self.hp_map = {}
            for vie in vies_data:
                libelle = vie.get('libelle', '')
                if '(' in libelle and ')' in libelle:
                    piece_type = libelle.split('(')[1].split(')')[0]
                    self.hp_map[piece_type] = vie.get('nombreVieInitiale', 1)
                    logger.debug("Parsed piece: %s -> %d HP", piece_type, vie.get('nombreVieInitiale', 1))
                else:
                    logger.warning("Skipping invalid libelle format: '%s' (expected format: 'Name (X)')", libelle)
            logger.info("HP map refreshed from REST API: %s", self.hp_map)
        except Exception as e:
            logger.warning("Failed to refresh HP values from REST API: %s. Using saved values.", e)
            # Fallback to saved hp_map
            self.hp_map = data.get('hp_map', self.hp_map or {})
        
        # scores
        self.scores = data.get('scores', self.scores)
        # pieces: ensure hp and max_hp keys set according to hp_map if missing
        loaded = []
        for pc in data.get('pieces', []):
            p = dict(pc)
            t = p.get('type')
            default_hp = self.hp_map.get(t, 1)
            if 'max_hp' not in p:
                p['max_hp'] = default_hp
            if 'hp' not in p:
                p['hp'] = p.get('max_hp', default_hp)
            # ensure last_hit exists for cooldown handling
            if 'last_hit' not in p:
                p['last_hit'] = 0.0
            loaded.append(p)
        self.pieces = loaded

    def _load_power_config(self):
        """Load power-up configuration from JSON with sane fallbacks."""
        cfg = dict(DEFAULT_POWER_CONFIG)
        path = getattr(self, 'power_config_path', POWER_CONFIG_PATH)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                for key in DEFAULT_POWER_CONFIG:
                    if key in data:
                        cfg[key] = data[key]
            else:
                logger.warning("Power config at %s is not a JSON object; using defaults", path)
        except FileNotFoundError:
            logger.info("Power config not found at %s; using defaults", path)
        except Exception as e:
            logger.warning("Failed to load power config %s: %s; using defaults", path, e)
        return cfg

    def update_power_config(self, new_config):
        """Mettre à jour la configuration de puissance depuis un dictionnaire externe."""
        if not isinstance(new_config, dict):
            return False
        try:
            # Sauvegarder dans le fichier
            path = getattr(self, 'power_config_path', POWER_CONFIG_PATH)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            # Recharger et appliquer (sans reset de charge)
            self.power_config = new_config
            cfg = new_config
            self.power_max_charge = max(1, int(cfg.get('charge_max', DEFAULT_POWER_CONFIG['charge_max'])))
            self.power_gain_per_hit = max(1, int(cfg.get('charge_per_hit', DEFAULT_POWER_CONFIG['charge_per_hit'])))
            self.power_special_damage = max(1, int(cfg.get('special_damage', DEFAULT_POWER_CONFIG['special_damage'])))
            # Si charge dépasse nouveau max, limiter
            self.power_charge = min(self.power_charge, self.power_max_charge)
            if self.power_charge >= self.power_max_charge:
                self.power_ready = True
            logger.info("Power config updated: max=%d, per_hit=%d, damage=%d", 
                       self.power_max_charge, self.power_gain_per_hit, self.power_special_damage)
            return True
        except Exception as e:
            logger.error("Failed to update power config: %s", e)
            return False

    def _reset_power_state(self, reload_config=True):
        """Reset power bar values and optionally reload configuration."""
        if reload_config:
            self.power_config = self._load_power_config()
        cfg = self.power_config if isinstance(self.power_config, dict) else DEFAULT_POWER_CONFIG
        try:
            charge_max = int(cfg.get('charge_max', DEFAULT_POWER_CONFIG['charge_max']))
        except Exception:
            charge_max = DEFAULT_POWER_CONFIG['charge_max']
        try:
            charge_per_hit = int(cfg.get('charge_per_hit', DEFAULT_POWER_CONFIG['charge_per_hit']))
        except Exception:
            charge_per_hit = DEFAULT_POWER_CONFIG['charge_per_hit']
        try:
            special_damage = int(cfg.get('special_damage', DEFAULT_POWER_CONFIG['special_damage']))
        except Exception:
            special_damage = DEFAULT_POWER_CONFIG['special_damage']

        self.power_max_charge = max(1, charge_max)
        self.power_gain_per_hit = max(1, charge_per_hit)
        self.power_special_damage = max(1, special_damage)
        self.power_charge = 0
        self.power_ready = False
        self.power_active = False
        # Mode spécial perçant (traverse les pièces détruites)
        self.special_piercing = False
        self.special_remaining_damage = 0
        try:
            self.ball.special_ready = False
            self.ball.special_active = False
        except Exception:
            pass

    def _create_new_game_from_template(self):
        # Ensure template exists
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        
        # Load HP values from REST API FIRST (before creating pieces)
        try:
            response = requests.get(API_BASE_URL, timeout=5)
            response.raise_for_status()
            vies_data = response.json()
            logger.debug("Raw API response in _create_new_game_from_template: %s", vies_data)
            # Build hp_map from API response
            hp_map = {}
            for vie in vies_data:
                libelle = vie.get('libelle', '')
                if '(' in libelle and ')' in libelle:
                    piece_type = libelle.split('(')[1].split(')')[0]
                    hp_map[piece_type] = vie.get('nombreVieInitiale', 1)
                    logger.debug("Parsed piece in template: %s -> %d HP", piece_type, vie.get('nombreVieInitiale', 1))
            logger.info("HP map loaded from REST API for new game: %s", hp_map)
        except Exception as e:
            logger.error("Failed to load HP values from REST API in _create_new_game_from_template: %s. Using defaults.", e)
            # Fallback to default values
            hp_map = {'P': 2, 'N': 4, 'R': 5, 'B': 5, 'Q': 8, 'K': 10}
        
        # Store hp_map in instance
        self.hp_map = hp_map
        
        # create a new per-game filename
        ts = int(time.time())
        new_name = f'game_{ts}.json'
        new_path = os.path.join(self.state_dir, new_name)
        # copy template content into new file (load+write to set hp/max_hp explicitly)
        with open(self.template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # decide whether to use template pieces (default 8x8) or generate
        # a reduced layout based on self.active_cols. Use API hp_map (not template)
        if self.active_cols == COLS:
            pieces = []
            for pc in data.get('pieces', []):
                p = dict(pc)
                t = p.get('type')
                default_hp = self.hp_map.get(t, 1)  # Use API hp_map, not template
                if 'max_hp' not in p:
                    p['max_hp'] = default_hp
                if 'hp' not in p:
                    p['hp'] = p.get('max_hp', default_hp)
                # Ensure hp is set to API value
                p['hp'] = default_hp
                p['max_hp'] = default_hp
                pieces.append(p)
        else:
            # for reduced boards, generate pieces according to self.cols/self.rows
            self.pieces = []
            self._init_pieces()
            pieces = list(self.pieces)

        state = {
            'hp_map': self.hp_map,  # Use API hp_map
            'scores': data.get('scores', [0,0]),
            'pieces': pieces
        }
        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        # set current db_path and load pieces into instance
        self.db_path = new_path
        self.pieces = pieces
        self.scores = data.get('scores', [0,0])


    def update(self, dt, player_commands):
        # player_commands: dict {0: 'left'/'right'/'stop', 1: ...}
        # At game start, player 1 must choose ball trajectory first
        if self.waiting_trajectory:
            # Check if player 1 has chosen a trajectory via player_commands
            trajectory = player_commands.get('trajectory', None)
            if trajectory is not None:
                # accept numeric angles or legacy labels
                if isinstance(trajectory, (int, float)):
                    self.pending_trajectory = float(trajectory)
                else:
                    # try parse numeric string
                    try:
                        self.pending_trajectory = float(str(trajectory))
                    except Exception:
                        # fallback to labels
                        if trajectory in ('left', 'center', 'right'):
                            self.pending_trajectory = trajectory
                        else:
                            self.pending_trajectory = None
                if self.pending_trajectory is not None:
                    # numeric angles are accepted as provided (no automatic clamping)
                    try:
                        if isinstance(self.pending_trajectory, (int, float)):
                            # ensure stored as float
                            self.pending_trajectory = float(self.pending_trajectory)
                    except Exception:
                        pass
                    self.waiting_trajectory = False
                    # Apply trajectory: set ball initial velocity
                    self._apply_trajectory()
            else:
                # Still waiting for player 1 to choose; do minimal updates
                # (allow paddle movements but not ball/pieces)
                for pid, cmd in player_commands.items():
                    if pid in (0,1):
                        self.paddles[pid].apply_command(cmd)
                left_bound = self.board['x']
                right_bound = self.board['x'] + self.board['width']
                for p in self.paddles:
                    p.update(dt, left_bound, right_bound)
                return {"scored": None, "collided": False}
        
        # Apply commands to paddles
        self.power_active = False
        for pid, cmd in player_commands.items():
            if pid in (0,1):
                self.paddles[pid].apply_command(cmd)

        # Update paddles (clamp to board horizontal bounds)
        left_bound = self.board['x']
        right_bound = self.board['x'] + self.board['width']
        for p in self.paddles:
            p.update(dt, left_bound, right_bound)

        # Update ball
        self.ball.update(dt)

        # Board bounds (reflect on all four edges)
        left = self.board['x']
        right = self.board['x'] + self.board['width']
        top = self.board['y']
        bottom = self.board['y'] + self.board['height']
        collided = False
        wall_hit = False
        # left/right
        if self.ball.x - self.ball.radius < left:
            self.ball.x = left + self.ball.radius
            self.ball.dx *= -1
            collided = True
            wall_hit = True
        if self.ball.x + self.ball.radius > right:
            self.ball.x = right - self.ball.radius
            self.ball.dx *= -1
            collided = True
            wall_hit = True
        # top/bottom
        if self.ball.y - self.ball.radius < top:
            self.ball.y = top + self.ball.radius
            self.ball.dy *= -1
            collided = True
            wall_hit = True
        if self.ball.y + self.ball.radius > bottom:
            self.ball.y = bottom - self.ball.radius
            self.ball.dy *= -1
            collided = True
            wall_hit = True
        
        # Si la balle touche un mur pendant le mode spécial actif, annuler le pouvoir
        if wall_hit and getattr(self, 'special_piercing', False):
            logger.info("Mur touché! Pouvoir spécial annulé (dégâts restants: %d)", getattr(self, 'special_remaining_damage', 0))
            self.special_piercing = False
            self.special_remaining_damage = 0
            self.power_active = False

        # Piece collisions: detect all pieces intersecting the ball this frame
        # and apply damage to each (instead of choosing one at random). Then
        # compute a combined response for the ball reflection based on overlaps.
        now_ts = time.time()
        colliding = []
        for pc in list(self.pieces):
            col = pc['col']
            row = pc['row']
            cx = self.board['x'] + col * self.board['cell_size']
            cy = self.board['y'] + row * self.board['cell_size']
            rleft = cx
            rtop = cy
            rright = cx + self.board['cell_size']
            rbottom = cy + self.board['cell_size']
            # circle-rect collision test
            nearest_x = max(rleft, min(self.ball.x, rright))
            nearest_y = max(rtop, min(self.ball.y, rbottom))
            dx = self.ball.x - nearest_x
            dy = self.ball.y - nearest_y
            if dx*dx + dy*dy <= (self.ball.radius + 0.0)**2:
                # compute overlaps as before
                overlap_x = min(self.ball.x - rleft, rright - self.ball.x)
                overlap_y = min(self.ball.y - rtop, rbottom - self.ball.y)
                colliding.append((pc, rleft, rtop, rright, rbottom, overlap_x, overlap_y))

        if colliding:
            # Vérifier si on est en mode spécial perçant ou si on commence un nouveau spécial
            use_special = bool(self.power_ready) or getattr(self, 'special_piercing', False)
            
            # Si c'est le début d'un nouveau spécial, initialiser le compteur de dégâts restants
            if self.power_ready and not getattr(self, 'special_piercing', False):
                self.special_piercing = True
                self.special_remaining_damage = self.power_special_damage
                self.power_ready = False
                self.power_charge = 0
                logger.info("DÉBUT POUVOIR SPÉCIAL! Capacité: %d dégâts", self.special_remaining_damage)
            
            # apply damage to all collided pieces (respect cooldown per piece)
            charge_gain = 0
            total_damage_dealt = 0
            pieces_destroyed = []
            
            for (pc, rleft, rtop, rright, rbottom, overlap_x, overlap_y) in colliding:
                last_hit = pc.get('last_hit', 0.0)
                if now_ts - last_hit >= HIT_COOLDOWN:
                    current_hp = pc.get('hp', self.hp_map.get(pc.get('type'), 1))
                    
                    if use_special and getattr(self, 'special_remaining_damage', 0) > 0:
                        # Mode spécial: appliquer les dégâts disponibles
                        damage_to_apply = min(self.special_remaining_damage, current_hp)
                        pc['hp'] = max(0, current_hp - damage_to_apply)
                        self.special_remaining_damage -= damage_to_apply
                        total_damage_dealt += damage_to_apply
                        logger.debug("Spécial: pièce touchée, dégâts=%d, HP restant=%d, capacité restante=%d", 
                                   damage_to_apply, pc['hp'], self.special_remaining_damage)
                    else:
                        # Mode normal: 1 dégât
                        applied = min(1, current_hp)
                        pc['hp'] = max(0, current_hp - 1)
                        charge_gain += applied * self.power_gain_per_hit
                    
                    pc['last_hit'] = now_ts
                    
                    # Marquer les pièces détruites
                    if pc['hp'] <= 0:
                        pieces_destroyed.append(pc)
            
            # Déterminer si la balle doit rebondir ou traverser
            should_bounce = True
            
            if use_special and getattr(self, 'special_piercing', False):
                # En mode spécial: ne pas rebondir si toutes les pièces touchées sont détruites
                # et qu'il reste de la capacité de dégâts
                all_destroyed = all(pc['hp'] <= 0 for (pc, _, _, _, _, _, _) in colliding)
                if all_destroyed and self.special_remaining_damage > 0:
                    should_bounce = False
                    logger.debug("Traversée! Toutes les pièces détruites, capacité restante: %d", self.special_remaining_damage)
                else:
                    # Soit une pièce survit, soit plus de capacité: rebondir et terminer le spécial
                    should_bounce = True
                    if self.special_remaining_damage <= 0:
                        logger.info("FIN POUVOIR SPÉCIAL! Capacité épuisée après %d dégâts", total_damage_dealt)
                    self.special_piercing = False
                    self.special_remaining_damage = 0
            
            # Appliquer le rebond si nécessaire
            if should_bounce:
                # Decide axis of response by averaging overlaps
                sum_ox = sum(c[5] for c in colliding)
                sum_oy = sum(c[6] for c in colliding)
                axis = 'x' if sum_ox < sum_oy else 'y'
                # compute average centers to determine which side to push ball out to
                avg_cx = sum((c[1] + c[3]) / 2.0 for c in colliding) / len(colliding)
                avg_cy = sum((c[2] + c[4]) / 2.0 for c in colliding) / len(colliding)
                # respond: push ball outside combined rect area
                if axis == 'x':
                    if self.ball.x < avg_cx:
                        leftmost = min(c[1] for c in colliding)
                        self.ball.x = leftmost - self.ball.radius
                    else:
                        rightmost = max(c[3] for c in colliding)
                        self.ball.x = rightmost + self.ball.radius
                    self.ball.dx *= -1
                else:
                    if self.ball.y < avg_cy:
                        topmost = min(c[2] for c in colliding)
                        self.ball.y = topmost - self.ball.radius
                    else:
                        bottommost = max(c[4] for c in colliding)
                        self.ball.y = bottommost + self.ball.radius
                    self.ball.dy *= -1
                collided = True
            
            # Mettre à jour la charge si en mode normal
            if charge_gain > 0 and not use_special:
                self.power_charge = min(self.power_charge + charge_gain, self.power_max_charge)
                logger.debug("Power charge: %d/%d", self.power_charge, self.power_max_charge)
                if self.power_charge >= self.power_max_charge:
                    self.power_ready = True
                    logger.info("PUISSANCE PRÊTE! Prochain coup = %d dégâts", self.power_special_damage)
            
            # Mettre à jour le flag d'activation pour l'affichage
            self.power_active = getattr(self, 'special_piercing', False)

            # remove pieces with zero hp and persist
            for pc in pieces_destroyed:
                try:
                    self.pieces.remove(pc)
                except ValueError:
                    pass
                try:
                    self._write_db()
                except Exception:
                    pass
                if pc.get('type') == 'K':
                    king_color = pc.get('color')
                    if king_color == 'white':
                        winner = 0
                    else:
                        winner = 1
                    self.game_over = {"winner": winner, "king_color": king_color}
                    logger.info("Game over: king %s destroyed, winner=%s", king_color, winner)

        # Paddle collisions
        # Paddle collisions - use circle-rect collision test to be robust against tunneling
        # paddle collision handling: use axis test and reflect velocity across
        # the contact normal so that hitting the top/bottom of a paddle always
        # reflects vertically, and hitting the sides reflects horizontally.
        # Also add a tiny per-paddle cooldown to avoid rapid repeated flips.
        if not hasattr(self, '_last_paddle_hit'):
            self._last_paddle_hit = [0.0, 0.0]
        now_ts = time.time()
        for i_paddle in (0, 1):
            p = self.paddles[i_paddle]
            left_p, top_p, right_p, bottom_p = p.get_bounds()
            nearest_x = max(left_p, min(self.ball.x, right_p))
            nearest_y = max(top_p, min(self.ball.y, bottom_p))
            ddx = self.ball.x - nearest_x
            ddy = self.ball.y - nearest_y
            if ddx*ddx + ddy*ddy <= (self.ball.radius)**2:
                # cooldown per paddle
                if now_ts - self._last_paddle_hit[i_paddle] < 0.06:
                    continue
                self._last_paddle_hit[i_paddle] = now_ts
                # decide axis by overlap (smaller overlap => axis of collision)
                overlap_x = min(self.ball.x - left_p, right_p - self.ball.x)
                overlap_y = min(self.ball.y - top_p, bottom_p - self.ball.y)
                s_pre = math.hypot(self.ball.dx, self.ball.dy)
                # compute horizontal offset from paddle center
                try:
                    offset = (self.ball.x - p.x) / (p.width/2)
                except Exception:
                    offset = 0
                if overlap_x < overlap_y:
                    # side collision: reflect horizontally
                    if self.ball.x < (left_p + right_p)/2:
                        # hit left side -> place ball left
                        self.ball.x = left_p - self.ball.radius
                    else:
                        self.ball.x = right_p + self.ball.radius
                    self.ball.dx *= -1
                    # apply horizontal impulse from hit offset
                    self.ball.dy += offset * 50
                else:
                    # vertical collision: reflect vertically
                    if self.ball.y < (top_p + bottom_p)/2:
                        # hit top side -> place ball above
                        self.ball.y = top_p - self.ball.radius
                        # ensure dy is negative (going up)
                        self.ball.dy = -abs(self.ball.dy)
                    else:
                        # hit bottom side -> place ball below
                        self.ball.y = bottom_p + self.ball.radius
                        # ensure dy is positive (going down)
                        self.ball.dy = abs(self.ball.dy)
                    # apply horizontal deflection based on hit position
                    self.ball.dx += offset * 100
                # normalize to preserve previous speed magnitude
                cur_s = math.hypot(self.ball.dx, self.ball.dy)
                if cur_s > 0 and s_pre > 0:
                    k = s_pre / cur_s
                    self.ball.dx *= k
                    self.ball.dy *= k
                collided = True

        scored = None

        # cap ball speed
        max_speed = 800
        s = math.hypot(self.ball.dx, self.ball.dy)
        if s > max_speed:
            k = max_speed / s
            self.ball.dx *= k
            self.ball.dy *= k

        # expose power flags to the renderer via the ball dict
        try:
            self.ball.special_ready = bool(self.power_ready)
            self.ball.special_active = bool(getattr(self, 'special_piercing', False))
        except Exception:
            pass

        return {"scored": scored, "collided": collided}

    def get_state(self):
        # include board and pieces in pixel coordinates for clients
        pieces_px = []
        for pc in self.pieces:
            col = pc['col']
            row = pc['row']
            x = self.board['x'] + col * self.board['cell_size'] + self.board['cell_size']/2
            y = self.board['y'] + row * self.board['cell_size'] + self.board['cell_size']/2
            pieces_px.append({
                "type": pc['type'],
                "color": pc['color'],
                "col": col,
                "row": row,
                "x": x,
                "y": y,
                "size": self.board['cell_size'],
                "hp": pc.get('hp', self.hp_map.get(pc.get('type'), 1)),
                "max_hp": pc.get('max_hp', self.hp_map.get(pc.get('type'), 1))
            })

        power_state = {
            "charge": int(getattr(self, 'power_charge', 0)),
            "max_charge": int(getattr(self, 'power_max_charge', DEFAULT_POWER_CONFIG['charge_max'])),
            "ready": bool(getattr(self, 'power_ready', False)),
            "active": bool(getattr(self, 'special_piercing', False)),
            "special_damage": int(getattr(self, 'power_special_damage', DEFAULT_POWER_CONFIG['special_damage'])),
            "remaining_damage": int(getattr(self, 'special_remaining_damage', 0))
        }

        return {
            "width": self.WIDTH,
            "height": self.HEIGHT,
            "board": dict(self.board),
            "ball": self.ball.to_dict(),
            "paddles": [p.to_dict() for p in self.paddles],
            "pieces": pieces_px,
            "scores": list(self.scores),
            "timestamp": time.time(),
            "game_over": self.game_over,
            "waiting_trajectory": getattr(self, 'waiting_trajectory', False),
            "power": power_state
        }

    def reset_game(self):
        # Recompute cols/rows in case EXTRA_DIMENSIONS changed, reconfigure
        # board geometry and paddles, then create a new per-game state.
        try:
            raw_dims = os.environ.get('EXTRA_DIMENSIONS')
            try:
                if raw_dims is not None:
                    dims = int(raw_dims)
                    if dims in (2,4,6,8):
                        self.active_cols = dims
                    else:
                        self.active_cols = COLS
                else:
                    self.active_cols = COLS
            except Exception:
                self.active_cols = COLS

            # recompute board geometry and paddles
            margin = 20
            board_w = self.WIDTH - margin * 2
            board_h = self.HEIGHT - margin * 2
            base_cell = min(board_w / COLS, board_h / ROWS)
            cell_size = max(8, int(base_cell))
            board_pixel_w = cell_size * self.active_cols
            board_pixel_h = cell_size * ROWS
            board_x0 = (self.WIDTH - board_pixel_w) / 2
            board_y0 = (self.HEIGHT - board_pixel_h) / 2
            self.board = {
                "cols": self.active_cols,
                "rows": ROWS,
                "cell_size": cell_size,
                "x": board_x0,
                "y": board_y0,
                "width": board_pixel_w,
                "height": board_pixel_h,
            }
            if self.active_cols == 2:
                pad_w = max(int(cell_size * 0.9), int(cell_size))
                pad_h = max(3, int(cell_size * 0.08))
                ball_radius = max(3, int(cell_size * 0.10))
            else:
                pad_w = cell_size * 1.75
                pad_h = cell_size * 0.25
                ball_radius = max(6, int(cell_size * 0.2))
            top_paddle_y = board_y0 + cell_size * 2 + pad_h/2 + 4
            bottom_paddle_y = board_y0 + cell_size * (ROWS - 2) - pad_h/2 - 4
            center_x = self.WIDTH / 2
            self.paddles = [
                Paddle(x=center_x, y=top_paddle_y, width=pad_w, height=pad_h, color="#00CCFF"),
                Paddle(x=center_x, y=bottom_paddle_y, width=pad_w, height=pad_h, color="#FFCC00")
            ]
            self.ball = Ball(x=self.WIDTH/2, y=self.HEIGHT/2, radius=ball_radius, color="#FFFFFF", speed=350)
            self._reset_power_state(reload_config=True)

            self._create_new_game_from_template()
            # reset ball position and require player 1 to choose trajectory again
            self.reset_ball(toward_bottom=True)
            # ensure ball doesn't move until trajectory chosen
            try:
                self.ball.dx = 0.0
                self.ball.dy = 0.0
            except Exception:
                pass
            # require new trajectory choice
            self.waiting_trajectory = True
            self.pending_trajectory = None
            self.game_over = None
            logger.info('Game reset: new per-game file created %s', self.db_path)
        except Exception:
            logger.exception('Failed to reset game')

