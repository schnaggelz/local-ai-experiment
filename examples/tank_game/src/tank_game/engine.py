import pygame
from typing import List, Optional
from tank_game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_LEVEL, GRAVITY, 
    COLOR_BLACK, COLOR_GREEN, COLOR_RED, COLOR_YELLOW, COLOR_WHITE, MAX_POWER
)
from tank_game.entities import Tank, Projectile

class GameEngine:
    def __init__(self, player1: Tank, player2: Tank):
        self.player1 = player1
        self.player2 = player2
        self.players = [player1, player2]
        self.current_player_idx = 0
        self.projectiles: List[Projectile] = []
        self.is_running = True
        self.game_over = False
        self.winner: Optional[Tank] = None
        self.last_action_done = False

    @property
    def current_player(self) -> Tank:
        return self.players[self.current_player_idx]

    def handle_input(self, event: pygame.event.Event) -> None:
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # Reset logic would go here (simplified for now)
                pass
            return

        player = self.current_player
        
        # Controls depend on which player is active
        # Player 1: Arrows + Space, Player 2: WASD + Enter
        if self.current_player_idx == 0:
            keys = pygame.key.get_pressed()
            if not self.last_action_done:
                if keys[pygame.K_UP]: player.angle -= 1
                if keys[pygame.K_DOWN]: player.angle += 1
                if keys[pygame.K_RIGHT]: player.power = min(MAX_POWER, player.power + 0.5)
                if keys[pygame.K_LEFT]: player.power = max(0, player.power - 0.5)
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self._fire()
        else:
            keys = pygame.key.get_pressed()
            if not self.last_action_done:
                if keys[pygame.K_w]: player.angle -= 1
                if keys[pygame.K_s]: player.angle += 1
                if keys[pygame.K_d]: player.power = min(MAX_POWER, player.power + 0.5)
                if keys[pygame.K_a]: player.power = max(0, player.power - 0.5)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self._fire()

    def _fire(self) -> None:
        player = self.current_player
        if self.last_action_done:
            return
            
        rad = math.radians(player.angle)
        # Power scaled for physics
        speed = player.power * 0.15 
        vx = speed * math.cos(rad)
        vy = speed * math.sin(rad)
        
        tip_x, tip_y = player.get_cannon_tip()
        self.projectiles.append(Projectile(tip_x, tip_y, vx, vy, self.current_player_idx))
        
        player.power = 0 # Reset power after shot
        self.last_action_done = True

    def update(self) -> None:
        if self.game_over:
            return

        # Update projectiles
        for p in self.projectiles[:]:
            p.update_correct()
            
            # Hit ground
            if p.y >= GROUND_LEVEL:
                self.projectiles.remove(p)
                self._next_turn()
                continue
                
            # Hit players
            for player in self.players:
                if player.id != p.owner_id:
                    dist = ((p.x - player.x)**2 + (p.y - player.y)**2)**0.5
                    if dist < 20: # Collision radius
                        player.health -= 30
                        self.projectiles.remove(p)
                        if player.health <= 0:
                            self.game_over = True
                            self.winner = self.current_player if p.owner_id != player.id else None
                            # Wait, logic error: if shooter hits, shooter wins.
                            # Let's refine:
                            self.winner = self.players[p.owner_id]
                        else:
                            self._next_turn()
                        break

    def _next_turn(self) -> None:
        self.current_player_idx = 1 - self.current_player_idx
        self.last_action_done = False

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(COLOR_BLACK)
        
        # Draw Ground
        pygame.draw.rect(screen, COLOR_GREEN, (0, GROUND_LEVEL, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_LEVEL))
        
        # Draw Players
        for player in self.players:
            player.draw(screen)
            
        # Draw Projectiles
        for p in self.projectiles:
            pygame.draw.circle(screen, COLOR_YELLOW, (int(p.x), int(p.y)), int(p.radius))

        # UI - Power Meter
        active_player = self.current_player
        pygame.draw.rect(screen, (50, 50, 50), (20, 20, 104, 24))
        power_width = (active_player.power / MAX_POWER) * 104
        pygame.draw.rect(screen, COLOR_BLUE if active_player.id == 0 else COLOR_RED, 
                         (20, 20, int(power_width), 24))
        
        if self.game_over and self.winner:
            font = pygame.font.SysFont("Arial", 72)
            text = font.render(f"PLAYER {self.winner.id} WINS!", True, COLOR_WHITE)
            screen.blit(text, (SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT//2))

import math # Added missing import inside engine
