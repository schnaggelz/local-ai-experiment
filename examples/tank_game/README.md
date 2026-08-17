# Tank Artillery Game

A physics-based 2D artillery game built with Pygame where two players control tanks on opposite sides of the screen, adjusting cannon angles and power to hit each other while accounting for gravity.

##  Controls

### Player 1 (Red Tank)
- **Up Arrow**: Increase cannon angle
- **Down Arrow**: Decrease cannon angle  
- **Right Arrow**: Increase power
- **Left Arrow**: Decrease power
- **Space**: Fire shot

### Player 2 (Blue Tank)
- **W**: Increase cannon angle
- **S**: Decrease cannon angle
- **D**: Increase power
- **A**: Decrease power
- **Enter**: Fire shot

##  Game Features

- Turn-based combat between two players
- Physics engine with gravity affecting projectile trajectory
- Health system for tanks
- Power meter visualization
- Win condition when opponent's tank health reaches zero

##  Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the game:
   ```bash
   python main.py
   ```

3. Press 'R' to restart after a game ends

##  Game Plan Implementation Status

This implementation follows the development roadmap:

### Phase 1: Engine Foundation & Basic Physics
-  Initialize Pygame window and game loop
-  Implement gravity constant and basic projectile motion logic
-  Create static "ground" boundary

### Phase 2: Tank & Control Implementation
-  Tank class with position, rotation, and health
-  Input handling for both players
-  Power meter UI element

### Phase 3: Collision & Game Logic
-  Collision detection for ground and tanks
-  Turn management system
-  Health system with damage calculation

### Phase 4: Visuals & Polish
-  Basic tank sprites and visual elements
-  Health bars
-  Win/Loss screen and reset functionality