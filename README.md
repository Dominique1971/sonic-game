# 🦊 Kitsune Adventure

A complete 2D platformer game built with **Python** and **pygame** — no external assets required. All graphics are drawn with pygame primitives and all sounds are generated procedurally with numpy.

---

## 🎮 Game Overview

Play as **Kitsune**, a cute orange fox on a journey through 10 unique worlds. Run, jump, and shoot your way past enemies, collect power-ups, and reach the goal portal at the end of each level!

---

## ✨ Features

| Feature | Details |
|---|---|
| **10 Levels** | Green Meadow → Enchanted Forest → Desert Dunes → Twilight Valley → Ice Kingdom → Underwater Realm → Volcanic Wasteland → Sky Kingdom → Crystal Cavern → Final Fortress |
| **5 Enemy Types** | Slime, BushSpike, FlyingBat, ArmoredCrab, Boulder |
| **6 Weapons** | Normal, Spread, Bounce, Homing, Laser, Bomb |
| **4 Power-ups** | Gem (+50pts), Weapon Orb, Heart (+1 life), Shield (invincibility) |
| **Parallax Backgrounds** | Unique animated scenery per world theme |
| **Chiptune Music** | Procedurally generated melody loop per theme |
| **Sound Effects** | 13 procedurally generated SFX via numpy |
| **Particle Effects** | Hit sparks, explosions, collection bursts |
| **3 Lives** | Respawn on death, game over at 0 lives |

---

## 🛠️ Installation

### Requirements

- Python 3.8+
- pygame 2.x
- numpy

### Install dependencies

```bash
pip install pygame numpy
```

### Run the game

From the workspace root:

```bash
cd sonic-game
python main.py
```

You can also run the current file directly in VS Code or from the repo folder:

```bash
cd sonic-game
python game.py
```

If no audio device is available, the game now falls back to **silent mode** instead of crashing.

---

## 🕹️ Controls

| Key | Action |
|---|---|
| **← →** Arrow Keys | Move left / right |
| **↑** or **Space** | Jump (coyote time + jump buffer supported) |
| **Enter** | Shoot current weapon |
| **P** | Pause / Resume |
| **M** | Toggle music on/off |
| **ESC** | Return to main menu |

---

## 🔫 Weapons

Collect **Weapon Orbs** scattered through each level to unlock new weapons. Each weapon has limited ammo (except Normal which is infinite). When ammo runs out, it reverts to Normal.

| Weapon | Color | Description |
|---|---|---|
| **Normal** | Yellow | Fast straight bullet, infinite ammo |
| **Spread** | Cyan | Fires 3 bullets in a spread pattern, 20 ammo |
| **Bounce** | Green | Bounces off floors/platforms up to 3 times, 15 ammo |
| **Homing** | Purple | Steers toward nearest enemy, leaves particle trail, 10 ammo |
| **Laser** | Red | Instant hit raycast beam across the screen, 8 ammo |
| **Bomb** | Orange | Arc projectile, explodes in 70px radius, 6 ammo |

---

## 👾 Enemies

| Enemy | Hits | Points | Behaviour |
|---|---|---|---|
| **Slime** | 1 | 100 | Patrols left/right, squash-and-stretch animation |
| **BushSpike** | ∞ | 0 | Stationary obstacle — jump over it! |
| **FlyingBat** | 1 | 150 | Flies in sine-wave pattern |
| **ArmoredCrab** | 2 | 200 | Chases player, eye-stalk display |
| **Boulder** | 1 | 250 | Rolls toward player, rotates as it moves |

---

## 💎 Power-ups

| Item | Effect |
|---|---|
| **Gold Gem** ⭐ | +50 points, spinning star shape |
| **Weapon Orb** 🔮 | Gives new weapon + ammo refill, color-coded per weapon |
| **Heart** ❤️ | +1 life (max 3) |
| **Shield** 🛡️ | ~4 seconds of invincibility |

---

## 🗺️ Level Progression

Each level increases in difficulty:
- More enemies, faster enemy speed
- Longer levels with more platforms
- Harder enemy types introduced gradually
- Score carries over between levels

| Level | Name | Theme |
|---|---|---|
| 1 | Green Meadow | Rolling hills, clouds, bushes |
| 2 | Enchanted Forest | Dark trees, glowing fireflies |
| 3 | Desert Dunes | Pyramids, cacti, sand dunes |
| 4 | Twilight Valley | Purple sky, silhouette mountains |
| 5 | Ice Kingdom | Snowflakes, ice spikes, glaciers |
| 6 | Underwater Realm | Light rays, bubbles, coral, seaweed |
| 7 | Volcanic Wasteland | Lava glow, volcanic smoke, ash |
| 8 | Sky Kingdom | Floating islands, birds, fluffy clouds |
| 9 | Crystal Cavern | Stalactites, glowing crystals |
| 10 | Final Fortress | Gothic castle, bats, lightning flashes |

---

## 📁 File Structure

```
sonic-game/
├── main.py          # Entry point
├── game.py          # Main game loop, state machine, HUD
├── player.py        # Fox character: physics, animation, weapons
├── enemy.py         # 5 enemy types with AI
├── projectile.py    # 6 projectile types
├── powerup.py       # 4 pickup types
├── level.py         # Level generation and management
├── background.py    # Themed parallax backgrounds (10 themes)
├── sound.py         # Procedural sound/music generation (numpy)
├── constants.py     # Global constants and level definitions
└── README.md        # This file
```

---

## 🎨 Technical Notes

- **No external assets** — everything drawn with `pygame.draw` primitives
- **Procedural audio** — numpy generates int16 waveforms at 44100 Hz
- **World vs Screen coords** — `screen_x = world_x - camera_x` (camera smoothly follows player)
- **One-way platforms** — land on top, pass through from below
- **Coyote time** — 6-frame grace period after walking off a ledge
- **Jump buffering** — jump input buffered for 8 frames before landing

---

## 🏆 Scoring

- Defeat Slime: **100 pts**
- Defeat FlyingBat: **150 pts**
- Defeat ArmoredCrab: **200 pts**
- Defeat Boulder: **250 pts**
- Collect Gem: **50 pts**
- Score carries across all 10 levels

---

## 📜 License

This project is open source. Enjoy and modify freely!
