
import os

import pygame


VIEW_W, VIEW_H = 960, 540
# Keep screen size and render scale consistent to avoid viewport clipping.
SCREEN_W, SCREEN_H = 1280, 720
DISPLAY_SCALE = min(SCREEN_W / VIEW_W, SCREEN_H / VIEW_H)
TITLE = "demo"

FPS = 60
WORLD_W, WORLD_H = 1024, 559
TILE_SIZE = 16
TILE_COLOR_A = (52, 58, 72)
TILE_COLOR_B = (40, 45, 58)
TILE_GRID_LINE = (28, 32, 42)

# COLORS FOR THE GAME

UI_BG = (35, 38, 52)
TEXT = (230, 232, 240)
ACCENT = (180, 120, 255)
DANGER = (255, 90, 90)
XP_COLOR = (120, 220, 255)

#PLAYER CONFIG:

PLAYER_SPEED = 220
PLAYER_RADIUS = 14
PLAYER_MAX_HP = 100
PLAYER_IFRAMES = 1.0

#ENEMY CONFIG:

SPAWN_START_INTERVAL = 2.2
SPAWN_MIN_INTERVAL = 0.35
DIFFICULTY_RAMP = 0.994
BATCH_SIZE_START = 1
BATCH_GROW_EVERY = 25.0

#GEM CONFIG:

GEM_VALUE = 8
MAGNET_BASE = 80
MAGNET_PER_LEVEL = 12


def xp_for_next_level(level):
    return int(28 + level * 16 + level * level * 2)


#ORBIT CONFIG:
ORBIT_COUNT_START = 4
ORBIT_RADIUS = 70
ORBIT_SPEED = 3.0
ORBIT_DAMAGE = 15
ORBIT_HIT_COOLDOWN = 0.2

#BULLET CONFIG:

PROJECTILE_COOLDOWN = 0.4
PROJECTILE_SPEED = 380
PROJECTILE_DAMAGE = 25
PROJECTILE_RADIUS = 7.5


def get_font(size):
    if os.name == "nt":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        for fname in ("msyh.ttc", "simhei.ttf", "simsun.ttc"):
            path = os.path.join(windir, "Fonts", fname)
            if os.path.isfile(path):
                try:
                    return pygame.font.Font(path, size)
                except OSError:
                    pass
    return pygame.font.Font(None, size)
