import sys
import os
import pygame
import time
from enum import Enum, auto

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battledex_engine.tetris_engine import TetrisEngine
from battledex_engine.rogue_bot import RogueBot
from roguedex_client.battle_visualizer import BattleVisualizer
from roguedex_client.network_client import NetworkClient
from roguedex_client.sound_manager import SoundManager

# Sample Bot Script (RogueScript)
BOT_SCRIPT = """
var x = get_piece_x();
if (x < 4) {
    move_right();
}
if (x > 4) {
    move_left();
}
hard_drop();
"""

class GamePhase(Enum):
    MENU = auto()
    PLAYING = auto()

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
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)

        # Audio
        try:
            self.sound_manager = SoundManager()
            print("Audio initialized.")
        except Exception as e:
            print(f"Audio failed to initialize: {e}")
            self.sound_manager = None

        self.phase = GamePhase.MENU
        
        # Multiplayer Config
        self.server_ip = os.environ.get("SERVER_IP")
        self.network = None
        
        # Game State
        self.engine = None
        self.visualizer = None
        self.bot = None
        self.auto_mode = False
        
        self.running = True

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            self._handle_input()
            self._update(dt)
            self._draw()

        if self.network:
            self.network.close()
        pygame.quit()
        sys.exit()

    def start_game(self, multiplayer=False):
        self.engine = TetrisEngine(bpm=128.0)
        self.last_beat_int = 0
        self.last_lines_cleared = 0
        self.bot = RogueBot(self.engine)
        self.visualizer = BattleVisualizer(self.screen, self.font)
        
        if multiplayer and self.server_ip:
            player_id = f"Player_{int(time.time())}"
            print(f"Connecting to {self.server_ip}...")
            self.network = NetworkClient(self.server_ip, 4242, player_id)
        
        self.phase = GamePhase.PLAYING

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.phase == GamePhase.MENU:
                    self._handle_menu_input(event.key)
                elif self.phase == GamePhase.PLAYING:
                    self._handle_game_input(event.key)

    def _handle_menu_input(self, key):
        if key == pygame.K_1:
            self.start_game(multiplayer=False)
        elif key == pygame.K_2 and self.server_ip:
            self.start_game(multiplayer=True)
        elif key == pygame.K_a:
            self.auto_mode = not self.auto_mode
        elif key == pygame.K_ESCAPE:
            self.running = False

    def _handle_game_input(self, key):
        if self.engine.state.game_over:
            if key == pygame.K_SPACE:
                # Return to menu or restart? Let's restart same mode
                self.start_game(multiplayer=(self.network is not None))
            elif key == pygame.K_ESCAPE:
                self.phase = GamePhase.MENU
                if self.network:
                    self.network.close()
                    self.network = None
            return

        # Controls
        action = None
        if key == pygame.K_LEFT: action = 'move_left'
        elif key == pygame.K_RIGHT: action = 'move_right'
        elif key == pygame.K_DOWN: action = 'move_down'
        elif key == pygame.K_UP: action = 'rotate_cw'
        elif key == pygame.K_z: action = 'rotate_ccw'
        elif key == pygame.K_x: action = 'rotate_cw'
        elif key == pygame.K_SPACE: action = 'hard_drop'
        elif key == pygame.K_c or key == pygame.K_LSHIFT: action = 'hold'
        elif key == pygame.K_ESCAPE:
            self.phase = GamePhase.MENU
            if self.network:
                self.network.close()
                self.network = None
            return

        if action:
            result = self.engine.submit_action(action)
            self._play_action_sound(result)

    def _play_action_sound(self, result):
        if not self.sound_manager: return
        
        if result == 'moved':
            self.sound_manager.play('move')
        elif result == 'rotated':
            self.sound_manager.play('rotate')
        elif result == 'dropped':
            self.sound_manager.play('drop')
        elif result == 'hold':
            self.sound_manager.play('move')

    def _update(self, dt):
        if self.phase == GamePhase.PLAYING:
            self.engine.update(dt)
            
            # Beat Sound
            current_beat_int = int(self.engine.state.current_beat)
            if current_beat_int > self.last_beat_int:
                if self.sound_manager:
                    self.sound_manager.play('beat')
                self.last_beat_int = current_beat_int
            
            # Line Clear Check for Sound & Network
            current_lines = self.engine.state.lines_cleared
            diff = current_lines - self.last_lines_cleared
            if diff > 0:
                if self.sound_manager:
                    self.sound_manager.play('clear')
                
                # Network Attack
                if diff > 1 and self.network:
                    garbage = diff if diff == 4 else diff - 1
                    if garbage > 0:
                        self.network.send_attack(garbage)
            
            self.last_lines_cleared = current_lines

            # Network Messages
            if self.network:
                msgs = self.network.get_messages()
                for msg in msgs:
                    if msg.get("command") == "garbage":
                        lines = msg.get("lines", 0)
                        self.engine.add_garbage(lines)

            # Bot
            if self.auto_mode and not self.engine.state.game_over:
                on_beat, _ = self.engine.is_on_beat()
                if on_beat:
                    now = time.time()
                    if now - self.last_bot_tick > 0.2:
                        self.bot.run_script(BOT_SCRIPT)
                        self.last_bot_tick = now

    def _draw(self):
        if self.phase == GamePhase.MENU:
            self._draw_menu()
        elif self.phase == GamePhase.PLAYING:
            self.visualizer.draw(self.engine.state)
            if self.auto_mode:
                 text = self.font.render("AUTO MODE", True, (255, 200, 0))
                 self.screen.blit(text, (20, 20))
        
        pygame.display.flip()

    def _draw_menu(self):
        self.screen.fill((20, 20, 30))
        
        cx = self.width // 2
        cy = self.height // 2 - 100
        
        title = self.title_font.render("RHYTHM TETRIS", True, (0, 255, 255))
        rect = title.get_rect(center=(cx, cy))
        self.screen.blit(title, rect)
        
        options = [
            "Press [1] for Singleplayer",
            f"Press [2] for Multiplayer {'(Ready)' if self.server_ip else '(No Server IP)'}",
            f"Press [A] to Toggle Auto Bot {'(ON)' if self.auto_mode else '(OFF)'}",
            "Press [ESC] to Quit"
        ]
        
        for i, line in enumerate(options):
            text = self.font.render(line, True, (200, 200, 200))
            rect = text.get_rect(center=(cx, cy + 80 + i * 40))
            self.screen.blit(text, rect)
            
        # Instructions
        inst_y = self.height - 150
        inst_text = [
            "HOW TO PLAY:",
            "Use Arrow Keys to Move/Rotate.",
            "SPACE to Hard Drop. C to Hold.",
            "TIMING MATTERS: Actions on the beat score double points!"
        ]
        
        for i, line in enumerate(inst_text):
            color = (100, 255, 100) if i == 3 else (150, 150, 150)
            text = self.font.render(line, True, color)
            rect = text.get_rect(center=(cx, inst_y + i * 30))
            self.screen.blit(text, rect)

if __name__ == "__main__":
    app = RogueDexTetrisClient()
    app.run()
