"""可调数值和字体（改游戏手感主要改这里）。"""
import os

import pygame

SCREEN_W, SCREEN_H = 960, 540
TITLE = "demo"

WORLD_W, WORLD_H = 3200, 2000
TILE_SIZE = 16
TILE_COLOR_A = (52, 58, 72)
TILE_COLOR_B = (40, 45, 58)
TILE_GRID_LINE = (28, 32, 42)

BG = (18, 20, 28)
UI_BG = (35, 38, 52)
TEXT = (230, 232, 240)
ACCENT = (180, 120, 255)
DANGER = (255, 90, 90)
XP_COLOR = (120, 220, 255)

PLAYER_SPEED = 220
PLAYER_RADIUS = 14
PLAYER_MAX_HP = 100
PLAYER_IFRAMES = 1.0

SPAWN_START_INTERVAL = 1.2
SPAWN_MIN_INTERVAL = 0.35
DIFFICULTY_RAMP = 0.985
BATCH_SIZE_START = 1
BATCH_GROW_EVERY = 25.0

GEM_VALUE = 8
MAGNET_BASE = 80
MAGNET_PER_LEVEL = 12


def xp_for_next_level(level):
    return int(28 + level * 16 + level * level * 2)


ORBIT_COUNT_START = 3
ORBIT_RADIUS = 72
ORBIT_SPEED = 2.2
ORBIT_DAMAGE = 12
ORBIT_HIT_COOLDOWN = 0.35

PROJECTILE_COOLDOWN = 0.9
PROJECTILE_SPEED = 380
PROJECTILE_DAMAGE = 18
PROJECTILE_RADIUS = 6


def get_font(size):
    # 不用 SysFont，避免个别 Windows 注册表字体导致崩溃
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
