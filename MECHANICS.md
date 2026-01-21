# RogueDex: Game Mechanics

This document provides a detailed breakdown of the internal systems governing Rhythm Tetris.

---

## 🎵 Rhythm System

The defining feature of RogueDex. The game tracks a global BPM (default 128) and defines a "Beat Window".

- **The Window**: A ±0.2s window around each beat.
- **Visual Feedback**: A rhythm bar at the bottom pulses green when you are "on-beat".
- **Score Bonus**: Any action (Move, Rotate, Hold) performed on the beat grants bonus points.
- **Attack Bonus**: Line clears performed on the beat add **+1 Garbage Line** to the attack.
- **Rhythmic Sending**: Buffered attacks are only sent to opponents exactly on the beat, emphasizing the "Battle" rhythm.

---

## 🧩 Tetris Engine (SRS)

RogueDex uses the **Super Rotation System (SRS)** standard found in modern competitive Tetris.

- **7-Bag Randomizer**: Ensures you get exactly one of each of the 7 pieces every 7 spawns, preventing long droughts.
- **Wall Kicks**: Standard J, L, S, T, Z and I piece kick tables are implemented. This allows for advanced maneuvers like T-Spins and S/Z-Spins.
- **Buffer Zone**: 20 hidden rows exist above the visible 20-row grid. 
- **Top-out Rules**: Game over occurs if a piece locks entirely above the visible area or if a spawn collision occurs.

---

## 🤖 RogueScript Botting

You can automate your gameplay by editing `bot_script.rogue`. The script is interpreted as bytecode every beat when Auto-Mode is enabled.

### Available Native Functions:
- `move_left()` / `move_right()` / `move_down()`
- `rotate_cw()` / `rotate_ccw()`
- `hard_drop()`
- `hold()`
- `get_piece_x()`: Returns current column (0-9).
- `get_piece_y()`: Returns current row (0-39).
- `get_piece_shape()`: Returns shape ID ('I', 'T', etc.).
- `is_occupied(x, y)`: Returns true if a block exists at coordinates.

### Sample Script:
```js
var x = get_piece_x();
if (x < 4) { move_right(); }
if (x > 4) { move_left(); }
hard_drop();
```

---

## 🎮 Input Handling

Competitive Tetris requires precise input. We support:

- **DAS (Delayed Auto Shift)**: The initial delay before a held key starts repeating.
- **ARR (Auto Repeat Rate)**: The speed at which movement repeats while held.
- **0 ARR (Instant Snap)**: Setting ARR to 0 enables "Instant Snap" behavior, where the piece immediately hits the wall after the DAS delay.
- **Infinite Soft Drop**: A toggle that makes the "Soft Drop" key behave like a manual hard-drop without locking.

---

## 🌐 Multiplayer (picoNet)

The networking is handled by `picoNet`, a custom UDP implementation.

- **Deterministic Seeds**: The server generates a `match_seed` upon connection, ensuring both players get the exact same sequence of pieces.
- **Board Syncing**: Your opponent's board is rendered in real-time on your screen (mini-view).
- **Garbage System**: Clearing lines sends "Gray" lines to your opponent. These lines have a single hole at a random position.
