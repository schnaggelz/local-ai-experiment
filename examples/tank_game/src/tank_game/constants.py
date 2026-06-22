from typing import Final

# Screen dimensions
SCREEN_WIDTH: Final[int] = 1024
SCREEN_HEIGHT: Final[int] = 768
GROUND_LEVEL: Final[int] = 650

# Physics
GRAVITY: Final[float] = 0.25
FPS: Final[int] = 60

# Colors
COLOR_BLACK: Final[tuple[int, int, int]] = (0, 0, 0)
COLOR_WHITE: Final[tuple[int, int, int]] = (255, 255, 255)
COLOR_GREEN: Final[tuple[int, int, int]] = (34, 139, 34)
COLOR_RED: Final[tuple[int, int, int]] = (220, 20, 60)
COLOR_BLUE: Final[tuple[int, int, int]] = (30, 144, 255)
COLOR_YELLOW: Final[tuple[int, int, int]] = (255, 215, 0)

# Gameplay
TANK_RADIUS: Final[int] = 15
CANNON_LENGTH: Final[float] = 30.0
MAX_POWER: Final[float] = 100.0
