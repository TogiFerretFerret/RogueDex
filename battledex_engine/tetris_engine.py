import random
import time
from typing import List, Tuple, Optional
from .state import GameState, GRID_WIDTH, TOTAL_HEIGHT, BUFFER_HEIGHT
from .tetromino import Tetromino, SHAPES, WALL_KICKS_JLSTZ, WALL_KICKS_I

class TetrisEngine:
    def __init__(self, bpm: float = 120.0):
        self.state = GameState()
        self.state.bpm = bpm
        self.bag = []
        self._fill_bag()
        
        # Timing
        self.start_time = time.time()
        self.last_drop_time = self.start_time
        self.gravity_delay = 1.0 
        
        # Rhythm Window (seconds)
        # 120 BPM = 0.5s per beat. Window of 0.1s is quite tight.
        self.beat_window = 0.1 
        
        self.spawn_piece()

    def _fill_bag(self):
        new_bag = list(SHAPES.keys())
        random.shuffle(new_bag)
        self.bag.extend(new_bag)

    def spawn_piece(self):
        if len(self.bag) < 7:
            self._fill_bag()
        
        while len(self.state.next_queue) <= 5:
            self.state.next_queue.append(self.bag.pop(0))
            if len(self.bag) < 7:
                self._fill_bag()

        shape = self.state.next_queue.pop(0)
        self.state.current_piece = Tetromino(shape=shape)
        self.last_drop_time = time.time()
        
        if self._check_collision(self.state.current_piece):
            self.state.game_over = True

        self.state.can_hold = True

    def _check_collision(self, piece: Tetromino) -> bool:
        for x, y in piece.get_blocks():
            if x < 0 or x >= GRID_WIDTH:
                return True
            if y >= TOTAL_HEIGHT:
                return True
            if y >= 0 and self.state.grid[y][x] != 0:
                return True
        return False

    def is_on_beat(self) -> Tuple[bool, float]:
        """Returns (is_on_beat, offset_from_nearest_beat)."""
        elapsed = time.time() - self.start_time
        beat_duration = 60.0 / self.state.bpm
        current_beat = elapsed / beat_duration
        
        offset = abs(current_beat - round(current_beat)) * beat_duration
        return (offset <= self.beat_window, offset)

    def submit_action(self, action_type: str, *args) -> bool:
        """
        Executes an action and applies rhythm bonuses.
        action_type: 'move_left', 'move_right', 'move_down', 'rotate_cw', 'rotate_ccw', 'hard_drop', 'hold'
        """
        if self.state.game_over:
            return False

        on_beat, offset = self.is_on_beat()
        multiplier = 2.0 if on_beat else 1.0
        
        success = False
        if action_type == 'move_left':
            success = self.move(-1, 0)
        elif action_type == 'move_right':
            success = self.move(1, 0)
        elif action_type == 'move_down':
            success = self.move(0, 1)
        elif action_type == 'rotate_cw':
            success = self.rotate(True)
        elif action_type == 'rotate_ccw':
            success = self.rotate(False)
        elif action_type == 'hard_drop':
            self.hard_drop(multiplier)
            success = True
        elif action_type == 'hold':
            self.hold()
            success = True
            
        if success and on_beat:
            self.state.score += int(10 * multiplier)
            
        return success

    def move(self, dx: int, dy: int) -> bool:
        if self.state.game_over or not self.state.current_piece:
            return False

        piece = self.state.current_piece
        piece.x += dx
        piece.y += dy

        if self._check_collision(piece):
            piece.x -= dx
            piece.y -= dy
            return False
            
        if dy > 0:
             self.last_drop_time = time.time()
        return True

    def rotate(self, clockwise: bool = True) -> bool:
        if self.state.game_over or not self.state.current_piece:
            return False

        piece = self.state.current_piece
        old_rotation = piece.rotation
        new_rotation = (piece.rotation + 1) % 4 if clockwise else (piece.rotation - 1) % 4
        
        kick_key = (old_rotation, new_rotation)
        
        if piece.shape == 'I':
            kicks = WALL_KICKS_I.get(kick_key, [(0, 0)])
        elif piece.shape == 'O':
            kicks = [(0, 0)]
        else:
            kicks = WALL_KICKS_JLSTZ.get(kick_key, [(0, 0)])

        piece.rotation = new_rotation
        
        for kx, ky in kicks:
            piece.x += kx
            piece.y -= ky
            if not self._check_collision(piece):
                return True
            piece.x -= kx
            piece.y += ky
            
        piece.rotation = old_rotation
        return False

    def hard_drop(self, multiplier: float = 1.0):
        if self.state.game_over or not self.state.current_piece:
            return
        
        dropped_cells = 0
        while self.move(0, 1):
            dropped_cells += 1
        
        self.state.score += int(dropped_cells * 2 * multiplier)
        self.lock_piece()

    def lock_piece(self):
        if not self.state.current_piece:
            return

        for x, y in self.state.current_piece.get_blocks():
            if 0 <= y < TOTAL_HEIGHT:
                self.state.grid[y][x] = self.state.current_piece.shape
            elif y < 0:
                 self.state.game_over = True

        self._clear_lines()
        self.state.current_piece = None
        self.spawn_piece()

    def _clear_lines(self):
        lines_to_clear = []
        for y in range(TOTAL_HEIGHT):
            if 0 not in self.state.grid[y]:
                lines_to_clear.append(y)
        
        num_cleared = len(lines_to_clear)
        if num_cleared == 0:
            if self.state.combo > -1:
                self.state.combo = -1
            return

        on_beat, _ = self.is_on_beat()
        rhythm_bonus = 1.5 if on_beat else 1.0

        base_scores = {1: 100, 2: 300, 3: 500, 4: 800}
        self.state.score += int(base_scores.get(num_cleared, 0) * self.state.level * rhythm_bonus)
        
        self.state.lines_cleared += num_cleared
        self.state.combo += 1
        
        for row_idx in lines_to_clear:
            del self.state.grid[row_idx]
            self.state.grid.insert(0, [0] * GRID_WIDTH)

        if self.state.lines_cleared >= self.state.level * 10:
            self.state.level += 1

    def hold(self):
        if not self.state.can_hold or self.state.game_over:
            return
        
        current_shape = self.state.current_piece.shape
        
        if self.state.hold_piece is None:
            self.state.hold_piece = current_shape
            self.spawn_piece() 
        else:
            temp = self.state.hold_piece
            self.state.hold_piece = current_shape
            self.state.current_piece = Tetromino(shape=temp)
            self.state.current_piece.x = 3
            self.state.current_piece.y = -1
            self.last_drop_time = time.time()
        
        self.state.can_hold = False

    def update(self, dt: float = 0):
        if self.state.game_over or not self.state.current_piece:
            return

        # Update current beat in state for visualizer
        elapsed = time.time() - self.start_time
        beat_duration = 60.0 / self.state.bpm
        self.state.current_beat = elapsed / beat_duration

        speed_level = min(20, self.state.level)
        self.gravity_delay = max(0.05, (1.0 - (speed_level - 1) * 0.05))

        now = time.time()
        if now - self.last_drop_time > self.gravity_delay:
            if not self.move(0, 1):
                self.lock_piece()
            self.last_drop_time = now
