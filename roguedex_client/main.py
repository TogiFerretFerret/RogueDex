import sys
import os
import pygame
import time

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battledex_engine.tetris_engine import TetrisEngine
from battledex_engine.rogue_bot import RogueBot
from roguedex_client.battle_visualizer import BattleVisualizer

# Sample Bot Script (RogueScript)
BOT_SCRIPT = """
var x = get_piece_x();
if (x < 4) {
    move_right();
}
if (x > 4) {
    move_left();
}
// Simple: always drop
hard_drop();
"""

class RogueDexTetrisClient:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.width = 800
        self.height = 750
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("RogueDex Rhythm Tetris")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)

        # Game Engine
        self.engine = TetrisEngine(bpm=128.0)
        
        # Bot
        self.bot = RogueBot(self.engine)
        self.auto_mode = False
        self.last_bot_tick = 0
        
        # Visualizer
        self.visualizer = BattleVisualizer(self.screen, self.font)
        
        self.running = True

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            self._handle_input()
            self._update(dt)
            self._draw()

        pygame.quit()
        sys.exit()

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_keydown(self, key):
        if self.engine.state.game_over:
            if key == pygame.K_SPACE:
                self.engine = TetrisEngine(bpm=128.0)
                self.bot = RogueBot(self.engine)
            return

        # Toggle Auto Mode
        if key == pygame.K_a:
            self.auto_mode = not self.auto_mode
            print(f"Auto Mode: {'ON' if self.auto_mode else 'OFF'}")
            return

        if self.auto_mode:
             # Manual override or ignore? Let's allow manual moves.
             pass

        if key == pygame.K_LEFT:
            self.engine.submit_action('move_left')
        elif key == pygame.K_RIGHT:
            self.engine.submit_action('move_right')
        elif key == pygame.K_DOWN:
            self.engine.submit_action('move_down')
        elif key == pygame.K_UP:
            self.engine.submit_action('rotate_cw')
        elif key == pygame.K_z:
            self.engine.submit_action('rotate_ccw')
        elif key == pygame.K_x:
            self.engine.submit_action('rotate_cw')
        elif key == pygame.K_SPACE:
            self.engine.submit_action('hard_drop')
        elif key == pygame.K_c or key == pygame.K_LSHIFT:
            self.engine.submit_action('hold')
        elif key == pygame.K_ESCAPE:
            self.running = False

    def _update(self, dt):
        self.engine.update(dt)
        
        if self.auto_mode and not self.engine.state.game_over:
            # Run bot logic periodically or every beat?
            # Let's try running it every 0.5s if it's on beat.
            on_beat, _ = self.engine.is_on_beat()
            if on_beat:
                now = time.time()
                # Ensure we only "think" once per beat window
                if now - self.last_bot_tick > 0.2:
                    self.bot.run_script(BOT_SCRIPT)
                    self.last_bot_tick = now

    def _draw(self):
        self.visualizer.draw(self.engine.state)
        
        # Draw Auto Mode Status
        if self.auto_mode:
            text = self.font.render("AUTO MODE ACTIVE", True, (255, 200, 0))
            self.screen.blit(text, (20, 20))
            
        pygame.display.flip()

if __name__ == "__main__":
    app = RogueDexTetrisClient()
    app.run()