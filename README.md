# Software-engineering-project-demo
---

## Graphical Abstract

---

## Purpose of the Software
### 1. Applied Software Development Process
This project adopts **Agile Scrum iterative development methodology** for the full lifecycle of software development.

### 2. Rationale for Choosing This Model (Waterfall vs. Agile) 
We selected the Agile Scrum model over the traditional Waterfall model for this game development project, with a direct comparison and core rationale as follows: 
| Evaluation Dimension | Agile Scrum (Selected Model) | Traditional Waterfall Model | 
|----------------------|--------------------------------|------------------------------|
 | Development Flexibility | Supports iterative adjustment of gameplay mechanics, numerical balance, and user experience based on real-time testing feedback, which is critical for game development where gameplay feel needs continuous optimization | Follows a strict linear, phase-locked workflow, requiring all requirements to be fully defined and frozen at the start of the project, with no room for flexible adjustment once development begins |
| Risk Management | Risks are identified and resolved at the end of each 1-week sprint, with continuous testing and bug fixing throughout the development cycle, minimizing the impact of technical and design risks | All risks are concentrated in the final testing phase; if core gameplay or functional issues are found at this stage, the cost of modification is extremely high, and may require full rework of multiple previous phases | 
| Delivery Capability | Delivers a runnable game version at the end of each sprint, ensuring we always have a functional demo aligned with the project's pilot-level requirement | Only delivers a runnable product at the very end of the full development cycle, with no way to validate core gameplay and functionality until the final phase | 
| Team Collaboration Efficiency | Enables continuous communication and clear division of labor within the small team, with each member contributing to every sprint, and regular review sessions to align progress and adjust priorities | Separates development into siloed phases (requirements → design → development → testing → delivery), with limited cross-phase collaboration, and high communication costs for any requirement or design changes | 

### 3. Target Market & Application Scenarios
- **Core Target Users**: Casual game players, indie game enthusiasts, and beginners of Python/Pygame game development
- **Entertainment Usage**: Provides a lightweight, low-threshold survival action game experience for casual players, with a smooth combat loop and progressive difficulty design
- **Stress Relief & Leisure Gaming Usage**: Offers fast-paced, engaging, and easy-to-access gameplay that helps users relieve daily stress, refresh their minds, and enjoy a lightweight immersive gaming experience in free time.
- **Secondary Development Usage**: Provides an open-source basic game framework, which can be extended with more gameplay, art resources, and functional modules by secondary developers

---

## Software Development Plan
### 1. Detailed Development Process
The project follows the Agile Scrum framework, divided into 4 sprints (1 week per sprint), with clear deliverables for each sprint, and a test & review session at the end of each sprint to adjust the development plan in time.
1. **Sprint 1 (Week 1: Requirement & Framework Setup)**
   - Complete requirement analysis, technical selection, and project architecture design
   - Build the basic game window, map rendering system, and player movement control module
   - Deliverable: Runnable basic game framework with normal player movement and map display
2. **Sprint 2 (Week 2: Core Gameplay Development)**
   - Develop enemy AI tracking system, dynamic enemy spawn mechanism, and circular collision detection algorithm
   - Complete player health system, damage calculation, and experience gem collection logic
   - Deliverable: Runnable game version with complete basic combat and survival loop
3. **Sprint 3 (Week 3: Advanced System & UI Development)**
   - Develop orbit blade weapon system, homing missile system, and player level-up upgrade system
   - Complete dynamic difficulty adjustment algorithm, in-game UI interface, pause menu, and background music system
   - Deliverable: Full playable game version with complete game systems
4. **Sprint 4 (Week 4: Testing & Final Delivery)**
   - Complete full functional testing, compatibility testing, bug fixing, and numerical balance optimization
   - Write project documentation, record demo video, and sort out the final delivery materials
   - Deliverable: Final stable release version of the game, complete documentation and demo materials

### 2. Team Members (Roles & Responsibilities & Contribution Portion)
| Member | Role | Core Responsibilities | Contribution |
|--------|------|----------------------|--------------|
| NG KA HANG  | **Project Manager & Lead Developer** | Overall project planning, architecture design, core game system development, final code integration, and progress supervision | 20% |
| WAN ZIXUAN | **Gameplay Programmer** | Player control system, combat mechanics, enemy AI, collision detection, and core gameplay logic implementation | 20% |
| HUANG YUMO| **UI & System Developer** | In-game UI design, menu system, upgrade system, audio integration, and visual effect implementation | 20% | 
| WONG CHON SENG | **Test Engineer & Debug Specialist** | Full functional testing, bug detection & fixing, performance optimization, compatibility verification | 20% |
| NG CHI HOU | **Document & Media Specialist** | README documentation, project report writing, demo video production, asset management, and final submission | 20% |

