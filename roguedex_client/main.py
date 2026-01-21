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
        with open("bot_script.rogue", "r") as f: return f.read()
    except: return "hard_drop();"

class GamePhase(Enum):
    MENU = auto()
    SETTINGS = auto()
    KEYMAP = auto()
    INFO = auto()
    PLAYING = auto()

class RogueDexTetrisClient:
    def __init__(self):
        pygame.init()
        # Default starting size, but resizable
        self.width, self.height = 1000, 900
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("RogueDex Rhythm Tetris")
        self.clock = pygame.time.Clock()
        self._update_fonts()
        self.bot_source = load_bot_script()
        try: self.sound_manager = SoundManager()
        except: self.sound_manager = None

        self.phase = GamePhase.MENU
        self.server_ip = os.environ.get("SERVER_IP", "")
        self.network = None
        self.das_delay, self.arr_rate, self.soft_drop_infinite = 0.17, 0.03, False
        
        self.keybinds = {
            'move_left': pygame.K_LEFT, 'move_right': pygame.K_RIGHT, 'move_down': pygame.K_DOWN,
            'rotate_cw': pygame.K_UP, 'rotate_ccw': pygame.K_z, 'hard_drop': pygame.K_SPACE, 'hold': pygame.K_c
        }
        
        self.settings_index = 0
        self.settings_options = ['Server IP', 'DAS (ms)', 'ARR (ms)', 'Infinite Soft Drop', 'Edit Keybinds', 'Back']
        self.keymap_index = 0
        self.binding_action = None
        
        self.info_lines = []
        self.info_scroll = 0
        self._load_info_text()
        
        self.key_timers, self.engine, self.visualizer, self.bot = {}, None, None, None
        self.auto_mode, self.last_bot_tick, self.connected, self.pending_start, self.running = False, 0, False, False, True

    def _update_fonts(self):
        # Scale fonts based on window height slightly or keep static
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 72)

    def _load_info_text(self):
        try:
            with open("MECHANICS.md", "r") as f:
                self.info_lines = [line.rstrip() for line in f.readlines()]
        except:
            self.info_lines = ["Could not load MECHANICS.md"]

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_input()
            self._update(dt)
            self._draw()
        if self.network: self.network.close()
        pygame.quit()

    def start_game(self, multiplayer=False):
        if self.pending_start or self.phase == GamePhase.PLAYING: return
        self.opponents, self.update_timer, self.last_beat_int, self.last_lines_cleared, self.connected = {}, 0, 0, 0, False
        if multiplayer and self.server_ip:
            self.pending_start = True
            player_id = f"Player_{random.randint(1000, 9999)}"
            self.network = NetworkClient(self.server_ip, 4242, player_id)
        else:
            self.pending_start, self.engine = False, TetrisEngine(bpm=128.0)
            self.bot, self.visualizer, self.phase = RogueBot(self.engine), BattleVisualizer(self.screen, self.font), GamePhase.PLAYING

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.VIDEORESIZE:
                if event.w != self.width or event.h != self.height:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self._update_fonts()
                    if self.visualizer:
                        self.visualizer = BattleVisualizer(self.screen, self.font)
            elif event.type == pygame.KEYDOWN:
                if self.phase == GamePhase.MENU: self._handle_menu_input(event.key)
                elif self.phase == GamePhase.SETTINGS: self._handle_settings_input(event)
                elif self.phase == GamePhase.KEYMAP: self._handle_keymap_input(event)
                elif self.phase == GamePhase.INFO: self._handle_info_input(event.key)
                elif self.phase == GamePhase.PLAYING: self._handle_game_keydown(event.key)
            elif event.type == pygame.KEYUP:
                if self.phase == GamePhase.PLAYING and event.key in self.key_timers: del self.key_timers[event.key]

    def _handle_menu_input(self, key):
        if key == pygame.K_1: self.start_game(multiplayer=False)
        elif key == pygame.K_2:
            if self.server_ip: self.start_game(multiplayer=True)
            else: self.phase = GamePhase.SETTINGS 
        elif key == pygame.K_3: self.phase = GamePhase.SETTINGS
        elif key == pygame.K_4: self.phase = GamePhase.INFO; self.info_scroll = 0
        elif key == pygame.K_a: self.auto_mode = not self.auto_mode
        elif key == pygame.K_r: self.bot_source = load_bot_script()
        elif key == pygame.K_ESCAPE: self.running = False
        self.key_timers = {}

    def _handle_settings_input(self, event):
        if event.type != pygame.KEYDOWN: return
        key = event.key
        if key == pygame.K_ESCAPE: self.phase = GamePhase.MENU; self.key_timers = {}; return
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
        elif opt == 'Edit Keybinds' and key == pygame.K_RETURN: self.phase = GamePhase.KEYMAP; self.keymap_index = 0
        elif opt == 'Back' and key == pygame.K_RETURN: self.phase = GamePhase.MENU; self.key_timers = {}

    def _handle_keymap_input(self, event):
        if self.binding_action:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE: self.keybinds[self.binding_action] = event.key
                self.binding_action = None
            return
        if event.type != pygame.KEYDOWN: return
        key, actions = event.key, list(self.keybinds.keys())
        if key == pygame.K_ESCAPE: self.phase = GamePhase.SETTINGS; return
        if key == pygame.K_UP: self.keymap_index = (self.keymap_index - 1) % (len(actions) + 1)
        elif key == pygame.K_DOWN: self.keymap_index = (self.keymap_index + 1) % (len(actions) + 1)
        elif key == pygame.K_RETURN:
            if self.keymap_index < len(actions): self.binding_action = actions[self.keymap_index]
            else: self.phase = GamePhase.SETTINGS

    def _handle_info_input(self, key):
        if key == pygame.K_ESCAPE or key == pygame.K_RETURN: self.phase = GamePhase.MENU
        elif key == pygame.K_UP: self.info_scroll = max(0, self.info_scroll - 1)
        elif key == pygame.K_DOWN: self.info_scroll = min(len(self.info_lines) - 25, self.info_scroll + 1)
        elif key == pygame.K_PAGEUP: self.info_scroll = max(0, self.info_scroll - 10)
        elif key == pygame.K_PAGEDOWN: self.info_scroll = min(len(self.info_lines) - 25, self.info_scroll + 10)

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
            elif key == pygame.K_ESCAPE: self.phase = GamePhase.MENU; (self.network.close() if self.network else None); self.network = None; self.key_timers = {}
            return
        if key == pygame.K_F5: self.bot_source = load_bot_script(); return
        action = None
        if key == self.keybinds['rotate_cw']: action = 'rotate_cw'
        elif key == self.keybinds['rotate_ccw']: action = 'rotate_ccw'
        elif key == self.keybinds['hard_drop']: action = 'hard_drop'
        elif key == self.keybinds['hold']: action = 'hold'
        elif key == pygame.K_ESCAPE: self.phase = GamePhase.MENU; (self.network.close() if self.network else None); self.network = None; self.key_timers = {}; return
        if action: self._play_action_sound(self.engine.submit_action(action))

    def _play_action_sound(self, result):
        if self.sound_manager:
            if result == 'moved': self.sound_manager.play('move')
            elif result in ['rotated', 'dropped', 'hold', 'clear']: self.sound_manager.play(result if result != 'hold' else 'move')

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
                        self.bot, self.visualizer, self.phase, self.pending_start = RogueBot(self.engine), BattleVisualizer(self.screen, self.font), GamePhase.PLAYING, False
                elif cmd == "opponent_update": self.opponents[msg.get("player_id")] = {"score": msg.get("score"), "grid": msg.get("grid")}
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
        if key == self.keybinds['move_left']:
            if self.arr_rate == 0:
                while self.engine.move(-1, 0): pass
            else: self.engine.submit_action('move_left')
        elif key == self.keybinds['move_right']:
            if self.arr_rate == 0:
                while self.engine.move(1, 0): pass
            else: self.engine.submit_action('move_right')
        elif key == self.keybinds['move_down']: self.engine.submit_action('move_down')

    def _draw(self):
        self.screen.fill((40, 40, 60))
        if self.phase == GamePhase.MENU: self._draw_menu()
        elif self.phase == GamePhase.SETTINGS: self._draw_settings()
        elif self.phase == GamePhase.KEYMAP: self._draw_keymap()
        elif self.phase == GamePhase.INFO: self._draw_info()
        elif self.phase == GamePhase.PLAYING:
            self.visualizer.draw(self.engine.state, opponents=self.opponents)
            if self.auto_mode:
                text = self.font.render("AUTO MODE", True, (255, 200, 0))
                self.screen.blit(text, (20, 20))
            if self.network:
                status_color = (0, 255, 0) if self.connected else (255, 100, 0)
                conn_text = self.font.render("ONLINE" if self.connected else "CONNECTING...", True, status_color)
                self.screen.blit(conn_text, (self.width - 150, 20))
        pygame.display.flip()

    def _draw_menu(self):
        cx, cy = self.width // 2, self.height // 2
        # Title at 20% height
        title = self.title_font.render("RHYTHM TETRIS", True, (0, 255, 255))
        self.screen.blit(title, title.get_rect(center=(cx, self.height * 0.15)))
        
        opts = ["Press [1] for Singleplayer", f"Press [2] for Multiplayer {'(Ready)' if self.server_ip else '(No IP)'}", 
                "Press [3] for Settings", "Press [4] for Detailed Info", 
                f"Press [A] to Toggle Bot {'(ON)' if self.auto_mode else '(OFF)'}", 
                "Press [R] to Reload Bot", "Press [ESC] to Quit"]
        
        start_y = self.height * 0.25
        for i, l in enumerate(opts):
            text = self.font.render(l, True, (200, 200, 200))
            self.screen.blit(text, text.get_rect(center=(cx, start_y + i * 50)))
            
        inst = ["MECHANICS: SRS Rotation, 7-Bag, Rhythmic Attacks", 
                "RHYTHM: Hit actions on the GREEN bar for Score/Attack bonuses!",
                "BOTS: Edit 'bot_script.rogue' and toggle with [A]!",
                "SETTINGS: Customize DAS/ARR/Keybinds in the Settings menu."]
        
        # Instructions at 75% height
        inst_y = self.height * 0.70
        for i, l in enumerate(inst):
            color = (100, 255, 100) if i == 1 else (150, 150, 150)
            text = self.small_font.render(l, True, color)
            self.screen.blit(text, text.get_rect(center=(cx, inst_y + i * 35)))

    def _draw_settings(self):
        cx, cy = self.width // 2, self.height // 2
        title = self.title_font.render("SETTINGS", True, (0, 255, 255))
        self.screen.blit(title, title.get_rect(center=(cx, self.height * 0.15)))
        
        start_y = self.height * 0.3
        for i, opt in enumerate(self.settings_options):
            color = (255, 255, 0) if i == self.settings_index else (200, 200, 200)
            val = {"Server IP": self.server_ip, "DAS (ms)": f"{int(self.das_delay*1000)}", 
                   "ARR (ms)": f"{int(self.arr_rate*1000)}", "Infinite Soft Drop": "ON" if self.soft_drop_infinite else "OFF", 
                   "Edit Keybinds": "", "Back": ""}.get(opt, "")
            text = self.font.render(f"{opt}: {val}", True, color)
            self.screen.blit(text, text.get_rect(center=(cx, start_y + i * 60)))

    def _draw_keymap(self):
        cx, cy = self.width // 2, self.height // 2
        title = self.title_font.render("KEYBIND EDITOR", True, (0, 255, 255))
        self.screen.blit(title, title.get_rect(center=(cx, self.height * 0.15)))
        
        actions = list(self.keybinds.keys()) + ["Back"]
        start_y = self.height * 0.25
        for i, act in enumerate(actions):
            color = (255, 255, 0) if i == self.keymap_index else (200, 200, 200)
            key_name = pygame.key.name(self.keybinds[act]).upper() if act in self.keybinds else ""
            text = self.font.render(f"{act.replace('_',' ').upper()}: {key_name}", True, color)
            self.screen.blit(text, text.get_rect(center=(cx, start_y + i * 50)))
            
        if self.binding_action:
            overlay = pygame.Surface((self.width, self.height)); overlay.set_alpha(180); overlay.fill((0,0,0)); self.screen.blit(overlay, (0,0))
            msg = self.font.render(f"PRESS ANY KEY FOR: {self.binding_action.replace('_',' ').upper()}", True, (255, 255, 255))
            self.screen.blit(msg, msg.get_rect(center=(cx, self.height // 2)))

    def _draw_info(self):
        cx = self.width // 2
        title = self.font.render("GAME MECHANICS (Scroll with Arrows/PgUp/PgDn)", True, (0, 255, 255))
        self.screen.blit(title, title.get_rect(center=(cx, 40)))
        
        y_start = 100
        visible_count = int((self.height - 200) / 25) # Dynamic count based on height
        for i in range(visible_count):
            idx = i + self.info_scroll
            if idx >= len(self.info_lines): break
            line = self.info_lines[idx]
            color = (255, 255, 255)
            fnt = self.font
            if line.startswith("# "): color = (0, 255, 255)
            elif line.startswith("## "): color = (255, 255, 0)
            else: fnt = self.small_font
            
            text = fnt.render(line, True, color)
            self.screen.blit(text, (60, y_start + i * 25))
            
        help_msg = self.small_font.render("Press ESC or ENTER to return", True, (150, 150, 150))
        self.screen.blit(help_msg, help_msg.get_rect(center=(cx, self.height - 40)))

if __name__ == "__main__":
    RogueDexTetrisClient().run()
