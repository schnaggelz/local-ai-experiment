# Artillery Game Plan

A physics-based 2D artillery game built with `pygame`. Two players control tanks on opposite sides of the screen, adjusting cannon angles and power to hit each other while accounting for gravity.

## 🎯 Core Gameplay Mechanics
- **Turn-Based Combat**: Players take turns aiming and firing.
- **Physics Engine**: Projectiles follow a parabolic trajectory influenced by gravity.
- **Aiming System**: Adjustable cannon angle (pipe) and variable shot power.
- **Win Condition**: Reduce the opponent's health to zero or land a direct hit that destroys their tank.

## 🛠 Technical Stack
- **Language**: Python 3.x
- **Library**: `pygame` (for rendering, input handling, and physics loops)

## 📋 Development Roadmap

### Phase 1: Engine Foundation & Basic Physics
- [ ] Initialize Pygame window and game loop.
- [ ] Implement gravity constant and basic projectile motion logic.
- [ ] Create a static "ground" boundary.

### Phase 2: Tank & Control Implementation
- [ ] **Tank Class**: Implement position, rotation (angle), and health.
- [ ] **Input Handling**: 
    - Player 1: Arrow keys (angle) + Space (power/fire).
    - Player 2: WASD (angle) + Enter (power/fire).
- [ ] **Power Meter**: Implement a visual UI element showing current shot power.

### Phase 3: Collision & Game Logic
- [ ] **Collision Detection**: Detect when a projectile hits the ground or a player tank.
- [ ] **Turn Management**: Implement a state machine to switch turns between players after a shot lands.
- [ ] **Health System**: Subtract health upon successful hits.

### Phase 4: Visuals & Polish
- [ ] Add explosion effects using particle systems.
- [ ] Enhance graphics (tank sprites, better ground textures).
- [ ] Implement a Win/Loss screen and Reset functionality.

## 🚀 Getting Started
1. Clone the repository.
2. Install dependencies: `pip install pygame`.
3. Run the game: `python examples/tank_game/main.py`.