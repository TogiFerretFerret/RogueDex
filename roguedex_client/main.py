import sys
import os
import pygame
import time
import random
from enum import Enum, auto

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battledex_engine.tetris_engine import TetrisEngine
from battledex_engine.rogue_bot import RogueBot
from roguedex_client.battle_visualizer import BattleVisualizer
from roguedex_client.network_client import NetworkClient
from roguedex_client.sound_manager import SoundManager

# Load Bot Script
def load_bot_script():
    try:
        with open("bot_script.rogue", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "hard_drop();"

class GamePhase(Enum):
    MENU = auto()
    SETTINGS = auto()
    PLAYING = auto()

class RogueDexTetrisClient:
    def __init__(self):
        pygame.init()
        self.width = 800
        self.height = 750
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("RogueDex Rhythm Tetris")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.title_font = pygame.font.Font(None, 60)
        
        self.bot_source = load_bot_script()

        try:
            self.sound_manager = SoundManager()
        except Exception as e:
            print(f"Audio failed: {e}")
            self.sound_manager = None

        self.phase = GamePhase.MENU
        self.server_ip = os.environ.get("SERVER_IP", "")
        self.network = None
        
        # Input Settings
        self.das_delay = 0.17
        self.arr_rate = 0.03
        self.soft_drop_infinite = False
        
        self.keybinds = {
            'move_left': pygame.K_LEFT,
            'move_right': pygame.K_RIGHT,
            'move_down': pygame.K_DOWN,
            'rotate_cw': pygame.K_UP,
            'rotate_ccw': pygame.K_z,
            'hard_drop': pygame.K_SPACE,
            'hold': pygame.K_c
        }
        
        self.settings_index = 0
        self.settings_options = ['Server IP', 'DAS (ms)', 'ARR (ms)', 'Infinite Soft Drop', 'Keybinds', 'Back']
        self.binding_key = None
        
        self.key_timers = {}
        self.engine = None
        self.visualizer = None
        self.bot = None
        self.auto_mode = False
        self.last_bot_tick = 0
        self.connected = False
        self.pending_start = False
        self.running = True

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_input()
            self._update(dt)
            self._draw()
        if self.network: self.network.close()
        pygame.quit()
        sys.exit()

    def start_game(self, multiplayer=False):
        if self.pending_start or self.phase == GamePhase.PLAYING: return
        self.opponents = {}
        self.update_timer = 0
        self.last_beat_int = 0
        self.last_lines_cleared = 0
        self.connected = False
        if multiplayer and self.server_ip:
            self.pending_start = True
            player_id = f"Player_{int(time.time())}_{random.randint(1000, 9999)}"
            self.network = NetworkClient(self.server_ip, 4242, player_id)
        else:
            self.pending_start = False
            self.engine = TetrisEngine(bpm=128.0)
            self.bot = RogueBot(self.engine)
            self.visualizer = BattleVisualizer(self.screen, self.font)
            self.phase = GamePhase.PLAYING

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.phase == GamePhase.MENU: self._handle_menu_input(event.key)
                elif self.phase == GamePhase.SETTINGS: self._handle_settings_input(event)
                elif self.phase == GamePhase.PLAYING: self._handle_game_keydown(event.key)
            elif event.type == pygame.KEYUP:
                if self.phase == GamePhase.PLAYING and event.key in self.key_timers:
                    del self.key_timers[event.key]

    def _handle_menu_input(self, key):
        if key == pygame.K_1: self.start_game(multiplayer=False)
        elif key == pygame.K_2:
            if self.server_ip: self.start_game(multiplayer=True)
            else: self.phase = GamePhase.SETTINGS 
        elif key == pygame.K_3: self.phase = GamePhase.SETTINGS
        elif key == pygame.K_a: self.auto_mode = not self.auto_mode
        elif key == pygame.K_r: 
            self.bot_source = load_bot_script()
            print("Bot script reloaded!")
        elif key == pygame.K_ESCAPE: self.running = False

    def _handle_settings_input(self, event):
        if self.binding_key:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE: self.keybinds[self.binding_key] = event.key
                self.binding_key = None
            return
        if event.type != pygame.KEYDOWN: return
        key = event.key
        if key == pygame.K_ESCAPE: self.phase = GamePhase.MENU; return
        if key == pygame.K_UP: self.settings_index = (self.settings_index - 1) % len(self.settings_options)
        elif key == pygame.K_DOWN: self.settings_index = (self.settings_index + 1) % len(self.settings_options)
        
        opt = self.settings_options[self.settings_index]
        if opt == 'Server IP':
            if key == pygame.K_BACKSPACE: self.server_ip = self.server_ip[:-1]
            elif event.unicode and event.unicode.isprintable() and key != pygame.K_RETURN:
                if len(self.server_ip) < 20: self.server_ip += event.unicode
        elif opt == 'DAS (ms)':
            if key == pygame.K_LEFT: self.das_delay = max(0.01, self.das_delay - 0.01)
            elif key == pygame.K_RIGHT: self.das_delay = min(0.5, self.das_delay + 0.01)
        elif opt == 'ARR (ms)':
            if key == pygame.K_LEFT: self.arr_rate = max(0.0, self.arr_rate - 0.005)
            elif key == pygame.K_RIGHT: self.arr_rate = min(0.1, self.arr_rate + 0.005)
        elif opt == 'Infinite Soft Drop':
            if key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN]: self.soft_drop_infinite = not self.soft_drop_infinite
        elif opt == 'Keybinds':
            if key == pygame.K_RETURN:
                if not hasattr(self, 'bind_idx'): self.bind_idx = 0
                keys = list(self.keybinds.keys())
                self.binding_key = keys[self.bind_idx % len(keys)]
                self.bind_idx += 1
        elif opt == 'Back' and key == pygame.K_RETURN: self.phase = GamePhase.MENU

    def _handle_game_keydown(self, key):
        if not self.engine: return
        if key in [self.keybinds['move_left'], self.keybinds['move_right'], self.keybinds['move_down']]:
            self.key_timers[key] = {'start_time': time.time(), 'last_trigger': time.time(), 'das_triggered': False}
            action = None
            if key == self.keybinds['move_left']: action = 'move_left'
            elif key == self.keybinds['move_right']: action = 'move_right'
            elif key == self.keybinds['move_down']:
                if self.soft_drop_infinite:
                    while self.engine.move(0, 1): pass
                    self._play_action_sound('moved'); return
                else: action = 'move_down'
            if action: self._play_action_sound(self.engine.submit_action(action))
            return
        if self.engine.state.game_over:
            if key == pygame.K_SPACE: self.start_game(multiplayer=(self.network is not None))
            elif key == pygame.K_ESCAPE: self.phase = GamePhase.MENU; (self.network.close() if self.network else None); self.network = None
            return
        if key == pygame.K_F5: self.bot_source = load_bot_script(); print("Bot reloaded!"); return
        action = None
        if key == self.keybinds['rotate_cw']: action = 'rotate_cw'
        elif key == self.keybinds['rotate_ccw']: action = 'rotate_ccw'
        elif key == self.keybinds['hard_drop']: action = 'hard_drop'
        elif key == self.keybinds['hold']: action = 'hold'
        elif key == pygame.K_ESCAPE: self.phase = GamePhase.MENU; (self.network.close() if self.network else None); self.network = None; return
        if action: self._play_action_sound(self.engine.submit_action(action))

    def _play_action_sound(self, result):
        if not self.sound_manager: return
        if result == 'moved': self.sound_manager.play('move')
        elif result == 'rotated': self.sound_manager.play('rotate')
        elif result == 'dropped': self.sound_manager.play('drop')
        elif result == 'hold': self.sound_manager.play('move')

    def _update(self, dt):
        if self.network:
            if self.phase == GamePhase.PLAYING:
                self.update_timer += dt
                if self.update_timer > 0.1:
                    self.network.send({"command": "update", "score": self.engine.state.score, "grid": self.engine.state.get_visible_grid()})
                    self.update_timer = 0
            for msg in self.network.get_messages():
                cmd = msg.get("command")
                if cmd == "garbage":
                    if self.engine: self.engine.add_garbage(msg.get("lines", 0))
                elif cmd == "welcome":
                    self.connected = True
                    seed = msg.get("match_seed")
                    if self.pending_start:
                        self.engine = TetrisEngine(bpm=128.0, seed=seed)
                        self.bot = RogueBot(self.engine)
                        self.visualizer = BattleVisualizer(self.screen, self.font)
                        self.phase = GamePhase.PLAYING; self.pending_start = False
                elif cmd == "opponent_update":
                    self.opponents[msg.get("player_id")] = {"score": msg.get("score"), "grid": msg.get("grid")}
        if self.phase == GamePhase.PLAYING:
            self.engine.update(dt)
            now = time.time()
            for k, d in list(self.key_timers.items()):
                if not d['das_triggered']:
                    if now - d['start_time'] >= self.das_delay: d['das_triggered'] = True; d['last_trigger'] = now; self._trigger_repeat(k)
                elif now - d['last_trigger'] >= self.arr_rate: d['last_trigger'] = now; self._trigger_repeat(k)
            if self.network and not self.connected:
                if not hasattr(self, 'login_timer'): self.login_timer = 0
                self.login_timer += dt
                if self.login_timer > 1.0: self.network.send_login(); self.login_timer = 0
            curr_beat = int(self.engine.state.current_beat)
            if curr_beat > self.last_beat_int:
                if self.sound_manager: self.sound_manager.play('beat')
                if self.network and hasattr(self.engine.state, 'attack_buffer') and self.engine.state.attack_buffer > 0:
                    self.network.send_attack(self.engine.state.attack_buffer); self.engine.state.attack_buffer = 0
                self.last_beat_int = curr_beat
            if self.engine.state.lines_cleared > self.last_lines_cleared:
                if self.sound_manager: self.sound_manager.play('clear')
                self.last_lines_cleared = self.engine.state.lines_cleared
            if self.auto_mode and not self.engine.state.game_over:
                on_beat, _ = self.engine.is_on_beat()
                if on_beat and now - self.last_bot_tick > 0.2: self.bot.run_script(self.bot_source); self.last_bot_tick = now

    def _trigger_repeat(self, key):
        action = None
        if key == self.keybinds['move_left']: action = 'move_left'
        elif key == self.keybinds['move_right']: action = 'move_right'
        elif key == self.keybinds['move_down']: action = 'move_down'
        if action: self.engine.submit_action(action)

    def _draw(self):
        if self.phase == GamePhase.MENU: self._draw_menu()
        elif self.phase == GamePhase.SETTINGS: self._draw_settings()
        elif self.phase == GamePhase.PLAYING:
            self.visualizer.draw(self.engine.state, opponents=self.opponents)
            if self.auto_mode:
                text = self.font.render("AUTO MODE", True, (255, 200, 0))
                self.screen.blit(text, (20, 20))
            if self.network:
                status_color = (0, 255, 0) if self.connected else (255, 100, 0)
                status_text = "ONLINE" if self.connected else "CONNECTING..."
                conn_text = self.font.render(status_text, True, status_color)
                self.screen.blit(conn_text, (self.width - 150, 20))
        pygame.display.flip()

    def _draw_menu(self):
        self.screen.fill((40, 40, 60))
        cx, cy = self.width // 2, self.height // 2 - 100
        title = self.title_font.render("RHYTHM TETRIS", True, (0, 255, 255))
        self.screen.blit(title, title.get_rect(center=(cx, cy)))
        opts = ["Press [1] for Singleplayer", f"Press [2] for Multiplayer {'(Ready)' if self.server_ip else '(No IP)'}", "Press [3] for Settings", f"Press [A] to Toggle Bot {'(ON)' if self.auto_mode else '(OFF)'}", "Press [R] to Reload Bot", "Press [ESC] to Quit"]
        for i, l in enumerate(opts):
            text = self.font.render(l, True, (200, 200, 200))
            self.screen.blit(text, text.get_rect(center=(cx, cy + 80 + i * 40)))
        inst_y = self.height - 150
        inst = ["FEATURES: SRS, Hold, Rhythm Scoring", "CUSTOM BOT: Edit 'bot_script.rogue'!", "TIMING: Actions on beat = bonus!", "MULTIPLAYER: Attack with garbage!"]
        for i, l in enumerate(inst):
            color = (100, 255, 100) if i == 2 else (150, 150, 150)
            text = self.font.render(l, True, color)
            self.screen.blit(text, text.get_rect(center=(cx, inst_y + i * 30)))

    def _draw_settings(self):
        self.screen.fill((40, 40, 60))
        cx, cy = self.width // 2, self.height // 2 - 150
        title = self.title_font.render("SETTINGS", True, (0, 255, 255))
        self.screen.blit(title, title.get_rect(center=(cx, cy)))
        for i, opt in enumerate(self.settings_options):
            color = (255, 255, 0) if i == self.settings_index else (200, 200, 200)
            val = ""
            if opt == 'Server IP': val = self.server_ip
            elif opt == 'DAS (ms)': val = f"{int(self.das_delay * 1000)}"
            elif opt == 'ARR (ms)': val = f"{int(self.arr_rate * 1000)}"
            elif opt == 'Infinite Soft Drop': val = "ON" if self.soft_drop_infinite else "OFF"
            elif opt == 'Keybinds': val = f"[{self.binding_key if self.binding_key else 'Press ENTER to cycle'}]"
            text = self.font.render(f"{opt}: {val}", True, color)
            self.screen.blit(text, text.get_rect(center=(cx, cy + 100 + i * 40)))
        if self.binding_key:
            overlay = pygame.Surface((self.width, self.height)); overlay.set_alpha(150); overlay.fill((0,0,0)); self.screen.blit(overlay, (0,0))
            msg = self.font.render(f"PRESS KEY FOR: {self.binding_key}", True, (255, 255, 255))
            self.screen.blit(msg, msg.get_rect(center=(cx, self.height // 2)))

if __name__ == "__main__":
    RogueDexTetrisClient().run()
