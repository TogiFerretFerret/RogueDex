import pygame
from battledex_engine.state import GameState, GRID_WIDTH, GRID_HEIGHT, BUFFER_HEIGHT
from battledex_engine.tetromino import COLORS

# UI Configuration
BLOCK_SIZE = 30
GRID_OFFSET_X = 300
GRID_OFFSET_Y = 50
SIDE_PANEL_WIDTH = 150

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
        # combatant_map is kept for signature compatibility but unused
        self.combatant_map = combatant_map 
        
        self.small_font = pygame.font.Font(None, 20)

    def draw(self, state: GameState, logs: list = None, opponents: dict = None):
        """
        Draws the complete Tetris game state.
        """
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
        
        # Draw Opponents
        if opponents:
            self._draw_opponents(opponents)

        if state.game_over:
            self._draw_game_over()

    def _draw_opponents(self, opponents):
        # Position them on the far right
        x_start = GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 180
        y_start = GRID_OFFSET_Y
        
        mini_block = 10
        for i, (oid, data) in enumerate(opponents.items()):
            if i > 2: break # Max 3 opponents visible
            
            ox = x_start + i * (GRID_WIDTH * mini_block + 20)
            
            # Label
            name = self.small_font.render(oid[:10], True, TEXT_COLOR)
            self.screen.blit(name, (ox, y_start - 20))
            
            # Board
            grid = data.get("grid", [])
            pygame.draw.rect(self.screen, GRID_BG_COLOR, (ox, y_start, GRID_WIDTH * mini_block, GRID_HEIGHT * mini_block))
            for gy, row in enumerate(grid):
                for gx, cell in enumerate(row):
                    if cell != 0:
                        color = COLORS.get(cell, (100, 100, 100))
                        pygame.draw.rect(self.screen, color, (ox + gx * mini_block, y_start + gy * mini_block, mini_block, mini_block))
            
            # Score
            score = self.small_font.render(f"S: {data.get('score', 0)}", True, TEXT_COLOR)
            self.screen.blit(score, (ox, y_start + GRID_HEIGHT * mini_block + 5))
    
    def _draw_rhythm_indicator(self, state: GameState):
        x_start = GRID_OFFSET_X
        y_pos = GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE + 20
        width = GRID_WIDTH * BLOCK_SIZE
        height = 40
        
        # Background
        pygame.draw.rect(self.screen, GRID_BG_COLOR, (x_start, y_pos, width, height))
        pygame.draw.rect(self.screen, (100, 100, 100), (x_start, y_pos, width, height), 1)
        
        # Beat Progress (0 to 1)
        beat_progress = state.current_beat % 1.0
        
        # Draw a moving bar or cursor
        cursor_x = x_start + beat_progress * width
        pygame.draw.line(self.screen, (255, 255, 255), (cursor_x, y_pos), (cursor_x, y_pos + height), 2)
        
        # Draw "Hit Zone" (center, 0.5 is usually the beat if we align it)
        # Actually, let's say 0.0/1.0 is the beat.
        window_width = (0.1 / (60.0 / state.bpm)) * width # approximate window in pixels
        
        # Zone at start/end
        pygame.draw.rect(self.screen, (0, 255, 0), (x_start, y_pos, window_width, height), 2)
        pygame.draw.rect(self.screen, (0, 255, 0), (x_start + width - window_width, y_pos, window_width, height), 2)
        
        # Pulsing circle if on beat
        is_on_beat = beat_progress < 0.1 or beat_progress > 0.9
        if is_on_beat:
             pygame.draw.circle(self.screen, (0, 255, 0), (x_start - 30, y_pos + height // 2), 10)
        else:
             pygame.draw.circle(self.screen, (100, 0, 0), (x_start - 30, y_pos + height // 2), 5)

    def _to_screen_coords(self, grid_x, grid_y):
        # We only draw the visible height (GRID_HEIGHT = 20)
        # grid_y starts at 0 (top of total buffer).
        # Visible rows start at BUFFER_HEIGHT (20).
        # We want visible row 0 (index BUFFER_HEIGHT) to be at GRID_OFFSET_Y
        
        screen_x = GRID_OFFSET_X + (grid_x * BLOCK_SIZE)
        screen_y = GRID_OFFSET_Y + ((grid_y - BUFFER_HEIGHT) * BLOCK_SIZE)
        return screen_x, screen_y

    def _draw_grid_background(self):
        rect = (GRID_OFFSET_X, GRID_OFFSET_Y, GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE)
        pygame.draw.rect(self.screen, GRID_BG_COLOR, rect)

    def _draw_grid_overlay(self):
        # Vertical lines
        for x in range(GRID_WIDTH + 1):
            px = GRID_OFFSET_X + x * BLOCK_SIZE
            start = (px, GRID_OFFSET_Y)
            end = (px, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE)
            pygame.draw.line(self.screen, GRID_LINE_COLOR, start, end)
            
        # Horizontal lines
        for y in range(GRID_HEIGHT + 1):
            py = GRID_OFFSET_Y + y * BLOCK_SIZE
            start = (GRID_OFFSET_X, py)
            end = (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE, py)
            pygame.draw.line(self.screen, GRID_LINE_COLOR, start, end)
            
        # Border
        rect = (GRID_OFFSET_X, GRID_OFFSET_Y, GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE)
        pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)

        # Buffer Line (Top of visible area)
        # Since grid starts at Y=0 relative to offset, this is just the top line.
        # But let's make it distinct (Red) to show "Death Line"
        pygame.draw.line(self.screen, (200, 50, 50), 
                         (GRID_OFFSET_X, GRID_OFFSET_Y), 
                         (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE, GRID_OFFSET_Y), 3)

    def _draw_block(self, x, y, color, alpha=255, outline=True):
        # Don't draw blocks above the visible area
        if y < BUFFER_HEIGHT:
            return

        screen_x, screen_y = self._to_screen_coords(x, y)
        
        rect = (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE)
        
        if alpha < 255:
            s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
            s.set_alpha(alpha)
            s.fill(color)
            self.screen.blit(s, (screen_x, screen_y))
        else:
            pygame.draw.rect(self.screen, color, rect)
            
        if outline:
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

    def _draw_locked_blocks(self, state: GameState):
        for y, row in enumerate(state.grid):
            for x, cell in enumerate(row):
                if cell != 0:
                    color = COLORS.get(cell, (100, 100, 100))
                    self._draw_block(x, y, color)

    def _draw_active_piece(self, state: GameState):
        piece = state.current_piece
        if not piece:
            return
        
        color = COLORS.get(piece.shape, (255, 255, 255))
        for x, y in piece.get_blocks():
            self._draw_block(x, y, color)

    def _draw_ghost_piece(self, state: GameState):
        piece = state.current_piece
        if not piece:
            return
        
        # Hard clone to find drop position
        # We can't import TetrisEngine here to use move logic logic easily without dependency cycles or duplication.
        # So we implement a simple drop check here or trust the state to have it? 
        # State doesn't have ghost pos.
        # We will do a simple simulate drop loop here.
        # NOTE: This requires collision logic which is in Engine. 
        # Ideally, Engine should provide ghost coordinates in State.
        # For now, we skip ghost or implement basic collision:
        
        ghost_y = piece.y
        while True:
            # Check collision at ghost_y + 1
            # We need to replicate basic collision check strictly against grid
            collision = False
            blocks = []
            local_coords = from_shape_data(piece.shape, piece.rotation)
            
            # Predict next step
            test_y = ghost_y + 1
            
            for lx, ly in local_coords:
                bx = piece.x + lx
                by = test_y + ly
                if bx < 0 or bx >= GRID_WIDTH or by >= len(state.grid):
                    collision = True
                    break
                if by >= 0 and state.grid[by][bx] != 0:
                    collision = True
                    break
            
            if collision:
                break
            ghost_y += 1
            
        color = COLORS.get(piece.shape, (255, 255, 255))
        local_coords = from_shape_data(piece.shape, piece.rotation)
        for lx, ly in local_coords:
            self._draw_block(piece.x + lx, ghost_y + ly, color, alpha=GHOST_ALPHA)


    def _draw_hold_queue(self, state: GameState):
        x_start = GRID_OFFSET_X - SIDE_PANEL_WIDTH + 20
        y_start = GRID_OFFSET_Y
        
        label = self.font.render("HOLD", True, TEXT_COLOR)
        self.screen.blit(label, (x_start, y_start - 30))
        
        pygame.draw.rect(self.screen, GRID_BG_COLOR, (x_start, y_start, 100, 100))
        pygame.draw.rect(self.screen, (100, 100, 100), (x_start, y_start, 100, 100), 1)

        if state.hold_piece:
            self._draw_mini_piece(state.hold_piece, x_start + 50, y_start + 50)
            
        if not state.can_hold:
             # Draw a red X or gray out indicating used?
             pass

    def _draw_next_queue(self, state: GameState):
        x_start = GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 30
        y_start = GRID_OFFSET_Y
        
        label = self.font.render("NEXT", True, TEXT_COLOR)
        self.screen.blit(label, (x_start, y_start - 30))
        
        # Draw slots for next 5 (or fewer)
        for i, shape in enumerate(state.next_queue[:5]):
            y_pos = y_start + i * 90
            pygame.draw.rect(self.screen, GRID_BG_COLOR, (x_start, y_pos, 100, 80))
            pygame.draw.rect(self.screen, (100, 100, 100), (x_start, y_pos, 100, 80), 1)
            self._draw_mini_piece(shape, x_start + 50, y_pos + 40)

    def _draw_mini_piece(self, shape, cx, cy):
        # Draw a piece centered at cx, cy
        from battledex_engine.tetromino import SHAPES
        coords = SHAPES[shape][0] # Default rotation
        color = COLORS[shape]
        
        mini_size = 20
        # Calculate bounds to center
        min_x = min(c[0] for c in coords)
        max_x = max(c[0] for c in coords)
        min_y = min(c[1] for c in coords)
        max_y = max(c[1] for c in coords)
        
        w = (max_x - min_x + 1) * mini_size
        h = (max_y - min_y + 1) * mini_size
        
        start_x = cx - w // 2
        start_y = cy - h // 2
        
        for x, y in coords:
            # Shift by min to normalize 0-based, then add start
            draw_x = start_x + (x - min_x) * mini_size
            draw_y = start_y + (y - min_y) * mini_size
            
            pygame.draw.rect(self.screen, color, (draw_x, draw_y, mini_size, mini_size))
            pygame.draw.rect(self.screen, (0,0,0), (draw_x, draw_y, mini_size, mini_size), 1)

    def _draw_stats(self, state: GameState):
        x_start = GRID_OFFSET_X - SIDE_PANEL_WIDTH + 20
        y_start = GRID_OFFSET_Y + 200
        
        stats = [
            f"SCORE: {state.score}",
            f"LEVEL: {state.level}",
            f"LINES: {state.lines_cleared}",
            f"COMBO: {max(0, state.combo)}"
        ]
        
        for i, line in enumerate(stats):
            text = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (x_start, y_start + i * 30))

    def _draw_game_over(self):
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        text = self.font.render("GAME OVER", True, (255, 50, 50))
        rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(text, rect)
        
        sub = self.small_font.render("Press SPACE to restart", True, (200, 200, 200))
        sub_rect = sub.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 40))
        self.screen.blit(sub, sub_rect)

# Helper to avoid circular imports or redefining data
def from_shape_data(shape, rotation):
    from battledex_engine.tetromino import SHAPES
    return SHAPES[shape][rotation]
