import math
import pygame
from dataclasses import dataclass, field
from typing import Optional
from tank_game.constants import (
    TANK_RADIUS, CANNON_LENGTH, GRAVITY, COLOR_BLUE, COLOR_RED, COLOR_YELLOW
)

@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    owner_id: int
    radius: float = 5.0

    def update(self) -> None:
        """Updates the projectile position based on velocity and gravity."""
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

@dataclass
class Tank:
    id: int
    x: float
    y: float
    health: float
    color: tuple[int, int, int]
    angle: float = -45.0  # degrees, 0 is horizontal, -90 is vertical
    power: float = 50.0
    
    def draw(self, surface: pygame.Surface) -> None:
        # Draw tank body
        pygame_color = pygame.Color(self.color)
        pygame.draw.circle(surface, pygame_color, (int(self.x), int(self.y)), TANK_RADIUS)
        
        # Calculate cannon end point
        rad = math.radians(self.angle)
        end_x = self.x + CANNON_LENGTH * math.cos(rad)
        end_y = self.y + CANNON_LENGTH * math.sin(rad)
        
        # Draw cannon
        pygame.draw.line(surface, (50, 50, 50), (self.x, self.y), (end_x, end_y), 5)

    def get_cannon_tip(self) -> tuple[float, float]:
        rad = math.radians(self.angle)
        return (
            self.x + CANNON_LENGTH * math.cos(rad),
            self.y + CANNON_LENGTH * math.sin(rad)
        )
