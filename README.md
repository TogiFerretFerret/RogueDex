# RogueDex: Rhythm Tetris

Welcome to **Rhythm Tetris**, a competitive Tetris clone that rewards rhythm game precision. Built from the ground up with a custom networking stack, scripting language, and game engine.

## 🚀 Features

- **Standard Competitive Tetris**: Implementation of the Super Rotation System (SRS), 7-bag randomizer, Hold piece, and Next queue.
- **Rhythm Mechanics**: Timing your moves to the beat grants significant scoring and attack bonuses.
- **Multiplayer Battle**: Custom UDP networking stack (**picoNet**) allows for real-time garbage sending and board syncing.
- **Custom Bot Scripting**: Write your own Tetris AI using **RogueScript**, a custom bytecode-interpreted language.
- **High-Level Customization**: Adjustable DAS, ARR (including 0 ARR instant snap), and dynamic keybindings.

## 🛠️ Modules

- `picoNet`: A custom low-level UDP networking stack for high-performance game sync.
- `battledex_engine`: The core Tetris logic, including the SRS implementation and the RogueScript VM.
- `roguedex_client`: The Pygame-based graphical client and sound manager.

## 🚦 Getting Started

1. **Install Dependencies**:
   ```bash
   uv add pygame numpy
   ```

2. **Run Singleplayer**:
   ```bash
   ./run_client.sh
   ```

3. **Run Multiplayer**:
   - Start the server: `./run_server.sh`
   - Start the client: `./run_client.sh 127.0.0.1`

## 📖 Documentation

Detailed mechanics, including SRS kick tables and RogueScript API, can be found in [MECHANICS.md](./MECHANICS.md).