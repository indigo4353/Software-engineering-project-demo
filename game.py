"""
游戏主程序：玩家、怪、武器、拾取、地图和界面都在这个文件里。
"""
import math
import random

import pygame

import config

# ---------- 小工具 ----------


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def circles_hit(ax, ay, ar, bx, by, br):
    return (ax - bx) ** 2 + (ay - by) ** 2 <= (ar + br) ** 2


def camera_xy(px, py):
    cx = max(0, min(px - config.SCREEN_W / 2, config.WORLD_W - config.SCREEN_W))
    cy = max(0, min(py - config.SCREEN_H / 2, config.WORLD_H - config.SCREEN_H))
    return int(cx), int(cy)


def to_screen(wx, wy, cam_x, cam_y):
    return int(wx) - cam_x, int(wy) - cam_y


# ---------- 游戏对象 ----------


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
            return True
        return False


def spawn_enemy(px, py, wave):
    ang = random.uniform(0, 2 * math.pi)
    d0 = max(config.SCREEN_W, config.SCREEN_H) * 0.52 + random.uniform(50, 220)
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
        for k in list(self.hit_cd.keys()):
            self.hit_cd[k] -= dt
            if self.hit_cd[k] <= 0:
                del self.hit_cd[k]

    def blade_positions(self, px, py):
        out = []
        for i in range(self.count):
            a = self.angle + (2 * math.pi * i) / max(1, self.count)
            out.append((px + math.cos(a) * config.ORBIT_RADIUS, py + math.sin(a) * config.ORBIT_RADIUS, 10.0))
        return out


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
        dx, dy = dx / d, dy / d
        dx += random.uniform(-0.08, 0.08)
        dy += random.uniform(-0.08, 0.08)
        self.cooldown = max(0.35, config.PROJECTILE_COOLDOWN - 0.04 * (self.level - 1))
        spd = config.PROJECTILE_SPEED * (1 + 0.02 * (self.level - 1))
        return Projectile(px, py, dx * spd, dy * spd, self.bolt_damage())


UPGRADES = [
    ("orbit_lv", "环绕飞刀 +1 等级", "伤害与转速提高"),
    ("orbit_cnt", "环绕飞刀 +1 数量", "多一枚飞刀"),
    ("dmg", "近战威力", "所有武器伤害 +12%"),
    ("speed", "移速", "移动 +8%"),
    ("hp", "体质", "最大生命 +15，并回血"),
    ("missile", "追踪火球", "自动朝最近敌人发射"),
    ("missile_lv", "火球强化", "火球更强更快"),
]


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


