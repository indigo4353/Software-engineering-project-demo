# Main game logic and objects.
import math
import random
from pathlib import Path

import pygame
import config


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def circles_hit(ax, ay, ar, bx, by, br):
    return (ax - bx) ** 2 + (ay - by) ** 2 <= (ar + br) ** 2


def camera_xy(px, py):
    vw, vh = config.VIEW_W, config.VIEW_H
    cx = max(0, min(px - vw / 2, config.WORLD_W - vw))
    cy = max(0, min(py - vh / 2, config.WORLD_H - vh))
    return int(cx), int(cy)


def to_screen(wx, wy, cam_x, cam_y):
    s = config.DISPLAY_SCALE
    return int((wx - cam_x) * s), int((wy - cam_y) * s)


def sr(r):
    return max(1, int(r * config.DISPLAY_SCALE))


def load_tex(folder, name, size_px):
    path = folder / name
    if not path.is_file():
        return None
    try:
        img = pygame.image.load(str(path)).convert_alpha()
        s = max(4, int(size_px))
        if img.get_size() != (s, s):
            img = pygame.transform.scale(img, (s, s))
        return img
    except pygame.error:
        return None


def blit_rot_center(dst, image, center_xy, angle_rad, tangent_offset=0.0):
    if image is None:
        return
    deg = -math.degrees(angle_rad + math.pi / 2 + tangent_offset)
    rot = pygame.transform.rotate(image, deg)
    dst.blit(rot, rot.get_rect(center=center_xy))


def overlay(surf, w, h, rgba):
    o = pygame.Surface((w, h), pygame.SRCALPHA)
    o.fill(rgba)
    surf.blit(o, (0, 0))


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.max_hp = config.PLAYER_MAX_HP
        self.hp = self.max_hp
        self.speed = config.PLAYER_SPEED
        self.radius = config.PLAYER_RADIUS
        self.level = 1
        self.xp_into_level = 0
        self.magnet = config.MAGNET_BASE
        self.damage_mult = 1.0
        self.iframes = 0.0

    def update(self, dt, keys, bounds):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if dx and dy:
            k = 1 / math.sqrt(2)
            dx *= k
            dy *= k
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
        self.x = max(bounds.left + self.radius, min(bounds.right - self.radius, self.x))
        self.y = max(bounds.top + self.radius, min(bounds.bottom - self.radius, self.y))
        if self.iframes > 0:
            self.iframes = max(0, self.iframes - dt)

    def take_damage(self, amount):
        if self.iframes > 0:
            return
        self.hp -= amount
        self.iframes = config.PLAYER_IFRAMES

    def alive(self):
        return self.hp > 0

    def add_xp(self, n):
        gained = 0
        self.xp_into_level += n
        while True:
            need = config.xp_for_next_level(self.level)
            if self.xp_into_level < need:
                break
            self.xp_into_level -= need
            self.level += 1
            gained += 1
            self.hp = min(self.max_hp, self.hp + self.max_hp * 0.15)
            self.magnet = config.MAGNET_BASE + config.MAGNET_PER_LEVEL * max(0, self.level - 1)
        return gained


ENEMY_COLOR = {"grunt": (200, 90, 90), "runner": (230, 160, 80), "brute": (140, 80, 200)}


