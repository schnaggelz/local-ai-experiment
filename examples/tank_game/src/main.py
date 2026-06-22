import pygame
import sys
from tank_game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GROUND_LEVEL, COLOR_BLUE, COLOR_RED
from tank_game.entities import Tank
from tank_game.engine import GameEngine

def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Artillery Tank Battle")
    clock = pygame.time.Clock()
    
    p1 = Tank(id=1, x=100, y=GROUND_LEVEL - 15, health=100, color=COLOR_BLUE)
    p2 = Tank(id=2, x=SCREEN_WIDTH - 100, y=GROUND_LEVEL - 15, health=100, color=COLOR_RED)
    
    engine = GameEngine(p1, p2)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                engine.handle_input(event)
        
        engine.update()
        engine.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
