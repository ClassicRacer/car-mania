# Car Mania

A top-down racing game built with **Python** and **pygame**. Choose your car, race through gate-ordered tracks, and complete laps to win!

Car Mania started as a high-school project in 2020. This repository contains a complete rewrite of the original that adopts an object-oriented design and adds a wide range of features. More features are planned.

## Features
- **Car Select:** database-backed car stats, normalized comparison bars, rotatable previews.  
- **Level Select:** database-backed levels, generated thumbnails, cinematic camera tour, transition to gameplay.  
- **Racing Rules:** Gate-ordered laps, global race timer, finish banner.  
- **Collision:** Sliding, bounce, and “unstick” nudges vs. walls/trees/gates.  
- **Level Codes:** Compact strings that assemble roads, gates, and trees, with support for procedural maze generation.

## Installation

### Requirements
- Python **3.10+**
- Pygame **2.5+**

### Quick Start

#### macOS / Linux

```console
git clone https://github.com/ClassicRacer/car-mania.git
cd car-mania
python -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### Windows

```console
git clone https://github.com/ClassicRacer/car-mania.git
cd car-mania
python -m venv .venv && source .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Run
From the project root:
```bash
python run.py
```

## Controls

- **W / Up Arrow** – Accelerate  
- **S / Down Arrow** – Reverse  
- **A / Left Arrow** – Steer left  
- **D / Right Arrow** – Steer right  
- **Space** – Brake  
- **Escape** – Pause / Back

## Menu Flow

1. **Main Menu** – Play / Credits
2. **Car Select** – Pick a car (retrieved from DB)
3. **Level Select** – Browse levels, tour, then start
4. **Gameplay** – Drive through active gates to complete laps and win
5. **Pause Menu** – Resume or Quit to Menu

## Data & Assets

- **Images & Fonts**: `game/assets/images/`, `game/assets/fonts/`
- **Database**: `data/carmania.db` (queried via `game/data/queries.py`)

> **Note:** Run from the **repo root** so relative asset paths resolve correctly.

## Credits
- **Programming & Game Design:** Harish Menon
- **Art & Assets:** Assets, cars, and level design derived from original release
- **Technology:** Built with Python and pygame
- **Fonts & Icons:** Bundled typefaces in `game/assets/fonts/`, with notices in `licenses/fonts/`
- **Version:** v2.0.0-alpha.1
- **Planned Features:** AI opponents, Sound effects, background music, configurable options, car/level creator, improved assets, adjustable views

## License
- Bundled fonts (Orbitron, Nunito, DejaVu, Noto Sans Symbols 2) are provided under the SIL Open Font License. See files under `licenses/fonts/`.
- No repository-wide source license is included; retain the existing structure and asset notices when redistributing.