class Enemy:
    def __init__(self, x, y, kind, hp, speed, radius, damage):
        self.x = x
        self.y = y
        self.kind = kind
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.radius = radius
        self.damage = damage
        self.touch_cooldown = 0.0
        self.alive = True

    def update(self, dt, px, py):
        d = dist(self.x, self.y, px, py) or 1
        self.x += (px - self.x) / d * self.speed * dt
        self.y += (py - self.y) / d * self.speed * dt
        if self.touch_cooldown > 0:
            self.touch_cooldown -= dt

    def hit(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False


def spawn_enemy(px, py, wave):
    ang = random.uniform(0, 2 * math.pi)
    d0 = max(config.VIEW_W, config.VIEW_H) * 0.52 + random.uniform(50, 220)
    x = max(24, min(config.WORLD_W - 24, px + math.cos(ang) * d0))
    y = max(24, min(config.WORLD_H - 24, py + math.sin(ang) * d0))
    r = random.random()
    scale = 1.0 + min(2.0, wave / 120.0)
    if r < 0.62:
        return Enemy(x, y, "grunt", 22 * scale, 68 + wave * 0.35, 12, 8 + wave * 0.08)
    if r < 0.88:
        return Enemy(x, y, "runner", 14 * scale, 105 + wave * 0.45, 9, 6 + wave * 0.06)
    return Enemy(x, y, "brute", 55 * scale, 48 + wave * 0.2, 18, 14 + wave * 0.1)


class Gem:
    def __init__(self, x, y, value=None):
        self.x = x
        self.y = y
        self.value = value if value is not None else config.GEM_VALUE
        self.radius = 5
        self.collected = False

    def update(self, dt, px, py, magnet):
        d = dist(self.x, self.y, px, py)
        if d < magnet and d > 1:
            pull = min(420, 180 + (magnet - d) * 3)
            self.x += (px - self.x) / d * pull * dt
            self.y += (py - self.y) / d * pull * dt


class Projectile:
    def __init__(self, x, y, vx, vy, damage):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.radius = config.PROJECTILE_RADIUS
        self.life = 2.2

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt


class OrbitBlades:
    def __init__(self, count, level=1):
        self.count = count
        self.level = level
        self.angle = 0.0
        self.hit_cd = {}

    def blade_damage(self):
        return config.ORBIT_DAMAGE * (1 + 0.12 * (self.level - 1))

    def update(self, dt):
        self.angle += config.ORBIT_SPEED * (1 + 0.03 * (self.level - 1)) * dt
        for k in list(self.hit_cd):
            self.hit_cd[k] -= dt
            if self.hit_cd[k] <= 0:
                del self.hit_cd[k]

    def blade_positions(self, px, py):
        n = max(1, self.count)
        r = config.ORBIT_RADIUS
        return [
            (px + math.cos(self.angle + 2 * math.pi * i / n) * r,
             py + math.sin(self.angle + 2 * math.pi * i / n) * r,
             10.0,
             self.angle + 2 * math.pi * i / n)
            for i in range(self.count)
        ]


class HomingMissiles:
    def __init__(self, level=1):
        self.level = level
        self.cooldown = 0.0

    def bolt_damage(self):
        return config.PROJECTILE_DAMAGE * (1 + 0.1 * (self.level - 1))

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt

    def try_fire(self, px, py, enemies):
        if self.cooldown > 0:
            return None
        living = [e for e in enemies if e.alive]
        if not living:
            return None
        t = min(living, key=lambda e: (e.x - px) ** 2 + (e.y - py) ** 2)
        dx, dy = t.x - px, t.y - py
        d = math.hypot(dx, dy) or 1
        dx, dy = dx / d + random.uniform(-0.08, 0.08), dy / d + random.uniform(-0.08, 0.08)
        self.cooldown = max(0.35, config.PROJECTILE_COOLDOWN - 0.04 * (self.level - 1))
        spd = config.PROJECTILE_SPEED * (1 + 0.02 * (self.level - 1))
        return Projectile(px, py, dx * spd, dy * spd, self.bolt_damage())


UPGRADES = [
    ("orbit_lv", "Orbit Blades +1 Level", "Damage and speed increased"),
    ("orbit_cnt", "Orbit Blades +1 Count", "One more blade"),
    ("dmg", "Melee Damage", "All weapons damage +12%"),
    ("speed", "Movement Speed", "Movement +8%"),
    ("hp", "HP Recovery", "Maximum health +15, and recover 25 HP"),
    ("missile", "Homing Bullet", "Automatically fire at the nearest enemy"),
    ("missile_lv", "Homing Bullet +1 Level", "Homing bullet stronger and faster"),
]
UPGRADE_META = {u[0]: u for u in UPGRADES}


def update_projectiles(projectiles, enemies, dt):
    for proj in projectiles[:]:
        proj.update(dt)
        if proj.life <= 0:
            projectiles.remove(proj)
            continue
        for e in enemies:
            if e.alive and circles_hit(proj.x, proj.y, proj.radius, e.x, e.y, e.radius):
                e.hit(proj.damage)
                projectiles.remove(proj)
                break


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.world_rect = pygame.Rect(0, 0, config.WORLD_W, config.WORLD_H)
        self.font = config.get_font(20)
        self.font_big = config.get_font(32)
        self.font_small = config.get_font(15)
        self.world_map = self._make_map()
        root_dir = Path(__file__).resolve().parent
        image_dir = root_dir / "images"
        scale = config.DISPLAY_SCALE
        self.tex_knight = load_tex(
            image_dir,
            "knight.png",
            max(8, int(2 * config.PLAYER_RADIUS * scale)),
        )
        self.tex_sword = load_tex(image_dir, "sword.png", max(12, int(20 * scale)))
        self.tex_enemy = {
            "grunt": load_tex(image_dir, "enemy.png", max(8, int(2 * 12 * scale))),
            "runner": load_tex(image_dir, "enemy2.png", max(8, int(2 * 9 * scale))),
            "brute": load_tex(image_dir, "enemy3.png", max(8, int(2 * 18 * scale))),
        }
        self.tex_bullet = load_tex(
            image_dir,
            "bullet.png",
            max(8, int(2 * config.PROJECTILE_RADIUS * scale)),
        )
        self.volume = 0.45
        self._start_bgm()
        self.reset(start_in_menu=True)

    def _start_bgm(self):
        p = Path(__file__).resolve().parent / "music" / "music.mp3"
        if not p.is_file():
            return
        try:
            pygame.mixer.music.load(str(p))
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def _set_volume(self, value):
        self.volume = max(0.0, min(1.0, value))
        try:
            pygame.mixer.music.set_volume(self.volume)
        except pygame.error:
            pass

    def _enemy_tex(self, enemy):
        tex = self.tex_enemy.get(enemy.kind)
        if tex:
            return tex
        return self.tex_enemy.get("grunt")

    def _menu_buttons(self):
        sw, sh = config.SCREEN_W, config.SCREEN_H
        bw = int(sw * 0.24)
        bh = max(44, int(sh * 0.08))
        cx = sw // 2
        y0 = int(sh * 0.42)
        gap = max(16, int(sh * 0.03))
        start_rect = pygame.Rect(cx - bw // 2, y0, bw, bh)
        quit_rect = pygame.Rect(cx - bw // 2, y0 + bh + gap, bw, bh)
        return start_rect, quit_rect

    def _make_map(self):
        sc = config.DISPLAY_SCALE
        map_path = Path(__file__).resolve().parent / "images" / "map.png"
        tw, th = config.WORLD_W, config.WORLD_H
        if map_path.is_file():
            try:
                img = pygame.image.load(str(map_path)).convert()
                if img.get_size() != (tw, th):
                    img = pygame.transform.scale(img, (tw, th))
                if sc != 1.0:
                    img = pygame.transform.scale(img, (int(tw * sc), int(th * sc)))
                return img
            except pygame.error:
                pass
        s = pygame.Surface((tw, th))
        ts = config.TILE_SIZE
        nx, ny = (tw + ts - 1) // ts, (th + ts - 1) // ts
        for ty in range(ny):
            for tx in range(nx):
                wx, wy = tx * ts, ty * ts
                w, h = min(ts, tw - wx), min(ts, th - wy)
                if w <= 0 or h <= 0:
                    continue
                c = config.TILE_COLOR_A if (tx + ty) % 2 == 0 else config.TILE_COLOR_B
                pygame.draw.rect(s, c, (wx, wy, w, h))
        for tx in range(0, nx + 1, 4):
            x = min(tx * ts, tw)
            pygame.draw.line(s, config.TILE_GRID_LINE, (x, 0), (x, th))
        for ty in range(0, ny + 1, 4):
            y = min(ty * ts, th)
            pygame.draw.line(s, config.TILE_GRID_LINE, (0, y), (tw, y))
        if sc != 1.0:
            s = pygame.transform.scale(s, (int(tw * sc), int(th * sc)))
        return s

    def reset(self, start_in_menu=False):
        cx, cy = config.WORLD_W // 2, config.WORLD_H // 2
        self.player = Player(cx, cy)
        self.enemies = []
        self.gems = []
        self.projectiles = []
        self.orbit = OrbitBlades(config.ORBIT_COUNT_START, 1)
        self.missiles = None
        self.time = 0.0
        self.spawn_timer = 0.0
        self.spawn_interval = config.SPAWN_START_INTERVAL
        self.batch = config.BATCH_SIZE_START
        self.state = "menu" if start_in_menu else "playing"
        self.level_queue = 0
        self.upgrade_choices = []
        self.pick_i = 0
        self.next_enemy_id = 0
        self.enemy_ids = {}

    def _spawn(self):
        wave = self.time + self.player.level * 4
        for _ in range(self.batch):
            e = spawn_enemy(self.player.x, self.player.y, wave)
            self.next_enemy_id += 1
            self.enemy_ids[id(e)] = self.next_enemy_id
            self.enemies.append(e)

    def _clean_dead(self):
        for e in self.enemies[:]:
            if e.alive:
                continue
            j = random.uniform(-10, 10)
            self.gems.append(Gem(e.x + j, e.y + random.uniform(-10, 10)))
            if id(e) in self.enemy_ids:
                del self.enemy_ids[id(e)]
            self.enemies.remove(e)

    def _roll_upgrades(self):
        skip = "missile_lv" if self.missiles is None else "missile"
        pool = [u[0] for u in UPGRADES if u[0] != skip]
        self.upgrade_choices = random.sample(pool, min(3, len(pool)))
        self.pick_i = 0

    def _apply_upgrade(self, key):
        p = self.player
        if key == "orbit_lv":
            self.orbit.level += 1
        elif key == "orbit_cnt":
            self.orbit.count += 1
        elif key == "dmg":
            p.damage_mult *= 1.12
        elif key == "speed":
            p.speed *= 1.08
        elif key == "hp":
            p.max_hp += 15
            p.hp = min(p.max_hp, p.hp + 25)
        elif key == "missile":
            self.missiles = HomingMissiles(1)
        elif key == "missile_lv" and self.missiles:
            self.missiles.level += 1
        p.magnet = config.MAGNET_BASE + config.MAGNET_PER_LEVEL * max(0, p.level - 1)

    def handle_input(self, events):
        for ev in events:
            if ev.type == pygame.QUIT:
                raise SystemExit
            if self.state == "menu":
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    start_rect, quit_rect = self._menu_buttons()
                    if start_rect.collidepoint(ev.pos):
                        self.state = "playing"
                    elif quit_rect.collidepoint(ev.pos):
                        raise SystemExit
                    return
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "playing"
                    elif ev.key == pygame.K_ESCAPE:
                        raise SystemExit
                return
            if self.state == "game_over" and ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                self.reset()
                return
            if self.state == "playing" and ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.state = "paused"
                return
            if self.state == "paused" and ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.state = "playing"
                elif ev.key in (pygame.K_LEFT, pygame.K_a, pygame.K_MINUS):
                    self._set_volume(self.volume - 0.05)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_EQUALS):
                    self._set_volume(self.volume + 0.05)
                return
            if self.state == "level_up" and ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_1, pygame.K_a):
                    self.pick_i = 0
                elif ev.key in (pygame.K_2, pygame.K_s):
                    self.pick_i = min(1, len(self.upgrade_choices) - 1)
                elif ev.key in (pygame.K_3, pygame.K_d):
                    self.pick_i = min(2, len(self.upgrade_choices) - 1)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.upgrade_choices:
                        self._apply_upgrade(self.upgrade_choices[self.pick_i])
                    self.level_queue -= 1
                    if self.level_queue > 0:
                        self._roll_upgrades()
                    else:
                        self.state = "playing"
                return

    def update(self, dt):
        if self.state in ("menu", "game_over", "level_up", "paused"):
            return
        keys = pygame.key.get_pressed()
        self.time += dt
        self.player.update(dt, keys, self.world_rect)

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self._spawn()
            self.spawn_timer = self.spawn_interval
            self.spawn_interval = max(config.SPAWN_MIN_INTERVAL, self.spawn_interval * config.DIFFICULTY_RAMP)
        self.batch = config.BATCH_SIZE_START + int(self.time / config.BATCH_GROW_EVERY)

        p = self.player
        for e in self.enemies:
            e.update(dt, p.x, p.y)
            if e.touch_cooldown <= 0 and dist(e.x, e.y, p.x, p.y) < e.radius + p.radius:
                p.take_damage(e.damage)
                e.touch_cooldown = 0.5

        self.orbit.update(dt)
        for i, e in enumerate(self.enemies):
            if not e.alive:
                continue
            eid = self.enemy_ids.get(id(e), i)
            if self.orbit.hit_cd.get(eid, 0) > 0:
                continue
            dmg = self.orbit.blade_damage() * p.damage_mult
            for bx, by, br, _ in self.orbit.blade_positions(p.x, p.y):
                if circles_hit(bx, by, br, e.x, e.y, e.radius):
                    self.orbit.hit_cd[eid] = config.ORBIT_HIT_COOLDOWN
                    e.hit(dmg)
                    break
        self._clean_dead()

        if self.missiles:
            self.missiles.update(dt)
            proj = self.missiles.try_fire(p.x, p.y, self.enemies)
            if proj:
                proj.damage *= p.damage_mult
                self.projectiles.append(proj)
        update_projectiles(self.projectiles, self.enemies, dt)
        self._clean_dead()

        if p.alive():
            for g in self.gems:
                if not g.collected:
                    g.update(dt, p.x, p.y, p.magnet)
                    if dist(g.x, g.y, p.x, p.y) < g.radius + p.radius:
                        g.collected = True
                        self.level_queue += p.add_xp(g.value)
            self.gems = [g for g in self.gems if not g.collected]
            if self.state == "playing" and self.level_queue > 0:
                self._roll_upgrades()
                self.state = "level_up"

        if not p.alive():
            self.state = "game_over"


def draw(game):
    surf = game.screen
    p = game.player
    icx, icy = camera_xy(p.x, p.y)
    s = config.DISPLAY_SCALE
    surf.blit(game.world_map, (-int(icx * s), -int(icy * s)))

    for g in game.gems:
        sx, sy = to_screen(g.x, g.y, icx, icy)
        pygame.draw.circle(surf, config.XP_COLOR, (sx, sy), sr(g.radius))

    for e in game.enemies:
        sx, sy = to_screen(e.x, e.y, icx, icy)
        tex = game._enemy_tex(e)
        if tex:
            surf.blit(tex, tex.get_rect(center=(sx, sy)))
        else:
            pygame.draw.circle(surf, ENEMY_COLOR.get(e.kind, (140, 80, 200)), (sx, sy), sr(e.radius))
        ratio = max(0, e.hp / e.max_hp)
        bw = int(e.radius * 2.2 * s)
        by = sy - sr(e.radius) - int(8 * s)
        pygame.draw.rect(surf, (40, 40, 50), (sx - bw // 2, by, bw, max(1, int(4 * s))))
        pygame.draw.rect(surf, config.DANGER, (sx - bw // 2, by, int(bw * ratio), max(1, int(4 * s))))

    for bx, by, br, bang in game.orbit.blade_positions(p.x, p.y):
        sbx, sby = to_screen(bx, by, icx, icy)
        if game.tex_sword:
            blit_rot_center(surf, game.tex_sword, (sbx, sby), bang)
        else:
            pygame.draw.circle(surf, config.ACCENT, (sbx, sby), sr(br))

    for pr in game.projectiles:
        sx, sy = to_screen(pr.x, pr.y, icx, icy)
        if game.tex_bullet:
            rot = pygame.transform.rotate(game.tex_bullet, -math.degrees(math.atan2(pr.vy, pr.vx)))
            surf.blit(rot, rot.get_rect(center=(sx, sy)))
        else:
            pygame.draw.circle(surf, (255, 200, 80), (sx, sy), sr(pr.radius))

    flash = p.iframes > 0 and (pygame.time.get_ticks() // 100) % 2 == 0
    psx, psy = to_screen(p.x, p.y, icx, icy)
    if game.tex_knight:
        if flash:
            pygame.draw.circle(surf, (255, 255, 200), (psx, psy), sr(p.radius) + 2)
        surf.blit(game.tex_knight, game.tex_knight.get_rect(center=(psx, psy)))
    else:
        col = (220, 230, 255) if not flash else (255, 255, 200)
        pygame.draw.circle(surf, col, (psx, psy), sr(p.radius))
        pygame.draw.circle(surf, config.ACCENT, (psx, psy), sr(p.radius), max(1, int(2 * s)))

    font, fs = game.font, game.font_small
    sw, sh = config.SCREEN_W, config.SCREEN_H
    edge_x = max(56, int(52 * sw / 960))
    edge_y = max(44, int(40 * sh / 540))
    bar_w = int(220 * sw / 960)
    bar_h = max(8, int(10 * sh / 540))
    hp_w = int(200 * sw / 960)
    gap = max(8, int(10 * sh / 540))
    line = font.render(f"Time {game.time:.0f}s  |  Lv.{p.level}", True, config.TEXT)
    need = config.xp_for_next_level(p.level)
    lbl_xp = fs.render(f"Experience {p.xp_into_level}/{need}", True, config.TEXT)
    hp_h = max(8, int(12 * sh / 540))
    lbl_hp = fs.render(f"Health {int(p.hp)}/{int(p.max_hp)}", True, config.TEXT)
    surf.blit(line, (edge_x, edge_y))
    y = edge_y + line.get_height() + gap
    br = pygame.Rect(edge_x, y, bar_w, bar_h)
    pygame.draw.rect(surf, config.UI_BG, br)
    fill = int(br.w * min(1.0, p.xp_into_level / max(1, need)))
    pygame.draw.rect(surf, config.ACCENT, (br.x, br.y, fill, br.h))
    y = br.bottom + 4
    surf.blit(lbl_xp, (edge_x, y))
    y += lbl_xp.get_height() + gap
    pygame.draw.rect(surf, config.UI_BG, (edge_x, y, hp_w, hp_h))
    pygame.draw.rect(surf, (80, 200, 120), (edge_x, y, int(hp_w * max(0, p.hp / p.max_hp)), hp_h))
    y += hp_h + 4
    surf.blit(lbl_hp, (edge_x, y))

    hint = fs.render("WASD Move | ESC Pause | Upgrade 1/2/3 + Enter", True, (150, 155, 175))
    surf.blit(hint, (edge_x, sh - hint.get_height() - edge_y))

    off = max(18, int(24 * sh / 540))
    cx, cyy = sw // 2, sh // 2
    if game.state == "menu":
        overlay(surf, sw, sh, (0, 0, 0, 170))
        t = game.font_big.render("Demo - Survival", True, config.ACCENT)
        surf.blit(t, t.get_rect(center=(cx, int(sh * 0.28))))
        start_rect, quit_rect = game._menu_buttons()
        mouse_pos = pygame.mouse.get_pos()
        start_hover = start_rect.collidepoint(mouse_pos)
        quit_hover = quit_rect.collidepoint(mouse_pos)
        start_bg = (110, 90, 190) if start_hover else config.UI_BG
        quit_bg = (130, 70, 70) if quit_hover else config.UI_BG
        pygame.draw.rect(surf, start_bg, start_rect, border_radius=8)
        pygame.draw.rect(surf, config.ACCENT, start_rect, width=2, border_radius=8)
        pygame.draw.rect(surf, quit_bg, quit_rect, border_radius=8)
        pygame.draw.rect(surf, config.DANGER, quit_rect, width=2, border_radius=8)
        start_txt = game.font.render("Start Game", True, config.TEXT)
        quit_txt = game.font.render("Quit", True, config.TEXT)
        surf.blit(start_txt, start_txt.get_rect(center=start_rect.center))
        surf.blit(quit_txt, quit_txt.get_rect(center=quit_rect.center))
        t3 = fs.render("WASD Move | ESC Pause | Upgrade 1/2/3 + Enter", True, config.TEXT)
        surf.blit(t3, t3.get_rect(center=(cx, quit_rect.bottom + int(sh * 0.08))))

    if game.state == "game_over":
        overlay(surf, sw, sh, (0, 0, 0, 170))
        t = game.font_big.render("Game Over", True, config.DANGER)
        surf.blit(t, t.get_rect(center=(cx, cyy - off)))
        t2 = font.render(f"Survival {game.time:.1f} seconds — R Restart", True, config.TEXT)
        surf.blit(t2, t2.get_rect(center=(cx, cyy + off)))

    if game.state == "paused":
        overlay(surf, sw, sh, (0, 0, 0, 120))
        t = game.font_big.render("Paused", True, config.TEXT)
        surf.blit(t, t.get_rect(center=(cx, cyy - off)))
        t2 = font.render("ESC: Continue  |  Left/Right (A/D): Volume", True, config.TEXT)
        surf.blit(t2, t2.get_rect(center=(cx, cyy + off)))
        vw = int(sw * 0.32)
        vh = max(12, int(sh * 0.02))
        vx = cx - vw // 2
        vy = cyy + off * 2
        pygame.draw.rect(surf, config.UI_BG, (vx, vy, vw, vh))
        pygame.draw.rect(surf, config.ACCENT, (vx, vy, int(vw * game.volume), vh))
        lbl = fs.render(f"Volume: {int(game.volume * 100)}%", True, config.TEXT)
        surf.blit(lbl, lbl.get_rect(center=(cx, vy + vh + 20)))

    if game.state == "level_up":
        overlay(surf, sw, sh, (10, 8, 20, 210))
        t = game.font_big.render("Upgrade — Choose one", True, config.ACCENT)
        surf.blit(t, t.get_rect(center=(cx, int(sh * 0.12))))
        y = int(sh * 0.28)
        row_gap = max(56, int(72 * sh / 540))
        for idx, key in enumerate(game.upgrade_choices):
            meta = UPGRADE_META.get(key, (key, key, ""))
            name, desc = meta[1], meta[2]
            c = (255, 240, 200) if idx == game.pick_i else config.TEXT
            pre = ">" if idx == game.pick_i else " "
            line1 = font.render(f"{pre} {idx + 1}. {name}", True, c)
            r1 = line1.get_rect(midtop=(cx, y))
            surf.blit(line1, r1)
            line2 = fs.render(desc, True, (160, 165, 190))
            r2 = line2.get_rect(midtop=(cx, r1.bottom + 6))
            surf.blit(line2, r2)
            y = r2.bottom + row_gap


def run():
    g = Game()
    while True:
        dt = g.clock.tick(60) / 1000.0
        events = pygame.event.get()
        try:
            g.handle_input(events)
        except SystemExit:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            pygame.quit()
            return
        g.update(dt)
        draw(g)
        pygame.display.flip()


if __name__ == "__main__":
    run()
