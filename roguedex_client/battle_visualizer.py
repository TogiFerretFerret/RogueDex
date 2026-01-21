import pygame
from battledex_engine.state import GameState, GRID_WIDTH, GRID_HEIGHT, BUFFER_HEIGHT
from battledex_engine.tetromino import COLORS

# Colors
BG_COLOR = (20, 20, 20)
GRID_BG_COLOR = (40, 40, 40)
GRID_LINE_COLOR = (60, 60, 60)
TEXT_COLOR = (240, 240, 240)
GHOST_ALPHA = 60

class BattleVisualizer:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, combatant_map=None):
        self.screen = screen
        self.font = font
        self.combatant_map = combatant_map 
        self.small_font = pygame.font.Font(None, 20)
        self._update_layout()

    def _update_layout(self):
        self.width, self.height = self.screen.get_size()
        
        # Target ~60% of height for a more compact feel
        ideal_h = int((self.height * 0.6) / GRID_HEIGHT)
        ideal_w = int((self.width * 0.3) / GRID_WIDTH)
        
        self.block_size = min(30, max(15, min(ideal_h, ideal_w)))
        self.grid_w = GRID_WIDTH * self.block_size
        self.grid_h = GRID_HEIGHT * self.block_size
        
        self.grid_x = (self.width - self.grid_w) // 2
        self.grid_y = (self.height - self.grid_h) // 2
        
        # Increased side panel space and fixed gaps
        self.side_w = 120
        self.gap = 60

    def draw(self, state: GameState, logs: list = None, opponents: dict = None):
        self._update_layout() # Refresh layout
        self.screen.fill(BG_COLOR)
        
        self._draw_grid_background()
        self._draw_locked_blocks(state)
        self._draw_ghost_piece(state)
        self._draw_active_piece(state)
        self._draw_grid_overlay()
        
        self._draw_hold_queue(state)
        self._draw_next_queue(state)
        self._draw_stats(state)
        self._draw_rhythm_indicator(state)
        self._draw_attack_buffer(state)
        
        if opponents:
            self._draw_opponents(opponents)

        if state.game_over:
            self._draw_game_over()

    def _to_screen_coords(self, grid_x, grid_y):
        screen_x = self.grid_x + (grid_x * self.block_size)
        screen_y = self.grid_y + ((grid_y - BUFFER_HEIGHT) * self.block_size)
        return screen_x, screen_y

    def _draw_grid_background(self):
        rect = (self.grid_x, self.grid_y, self.grid_w, self.grid_h)
        pygame.draw.rect(self.screen, GRID_BG_COLOR, rect)

    def _draw_grid_overlay(self):
        # Vertical lines
        for x in range(GRID_WIDTH + 1):
            px = self.grid_x + x * self.block_size
            pygame.draw.line(self.screen, GRID_LINE_COLOR, (px, self.grid_y), (px, self.grid_y + self.grid_h))
        # Horizontal lines
        for y in range(GRID_HEIGHT + 1):
            py = self.grid_y + y * self.block_size
            pygame.draw.line(self.screen, GRID_LINE_COLOR, (self.grid_x, py), (self.grid_x + self.grid_w, py))
        # Border and Buffer line
        pygame.draw.rect(self.screen, (100, 100, 100), (self.grid_x, self.grid_y, self.grid_w, self.grid_h), 2)
        pygame.draw.line(self.screen, (200, 50, 50), (self.grid_x, self.grid_y), (self.grid_x + self.grid_w, self.grid_y), 3)

    def _draw_block(self, x, y, color, alpha=255, outline=True):
        if y < BUFFER_HEIGHT: return
        sx, sy = self._to_screen_coords(x, y)
        rect = (sx, sy, self.block_size, self.block_size)
        if alpha < 255:
            s = pygame.Surface((self.block_size, self.block_size))
            s.set_alpha(alpha); s.fill(color); self.screen.blit(s, (sx, sy))
        else: pygame.draw.rect(self.screen, color, rect)
        if outline: pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

    def _draw_locked_blocks(self, state: GameState):
        for y, row in enumerate(state.grid):
            for x, cell in enumerate(row):
                if cell != 0: self._draw_block(x, y, COLORS.get(cell, (100, 100, 100)))

    def _draw_active_piece(self, state: GameState):
        if state.current_piece:
            color = COLORS.get(state.current_piece.shape, (255, 255, 255))
            for x, y in state.current_piece.get_blocks(): self._draw_block(x, y, color)

    def _draw_ghost_piece(self, state: GameState):
        piece = state.current_piece
        if not piece: return
        gy = piece.y
        from battledex_engine.tetromino import SHAPES
        local_coords = SHAPES[piece.shape][piece.rotation]
        while True:
            collision = False
            for lx, ly in local_coords:
                bx, by = piece.x + lx, gy + 1 + ly
                if bx < 0 or bx >= GRID_WIDTH or by >= len(state.grid) or (by >= 0 and state.grid[by][bx] != 0):
                    collision = True; break
            if collision: break
            gy += 1
        color = COLORS.get(piece.shape, (255, 255, 255))
        for lx, ly in local_coords: self._draw_block(piece.x + lx, gy + ly, color, alpha=GHOST_ALPHA)

    def _draw_hold_queue(self, state: GameState):
        hx = self.grid_x - self.side_w - self.gap
        hy = self.grid_y
        self.screen.blit(self.font.render("HOLD", True, TEXT_COLOR), (hx, hy - 35))
        pygame.draw.rect(self.screen, GRID_BG_COLOR, (hx, hy, self.side_w, self.side_w))
        pygame.draw.rect(self.screen, (100, 100, 100), (hx, hy, self.side_w, self.side_w), 1)
        if state.hold_piece: self._draw_mini_piece(state.hold_piece, hx + self.side_w // 2, hy + self.side_w // 2)

    def _draw_next_queue(self, state: GameState):
        nx = self.grid_x + self.grid_w + self.gap
        ny = self.grid_y
        self.screen.blit(self.font.render("NEXT", True, TEXT_COLOR), (nx, ny - 35))
        for i, shape in enumerate(state.next_queue[:5]):
            slot_y = ny + i * (self.side_w + 10)
            pygame.draw.rect(self.screen, GRID_BG_COLOR, (nx, slot_y, self.side_w, self.side_w))
            pygame.draw.rect(self.screen, (100, 100, 100), (nx, slot_y, self.side_w, self.side_w), 1)
            self._draw_mini_piece(shape, nx + self.side_w // 2, slot_y + self.side_w // 2)

    def _draw_mini_piece(self, shape, cx, cy):
        from battledex_engine.tetromino import SHAPES
        coords = SHAPES[shape][0]
        mini_size = self.block_size if self.block_size > 20 else 20
        min_x, max_x = min(c[0] for c in coords), max(c[0] for c in coords)
        min_y, max_y = min(c[1] for c in coords), max(c[1] for c in coords)
        w, h = (max_x - min_x + 1) * mini_size, (max_y - min_y + 1) * mini_size
        sx, sy = cx - w // 2, cy - h // 2
        for x, y in coords:
            pygame.draw.rect(self.screen, COLORS[shape], (sx + (x - min_x) * mini_size, sy + (y - min_y) * mini_size, mini_size, mini_size))
            pygame.draw.rect(self.screen, (0,0,0), (sx + (x - min_x) * mini_size, sy + (y - min_y) * mini_size, mini_size, mini_size), 1)

    def _draw_stats(self, state: GameState):
        # Align stats to the left of the hold box
        sx = self.grid_x - self.side_w - self.gap
        sy = self.grid_y + self.side_w + 60
        stats = [f"SCORE: {state.score}", f"LEVEL: {state.level}", f"LINES: {state.lines_cleared}", f"COMBO: {max(0, state.combo)}"]
        for i, line in enumerate(stats): self.screen.blit(self.font.render(line, True, TEXT_COLOR), (sx, sy + i * 45))

    def _draw_rhythm_indicator(self, state: GameState):
        rx, ry, rw, rh = self.grid_x, self.grid_y + self.grid_h + 20, self.grid_w, int(self.block_size * 1.5)
        pygame.draw.rect(self.screen, GRID_BG_COLOR, (rx, ry, rw, rh))
        pygame.draw.rect(self.screen, (100, 100, 100), (rx, ry, rw, rh), 1)
        
        beat_duration = 60.0 / state.bpm
        beat_prog = state.current_beat % 1.0
        cur_x = rx + beat_prog * rw
        pygame.draw.line(self.screen, (255, 255, 255), (cur_x, ry), (cur_x, ry + rh), 2)
        
        # Window width in percentage of a beat
        # engine.beat_window is 0.1s. Total window is +/- 0.1s.
        win_percent = 0.1 / beat_duration
        win_w = win_percent * rw
        
        # Draw hit zones at start and end of the bar
        pygame.draw.rect(self.screen, (0, 255, 0), (rx, ry, win_w, rh), 2)
        pygame.draw.rect(self.screen, (0, 255, 0), (rx + rw - win_w, ry, win_w, rh), 2)
        
        # Pulsing circle: match engine logic (offset <= 0.1)
        # offset = abs(beat_prog - round(beat_prog)) * beat_duration
        is_on_beat = (abs(beat_prog - round(beat_prog)) * beat_duration) <= 0.1
        
        if is_on_beat: pygame.draw.circle(self.screen, (0, 255, 0), (rx - 30, ry + rh // 2), 10)
        else: pygame.draw.circle(self.screen, (100, 0, 0), (rx - 30, ry + rh // 2), 5)

    def _draw_attack_buffer(self, state: GameState):
        if hasattr(state, 'attack_buffer') and state.attack_buffer > 0:
            self.screen.blit(self.font.render(f"READY: {state.attack_buffer} L", True, (255, 100, 100)), (self.grid_x, self.grid_y + self.grid_h + 70))

    def _draw_opponents(self, opponents):
        ox_start = self.grid_x + self.grid_w + self.side_w + 60
        oy_start, m_size = self.grid_y, self.block_size // 3
        for i, (oid, data) in enumerate(opponents.items()):
            if i > 2: break
            ox = ox_start + i * (GRID_WIDTH * m_size + 30)
            self.screen.blit(self.small_font.render(oid[:10], True, TEXT_COLOR), (ox, oy_start - 25))
            pygame.draw.rect(self.screen, GRID_BG_COLOR, (ox, oy_start, GRID_WIDTH * m_size, GRID_HEIGHT * m_size))
            grid = data.get("grid", [])
            for gy, row in enumerate(grid):
                for gx, cell in enumerate(row):
                    if cell != 0: pygame.draw.rect(self.screen, COLORS.get(cell, (100, 100, 100)), (ox + gx * m_size, oy_start + gy * m_size, m_size, m_size))
            self.screen.blit(self.small_font.render(f"S: {data.get('score', 0)}", True, TEXT_COLOR), (ox, oy_start + GRID_HEIGHT * m_size + 5))

    def _draw_game_over(self):
        overlay = pygame.Surface((self.width, self.height)); overlay.set_alpha(180); overlay.fill((0, 0, 0)); self.screen.blit(overlay, (0, 0))
        t = self.font.render("GAME OVER", True, (255, 50, 50))
        self.screen.blit(t, t.get_rect(center=(self.width // 2, self.height // 2)))
        s = self.small_font.render("Press SPACE to restart", True, (200, 200, 200))
        self.screen.blit(s, s.get_rect(center=(self.width // 2, self.height // 2 + 50)))