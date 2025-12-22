import pygame
from battledex_engine.state import BattleState

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
GRAY = (200, 200, 200)
HP_BG = (100, 100, 100)

class BattleVisualizer:
    def __init__(self, screen, font, combatant_map):
        self.screen = screen
        self.font = font
        self.combatant_map = combatant_map
        self.width, self.height = screen.get_size()
        
        # Positions for 1v1
        # Player (Left/Bottom)
        self.p1_pos = (150, 300)
        # Opponent (Right/Top)
        self.p2_pos = (450, 100)

    def draw(self, state: BattleState, logs: list = None):
        """
        Draws the current battle state.
        """
        self.screen.fill(WHITE)
        
        # We assume 2 teams, 1 active per team for now
        if len(state.teams) >= 2:
            team1 = state.teams[0]
            team2 = state.teams[1]
            
            self._draw_combatant(team1.active_combatant_id, self.p1_pos, is_player=True)
            self._draw_combatant(team2.active_combatant_id, self.p2_pos, is_player=False)
            
        # Draw Log/Message Box
        self._draw_logs(logs)

    def _draw_combatant(self, combatant_id: str, pos: tuple, is_player: bool):
        combatant = self.combatant_map.get(combatant_id)
        if not combatant:
            return

        x, y = pos
        
        # 1. Draw Sprite Placeholder
        rect_color = BLUE if is_player else RED
        rect_size = (100, 100)
        pygame.draw.rect(self.screen, rect_color, (*pos, *rect_size))
        
        # Label
        name_text = self.font.render(combatant.species_name, True, BLACK)
        self.screen.blit(name_text, (x, y - 30))
        
        # 2. Draw HP Bar
        # Calculate HP Percentage
        max_hp = combatant.stats.get("hp", 100)
        current_hp = combatant.current_hp
        hp_percent = max(0, min(1.0, current_hp / max_hp))
        
        bar_width = 120
        bar_height = 15
        bar_x = x - 10
        bar_y = y + 110
        
        # Background
        pygame.draw.rect(self.screen, HP_BG, (bar_x, bar_y, bar_width, bar_height))
        # Health
        hp_color = GREEN if hp_percent > 0.5 else (200, 200, 50) if hp_percent > 0.2 else RED
        pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, bar_width * hp_percent, bar_height))
        
        # Text HP
        hp_text = self.font.render(f"{current_hp}/{max_hp}", True, BLACK)
        self.screen.blit(hp_text, (bar_x + bar_width + 10, bar_y))

    def _draw_logs(self, logs):
        if not logs:
            return

        # Simple text box at bottom
        box_rect = (50, 450, 700, 130)
        pygame.draw.rect(self.screen, GRAY, box_rect)
        pygame.draw.rect(self.screen, BLACK, box_rect, 2)
        
        # Display last few log messages (assuming logs is a list of strings or Events)
        # We need to extract meaningful text from events or just use a message list passed in.
        
        y_offset = 460
        for log in logs[-4:]: # Show last 4 messages
            if hasattr(log, 'event_type'):
                # Basic formatting for events
                if log.event_type == "DAMAGE":
                    msg = f"Dealt {log.payload.get('damage')} damage!"
                elif log.event_type == "FAINT":
                    msg = "Fainted!"
                else:
                    msg = f"{log.event_type}: {log.payload}"
            else:
                msg = str(log)

            text = self.font.render(msg, True, BLACK)
            self.screen.blit(text, (60, y_offset))
            y_offset += 25