### 3. Project Schedule
| Phase | Time Range | Core Milestones |
|-------|------------|------------------|
| Preparation Phase | Day 1-2 | Requirement confirmation, technical selection, team role division |
| Sprint 1 | Day 3-9 | Basic game framework completed, player movement and map rendering function online |
| Sprint 2 | Day 10-16 | Core combat system completed, enemy spawn and collision detection function online |
| Sprint 3 | Day 17-23 | Full game system completed, upgrade system and UI interface online |
| Sprint 4 | Day 24-30 | Testing and optimization completed, final documentation and demo video delivered |
| Final Submission | Day 30 | Full project materials submitted via Canvas and GitHub |

### 4. Core Algorithm Implementation
1. Main Game Loop Algorithm
Goal: keep the game responsive by processing input, updating states, and rendering frames continuously.
Input: keyboard/mouse events and frame delta time dt.
Output: updated game state and rendered screen.
Process:
- Read input events of the current frame;
- Handle input by state (menu, playing, paused, level-up, game-over);
- Update player, enemies, projectiles, gems, and progression states;
- Draw map, characters, enemies, UI, and overlays;
- Flip display and continue to the next frame.

2. Enemy Spawning and Difficulty Scaling Algorithm
Goal: maintain pacing and gradually increase challenge.
Method:
- Spawn enemies around the player at random angle/distance (not directly on player);
- Randomly select among three enemy types (normal, fast, heavy);
- Scale enemy stats (HP, speed, damage) with wave/time;
- Decrease spawn interval over time and increase spawn batch size.
Result: easy early phase, progressively challenging late phase.

3. Collision Detection Algorithm (Circle-Based)
Goal: detect interactions among player, enemies, projectiles, and gems.
Rule:
(ax - bx)^2 + (ay - by)^2 <= (ar + br)^2
where (ax, ay), ar and (bx, by), br are centers and radii of two circles.
Used for:
- projectile hits enemy;
- enemy touches player;
- player collects experience gems.

4. Homing Projectile Algorithm
Goal: automatically attack the nearest enemy.
Process:
- Check cooldown;
- Select the nearest living enemy;
- Compute normalized direction vector toward target;
- Spawn projectile and apply level-based cooldown/speed/damage scaling.
Benefit: simple implementation with clear gameplay feedback.

### 5. Current Status of the Software
The project has completed all core function development, reached the **pilot level demo version** required by the project, and meets all the functional requirements of the course.
- All core game modules are fully developed and can run stably, including player control, enemy system, combat system, upgrade system, and UI interface
- The software has passed full functional testing and compatibility testing, no fatal bugs, and all functions are consistent with the demo content
- The software has basic cross-platform compatibility, supporting Windows, macOS and Linux operating systems

### 6. Future Plan
1. **Gameplay Expansion**: Add more enemy types, boss battles, more weapons and upgrade options, scene interactive elements, and prop system
2. **Art & Audio Optimization**: Replace higher-quality art resources, add character animation, special effect system, more background music and sound effects
3. **New Function Development**: Add save system, leaderboard, achievement system, multiple difficulty options, and custom character function
4. **Performance Optimization**: Optimize the performance of large-scale enemy spawn, adapt to more resolutions, and complete mobile porting
5. **Open Source & Community**: Improve open source documentation, support mod development, and provide more detailed secondary development tutorials

---

## Additional Components
### Demo Video (Youtube URL)
Full gameplay demo video: https://www.youtube.com/watch?v=Q0K1vT_whgI

### Software Development & Running Environment
#### Basic Information
- **Programming Language**: Python 3.8 or higher
- **Core Dependent Package**: pygame >= 2.5.0

#### Minimum Hardware Requirements
- Processor: 1.0GHz or higher dual-core CPU
- Memory: 512MB RAM or higher
- Graphics Card: Integrated or discrete graphics card supporting OpenGL 2.0
- Storage: 50MB available storage space

#### Minimum Software Requirements
- Operating System: Windows 7 or higher / macOS 10.15 or higher / Linux (Ubuntu 18.04+, Debian 10+)
- Runtime Environment: Python 3.8+, pip package manager

#### Installation & Running Guide
1) Open CMD / PowerShell / Git Bash
2) Go to the project folder (the folder that contains main.py):
   cd <your-project-folder>
   Example:
   cd Desktop/demo
   or
   cd C:\path\to\your\project
3) Install required package (first time only):
    python -m pip install "pygame>=2.5.0"
4) Start the game:
   python main.py

### Declaration
1. This project uses the open-source third-party library **Pygame (https://www.pygame.org/)**, which is licensed under the LGPL license. It is used for core functions such as game graphics rendering, audio playback, and input event processing. This content is not independently developed by our team, and we hereby declare it.
2. The font resources used in this project: Microsoft Yahei (msyh.ttc), SimHei (simhei.ttf), SimSun (simsun.ttc) built into the Windows system are system built-in fonts, not independently developed by our team, and we hereby declare them.
3. All core game logic codes (including `config.py`, `game.py`, `main.py`) in this project are independently developed by the team, without any other undeclared open-source code references.