# ---------- 主逻辑 ----------


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.world_rect = pygame.Rect(0, 0, config.WORLD_W, config.WORLD_H)
        self.font = config.get_font(18)
        self.font_big = config.get_font(28)
        self.font_small = config.get_font(14)
        self.world_map = self._make_map()
        self.reset()

    def _make_map(self):
        s = pygame.Surface((config.WORLD_W, config.WORLD_H))
        ts = config.TILE_SIZE
        nx = (config.WORLD_W + ts - 1) // ts
        ny = (config.WORLD_H + ts - 1) // ts
        for ty in range(ny):
            for tx in range(nx):
                wx, wy = tx * ts, ty * ts
                w = min(ts, config.WORLD_W - wx)
                h = min(ts, config.WORLD_H - wy)
                if w <= 0 or h <= 0:
                    continue
                c = config.TILE_COLOR_A if (tx + ty) % 2 == 0 else config.TILE_COLOR_B
                pygame.draw.rect(s, c, (wx, wy, w, h))
        for tx in range(0, nx + 1, 4):
            x = min(tx * ts, config.WORLD_W)
            pygame.draw.line(s, config.TILE_GRID_LINE, (x, 0), (x, config.WORLD_H))
        for ty in range(0, ny + 1, 4):
            y = min(ty * ts, config.WORLD_H)
            pygame.draw.line(s, config.TILE_GRID_LINE, (0, y), (config.WORLD_W, y))
        return s

    def reset(self):
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
        self.state = "playing"
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
        pool = [u[0] for u in UPGRADES]
        if self.missiles is None:
            pool = [p for p in pool if p != "missile_lv"]
        else:
            pool = [p for p in pool if p != "missile"]
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
            if self.state == "game_over" and ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                self.reset()
                return
            if self.state == "playing" and ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.state = "paused"
                return
            if self.state == "paused" and ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.state = "playing"
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
        if self.state in ("game_over", "level_up", "paused"):
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
            for bx, by, br in self.orbit.blade_positions(p.x, p.y):
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
    surf.fill(config.BG)
    p = game.player
    icx, icy = camera_xy(p.x, p.y)
    surf.blit(game.world_map, (-icx, -icy))

    for g in game.gems:
        sx, sy = to_screen(g.x, g.y, icx, icy)
        pygame.draw.circle(surf, config.XP_COLOR, (sx, sy), int(g.radius))

    for e in game.enemies:
        sx, sy = to_screen(e.x, e.y, icx, icy)
        if e.kind == "grunt":
            col = (200, 90, 90)
        elif e.kind == "runner":
            col = (230, 160, 80)
        else:
            col = (140, 80, 200)
        pygame.draw.circle(surf, col, (sx, sy), int(e.radius))
        ratio = max(0, e.hp / e.max_hp)
        bw = int(e.radius * 2.2)
        by = sy - int(e.radius) - 8
        pygame.draw.rect(surf, (40, 40, 50), (sx - bw // 2, by, bw, 4))
        pygame.draw.rect(surf, config.DANGER, (sx - bw // 2, by, int(bw * ratio), 4))

    for bx, by, br in game.orbit.blade_positions(p.x, p.y):
        sbx, sby = to_screen(bx, by, icx, icy)
        pygame.draw.circle(surf, config.ACCENT, (sbx, sby), int(br))

    for pr in game.projectiles:
        sx, sy = to_screen(pr.x, pr.y, icx, icy)
        pygame.draw.circle(surf, (255, 200, 80), (sx, sy), int(pr.radius))

    flash = p.iframes > 0 and (pygame.time.get_ticks() // 100) % 2 == 0
    col = (220, 230, 255) if not flash else (255, 255, 200)
    psx, psy = to_screen(p.x, p.y, icx, icy)
    pygame.draw.circle(surf, col, (psx, psy), int(p.radius))
    pygame.draw.circle(surf, config.ACCENT, (psx, psy), int(p.radius), 2)

    font, fs = game.font, game.font_small
    surf.blit(font.render(f"时间 {game.time:.0f}s  |  Lv.{p.level}", True, config.TEXT), (12, 8))
    need = config.xp_for_next_level(p.level)
    br = pygame.Rect(12, 36, 220, 10)
    pygame.draw.rect(surf, config.UI_BG, br, border_radius=3)
    fill = int(br.w * min(1.0, p.xp_into_level / max(1, need)))
    pygame.draw.rect(surf, config.ACCENT, (br.x, br.y, fill, br.h), border_radius=3)
    surf.blit(fs.render(f"经验 {p.xp_into_level}/{need}", True, config.TEXT), (12, 50))
    hp_w = 200
    pygame.draw.rect(surf, config.UI_BG, (12, 70, hp_w, 12), border_radius=3)
    pygame.draw.rect(surf, (80, 200, 120), (12, 70, int(hp_w * max(0, p.hp / p.max_hp)), 12), border_radius=3)
    surf.blit(fs.render(f"生命 {int(p.hp)}/{int(p.max_hp)}", True, config.TEXT), (12, 86))
    surf.blit(
        fs.render("WASD 移动 | ESC 暂停 | 升级 1/2/3 + Enter", True, (150, 155, 175)),
        (12, config.SCREEN_H - 26),
    )

    if game.state == "game_over":
        ov = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        surf.blit(ov, (0, 0))
        t = game.font_big.render("游戏结束", True, config.DANGER)
        surf.blit(t, t.get_rect(center=(config.SCREEN_W // 2, config.SCREEN_H // 2 - 20)))
        t2 = font.render(f"存活 {game.time:.1f} 秒 — R 重开", True, config.TEXT)
        surf.blit(t2, t2.get_rect(center=(config.SCREEN_W // 2, config.SCREEN_H // 2 + 20)))

    if game.state == "paused":
        ov = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 120))
        surf.blit(ov, (0, 0))
        t = game.font_big.render("已暂停", True, config.TEXT)
        surf.blit(t, t.get_rect(center=(config.SCREEN_W // 2, config.SCREEN_H // 2)))
        t2 = font.render("再按 ESC 继续", True, config.TEXT)
        surf.blit(t2, t2.get_rect(center=(config.SCREEN_W // 2, config.SCREEN_H // 2 + 40)))

    if game.state == "level_up":
        ov = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        ov.fill((10, 8, 20, 210))
        surf.blit(ov, (0, 0))
        t = game.font_big.render("升级 — 选一项", True, config.ACCENT)
        surf.blit(t, t.get_rect(center=(config.SCREEN_W // 2, 80)))
        y = 160
        for idx, key in enumerate(game.upgrade_choices):
            meta = next((u for u in UPGRADES if u[0] == key), (key, key, ""))
            name, desc = meta[1], meta[2]
            c = (255, 240, 200) if idx == game.pick_i else config.TEXT
            pre = ">" if idx == game.pick_i else " "
            surf.blit(font.render(f"{pre} {idx + 1}. {name}", True, c), (config.SCREEN_W // 2 - 200, y))
            surf.blit(fs.render(desc, True, (160, 165, 190)), (config.SCREEN_W // 2 - 180, y + 28))
            y += 72


def run():
    g = Game()
    while True:
        dt = g.clock.tick(60) / 1000.0
        events = pygame.event.get()
        try:
            g.handle_input(events)
        except SystemExit:
            pygame.quit()
            return
        g.update(dt)
        draw(g)
        pygame.display.flip()


if __name__ == "__main__":
    run()
