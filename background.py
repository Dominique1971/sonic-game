"""Parallax background rendering for each theme."""
import pygame
import math
import random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _draw_gradient(surface, top_color, bot_color, y_start=0, y_end=SCREEN_HEIGHT):
    h = y_end - y_start
    if h <= 0:
        return
    strip_h = max(1, h // 60)
    for y in range(y_start, y_end, strip_h):
        t = (y - y_start) / h
        c = _lerp_color(top_color, bot_color, t)
        pygame.draw.rect(surface, c, (0, y, SCREEN_WIDTH, strip_h + 1))


class _Cloud:
    def __init__(self, wx, wy, scale, speed):
        self.wx = wx
        self.wy = wy
        self.scale = scale
        self.speed = speed

    def update(self, dt):
        self.wx -= self.speed * dt * 30

    def draw(self, surface, camera_x, color=(255, 255, 255)):
        sx = int(self.wx - camera_x * 0.2)
        sy = int(self.wy)
        s = self.scale
        puffs = [(-20, 0, 25), (0, -10, 30), (20, 0, 25), (10, 8, 20), (-10, 8, 20)]
        for dx, dy, r in puffs:
            pygame.draw.circle(surface, color, (sx + int(dx * s), sy + int(dy * s)), int(r * s))


class _Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT // 2)
        self.brightness = random.randint(150, 255)
        self.twinkle = random.uniform(0, math.pi * 2)

    def update(self, dt):
        self.twinkle += dt * random.uniform(2, 5)

    def draw(self, surface):
        b = int(self.brightness * (0.6 + 0.4 * math.sin(self.twinkle)))
        pygame.draw.circle(surface, (b, b, b), (self.x, self.y), 1)


class _Bubble:
    def __init__(self, world_width):
        self.wx = random.uniform(0, world_width)
        self.wy = random.uniform(GROUND_Y - 300, GROUND_Y)
        self.speed = random.uniform(20, 60)
        self.r = random.randint(3, 8)

    def update(self, dt):
        self.wy -= self.speed * dt
        if self.wy < 0:
            self.wy = GROUND_Y

    def draw(self, surface, camera_x):
        sx = int(self.wx - camera_x * 0.5)
        sy = int(self.wy)
        if -20 < sx < SCREEN_WIDTH + 20:
            pygame.draw.circle(surface, (100, 180, 255), (sx, sy), self.r, 1)


class _Particle:
    def __init__(self, wx, wy, vx, vy, color, life):
        self.wx = wx
        self.wy = wy
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life

    def update(self, dt):
        self.wx += self.vx * dt
        self.wy += self.vy * dt
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0


class Background:
    def __init__(self, level_data, world_width):
        self.data = level_data
        self.theme = level_data['theme']
        self.world_width = world_width
        self.sky = level_data['sky']
        self.sky2 = level_data['sky2']
        self.ground_color = level_data['ground']
        self.ground2 = level_data['ground2']

        self._clouds = []
        self._stars = []
        self._bubbles = []
        self._particles = []
        self._anim_t = 0.0
        self._lightning_timer = 0.0
        self._lightning_alpha = 0

        self._bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._init_decorations()

    def _init_decorations(self):
        th = self.theme
        if th in ('meadow', 'forest', 'desert', 'sky'):
            for _ in range(8):
                self._clouds.append(_Cloud(
                    random.uniform(0, self.world_width * 0.4),
                    random.uniform(30, 180),
                    random.uniform(0.6, 1.4),
                    random.uniform(0.2, 0.6)
                ))
        if th in ('twilight', 'cave', 'castle', 'underwater'):
            self._stars = [_Star() for _ in range(60)]
        if th == 'underwater':
            self._bubbles = [_Bubble(self.world_width) for _ in range(40)]

    def update(self, camera_x, dt):
        self._anim_t += dt
        for c in self._clouds:
            c.update(dt)
            if c.wx < camera_x - 200:
                c.wx = camera_x + SCREEN_WIDTH + random.uniform(100, 400)
                c.wy = random.uniform(30, 180)
        for s in self._stars:
            s.update(dt)
        for b in self._bubbles:
            b.update(dt)
        for p in list(self._particles):
            p.update(dt)
            if not p.alive:
                self._particles.remove(p)

        if self.theme == 'castle':
            self._lightning_timer -= dt
            if self._lightning_timer <= 0:
                self._lightning_alpha = 180
                self._lightning_timer = random.uniform(2, 6)
            if self._lightning_alpha > 0:
                self._lightning_alpha = max(0, self._lightning_alpha - int(dt * 400))

        if self.theme == 'volcano' and random.random() < 0.05:
            wx = random.uniform(0, self.world_width)
            wy = random.uniform(GROUND_Y - 200, GROUND_Y)
            for _ in range(3):
                self._particles.append(_Particle(
                    wx, wy,
                    random.uniform(-20, 20),
                    random.uniform(-80, -30),
                    (200 + random.randint(0, 55), random.randint(50, 100), 0),
                    random.uniform(1, 3)
                ))

    def draw(self, surface, camera_x):
        th = self.theme
        # Sky gradient
        _draw_gradient(surface, self.sky, self.sky2, 0, GROUND_Y)

        # Theme-specific layers
        if th == 'meadow':
            self._draw_meadow(surface, camera_x)
        elif th == 'forest':
            self._draw_forest(surface, camera_x)
        elif th == 'desert':
            self._draw_desert(surface, camera_x)
        elif th == 'twilight':
            self._draw_twilight(surface, camera_x)
        elif th == 'ice':
            self._draw_ice(surface, camera_x)
        elif th == 'underwater':
            self._draw_underwater(surface, camera_x)
        elif th == 'volcano':
            self._draw_volcano(surface, camera_x)
        elif th == 'sky':
            self._draw_sky(surface, camera_x)
        elif th == 'cave':
            self._draw_cave(surface, camera_x)
        elif th == 'castle':
            self._draw_castle(surface, camera_x)

        # Particles
        for p in self._particles:
            sx = int(p.wx - camera_x * 0.7)
            sy = int(p.wy)
            alpha_r = max(0, p.life / p.max_life)
            c = tuple(int(ch * alpha_r) for ch in p.color)
            if 0 <= sx < SCREEN_WIDTH:
                pygame.draw.circle(surface, c, (sx, sy), 3)

        # Ground strip
        ground_y = GROUND_Y
        pygame.draw.rect(surface, self.ground_color, (0, ground_y, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y))
        pygame.draw.rect(surface, self.ground2, (0, ground_y + 15, SCREEN_WIDTH, 8))

    # ------------------------------------------------------------------
    def _draw_meadow(self, surface, camera_x):
        # Distant hills
        for i in range(5):
            hx = int((i * 700 - camera_x * 0.15) % (SCREEN_WIDTH + 400) - 200)
            hy = GROUND_Y - 80 - i * 20
            pts = []
            for x in range(-150, 151, 10):
                y = hy + int(60 * math.sin(math.pi * (x + 150) / 300))
                pts.append((hx + x, y))
            pts.append((hx + 150, GROUND_Y))
            pts.append((hx - 150, GROUND_Y))
            if len(pts) >= 3:
                pygame.draw.polygon(surface, (100, 180, 70), pts)
        # Clouds
        for c in self._clouds:
            c.draw(surface, camera_x)
        # Bushes near
        for i in range(12):
            bx = int((i * 320 - camera_x * 0.6) % (SCREEN_WIDTH + 100) - 50)
            pygame.draw.ellipse(surface, (60, 130, 40), (bx - 25, GROUND_Y - 30, 50, 30))
            pygame.draw.ellipse(surface, (60, 130, 40), (bx - 15, GROUND_Y - 40, 40, 28))

    def _draw_forest(self, surface, camera_x):
        # Stars/fireflies
        for s in self._stars:
            s.draw(surface)
        # Tall trees far
        for i in range(14):
            tx = int((i * 250 - camera_x * 0.25) % (SCREEN_WIDTH + 200) - 100)
            th2 = 180 + (i * 37) % 80
            pygame.draw.rect(surface, (40, 25, 15), (tx - 8, GROUND_Y - th2, 16, th2))
            pygame.draw.polygon(surface, (20, 60, 20), [
                (tx, GROUND_Y - th2 - 80),
                (tx - 40, GROUND_Y - th2 + 40),
                (tx + 40, GROUND_Y - th2 + 40),
            ])
            pygame.draw.polygon(surface, (25, 70, 25), [
                (tx, GROUND_Y - th2 - 50),
                (tx - 50, GROUND_Y - th2 + 60),
                (tx + 50, GROUND_Y - th2 + 60),
            ])
        # Fireflies
        for i in range(20):
            fx = int((i * 193 + math.sin(self._anim_t * 0.7 + i) * 30 - camera_x * 0.5) % SCREEN_WIDTH)
            fy = int(GROUND_Y - 60 - (i * 57) % 200 + math.sin(self._anim_t * 1.2 + i * 0.5) * 15)
            blink = (math.sin(self._anim_t * 3 + i * 1.7) > 0.3)
            if blink:
                pygame.draw.circle(surface, (200, 255, 100), (fx, fy), 3)

    def _draw_desert(self, surface, camera_x):
        # Sand dunes far
        for i in range(6):
            dx = int((i * 600 - camera_x * 0.2) % (SCREEN_WIDTH + 500) - 200)
            dh = 80 + (i * 43) % 60
            pts = []
            for x in range(-180, 181, 10):
                y = GROUND_Y - int(dh * math.sin(math.pi * (x + 180) / 360) ** 2)
                pts.append((dx + x, y))
            pts += [(dx + 180, GROUND_Y), (dx - 180, GROUND_Y)]
            if len(pts) >= 3:
                pygame.draw.polygon(surface, (220, 190, 120), pts)
        # Pyramids
        for i in range(3):
            px = int((i * 1500 + 400 - camera_x * 0.3) % (SCREEN_WIDTH + 600) - 200)
            pw = 180
            ph = 140
            pygame.draw.polygon(surface, (180, 150, 80), [
                (px, GROUND_Y - ph),
                (px - pw // 2, GROUND_Y),
                (px + pw // 2, GROUND_Y),
            ])
            pygame.draw.polygon(surface, (200, 170, 90), [
                (px, GROUND_Y - ph),
                (px, GROUND_Y),
                (px + pw // 2, GROUND_Y),
            ])
        # Clouds (hazy)
        for c in self._clouds:
            c.draw(surface, camera_x, (255, 230, 180))
        # Cacti
        for i in range(8):
            cx2 = int((i * 450 + 100 - camera_x * 0.7) % (SCREEN_WIDTH + 100) - 50)
            ch = 60 + (i * 23) % 30
            pygame.draw.rect(surface, (40, 100, 30), (cx2 - 5, GROUND_Y - ch, 10, ch))
            pygame.draw.rect(surface, (40, 100, 30), (cx2 - 20, GROUND_Y - ch + 15, 15, 8))
            pygame.draw.rect(surface, (40, 100, 30), (cx2 + 5, GROUND_Y - ch + 20, 15, 8))

    def _draw_twilight(self, surface, camera_x):
        for s in self._stars:
            s.draw(surface)
        # Mountains
        for i in range(5):
            mx = int((i * 500 - camera_x * 0.18) % (SCREEN_WIDTH + 400) - 200)
            mh = 160 + (i * 67) % 100
            pygame.draw.polygon(surface, (60, 35, 70), [
                (mx, GROUND_Y - mh),
                (mx - 120, GROUND_Y),
                (mx + 120, GROUND_Y),
            ])
        for c in self._clouds:
            c.draw(surface, camera_x, (200, 120, 100))

    def _draw_ice(self, surface, camera_x):
        # Snowflakes
        t = self._anim_t
        for i in range(30):
            sx2 = int((i * 213 + t * 20 * (1 + i % 3 * 0.3) - camera_x * 0.1) % SCREEN_WIDTH)
            sy2 = int((i * 137 + t * 25) % SCREEN_HEIGHT)
            pygame.draw.circle(surface, (220, 235, 255), (sx2, sy2), 2)
        # Ice spikes on horizon
        for i in range(12):
            ix = int((i * 280 - camera_x * 0.3) % (SCREEN_WIDTH + 200) - 100)
            ih = 60 + (i * 37) % 50
            pygame.draw.polygon(surface, (190, 215, 240), [
                (ix, GROUND_Y - ih),
                (ix - 18, GROUND_Y),
                (ix + 18, GROUND_Y),
            ])
        for c in self._clouds:
            c.draw(surface, camera_x, (200, 220, 255))

    def _draw_underwater(self, surface, camera_x):
        # Light rays from top
        for i in range(5):
            rx = 150 + i * 220
            alpha = int(40 + 20 * math.sin(self._anim_t * 1.5 + i))
            ray_surf = pygame.Surface((60, GROUND_Y), pygame.SRCALPHA)
            pts = [(0, 0), (60, 0), (80, GROUND_Y), (-20, GROUND_Y)]
            pygame.draw.polygon(ray_surf, (100, 180, 255, alpha), pts)
            surface.blit(ray_surf, (rx - 30, 0))
        # Bubbles
        for b in self._bubbles:
            b.draw(surface, camera_x)
        # Seaweed
        for i in range(10):
            swx = int((i * 350 + 80 - camera_x * 0.6) % (SCREEN_WIDTH + 100) - 50)
            swh = 60 + (i * 37) % 60
            for seg in range(swh // 12):
                szy = GROUND_Y - seg * 12
                swave = int(8 * math.sin(self._anim_t * 2 + i + seg * 0.5))
                pygame.draw.ellipse(surface, (0, 130, 60),
                    (swx + swave - 5, szy - 10, 10, 14))
        # Coral
        for i in range(6):
            corx = int((i * 480 + 150 - camera_x * 0.65) % (SCREEN_WIDTH + 100) - 50)
            col = [(255, 80, 80), (255, 140, 0), (200, 50, 150)][i % 3]
            for j in range(4):
                angle = -math.pi / 2 + (j - 1.5) * 0.4
                ex = corx + int(30 * math.cos(angle))
                ey = GROUND_Y - 10 - int(30 * math.sin(angle))
                pygame.draw.line(surface, col, (corx, GROUND_Y - 5), (ex, ey), 3)

    def _draw_volcano(self, surface, camera_x):
        # Volcanic mountains
        for i in range(4):
            vx = int((i * 800 + 200 - camera_x * 0.25) % (SCREEN_WIDTH + 600) - 200)
            vh = 200 + (i * 57) % 80
            pygame.draw.polygon(surface, (70, 25, 10), [
                (vx, GROUND_Y - vh),
                (vx - 140, GROUND_Y),
                (vx + 140, GROUND_Y),
            ])
            # Lava glow at top
            pygame.draw.circle(surface, (255, 80, 0), (vx, GROUND_Y - vh + 5), 12)
        # Smoke
        for i in range(10):
            sxt = int((i * 200 + self._anim_t * 8 - camera_x * 0.3) % SCREEN_WIDTH)
            syt = int(60 + (i * 97) % 120 + math.sin(self._anim_t + i) * 20)
            alpha_v = 40 + int(20 * math.sin(self._anim_t * 0.7 + i))
            smoke_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(smoke_surf, (80, 60, 50, alpha_v), (20, 20), 18)
            surface.blit(smoke_surf, (sxt - 20, syt - 20))

    def _draw_sky(self, surface, camera_x):
        for c in self._clouds:
            c.draw(surface, camera_x)
        # Extra big clouds
        for i in range(4):
            bclx = int((i * 900 + 100 - camera_x * 0.12) % (SCREEN_WIDTH + 600) - 200)
            bcly = 60 + (i * 80) % 140
            puffs = [(-40, 0, 40), (0, -20, 50), (40, 0, 40), (20, 15, 30), (-20, 15, 30)]
            for dx, dy, r in puffs:
                pygame.draw.circle(surface, (255, 255, 255), (bclx + dx, bcly + dy), r)
        # Birds
        for i in range(6):
            bx = int((i * 300 + self._anim_t * 25 - camera_x * 0.35) % (SCREEN_WIDTH + 100) - 50)
            by = 80 + (i * 70) % 150
            flap = int(8 * math.sin(self._anim_t * 4 + i))
            pygame.draw.arc(surface, (30, 30, 30),
                (bx - 20, by - flap, 18, 14), 0, math.pi, 2)
            pygame.draw.arc(surface, (30, 30, 30),
                (bx + 2, by - flap, 18, 14), 0, math.pi, 2)

    def _draw_cave(self, surface, camera_x):
        for s in self._stars:
            s.draw(surface)
        # Stalactites from top
        for i in range(14):
            stx = int((i * 220 + 60 - camera_x * 0.4) % (SCREEN_WIDTH + 100) - 50)
            sth = 50 + (i * 47) % 80
            col = (60, 40, 80)
            pygame.draw.polygon(surface, col, [
                (stx - 12, 0), (stx + 12, 0), (stx, sth)
            ])
        # Glowing crystals on ground
        for i in range(8):
            crx = int((i * 380 + 100 - camera_x * 0.65) % (SCREEN_WIDTH + 100) - 50)
            crh = 30 + (i * 23) % 40
            colors = [(100, 255, 220), (150, 100, 255), (0, 200, 255)]
            col = colors[i % 3]
            pygame.draw.polygon(surface, col, [
                (crx - 8, GROUND_Y),
                (crx + 8, GROUND_Y),
                (crx + 3, GROUND_Y - crh),
                (crx - 3, GROUND_Y - crh),
            ])
            # Glow
            glow = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*col, 50), (20, 20), 18)
            surface.blit(glow, (crx - 20, GROUND_Y - crh - 20))

    def _draw_castle(self, surface, camera_x):
        if self._lightning_alpha > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 200, self._lightning_alpha))
            surface.blit(flash, (0, 0))
        for s in self._stars:
            s.draw(surface)
        # Gothic castle towers
        for i in range(4):
            ctx = int((i * 500 + 100 - camera_x * 0.2) % (SCREEN_WIDTH + 400) - 200)
            cth = 200 + (i * 60) % 100
            ctw = 60 + (i * 20) % 30
            pygame.draw.rect(surface, (35, 20, 45), (ctx - ctw // 2, GROUND_Y - cth, ctw, cth))
            # Battlements
            for bt in range(4):
                bx2 = ctx - ctw // 2 + bt * (ctw // 3)
                pygame.draw.rect(surface, (35, 20, 45), (bx2, GROUND_Y - cth - 15, ctw // 4, 15))
            # Window glow
            pygame.draw.rect(surface, (255, 200, 50), (ctx - 8, GROUND_Y - cth + 20, 16, 20))
        # Bats
        for i in range(8):
            bx = int((i * 280 + math.sin(self._anim_t * 1.5 + i) * 40 - camera_x * 0.45) % SCREEN_WIDTH)
            by = int(80 + (i * 90) % 200 + math.sin(self._anim_t * 2.3 + i * 0.7) * 20)
            flap = int(5 * math.sin(self._anim_t * 6 + i))
            pygame.draw.polygon(surface, (60, 20, 70), [
                (bx, by), (bx - 15, by - 8 + flap), (bx - 5, by + 5)
            ])
            pygame.draw.polygon(surface, (60, 20, 70), [
                (bx, by), (bx + 15, by - 8 + flap), (bx + 5, by + 5)
            ])
