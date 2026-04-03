"""Level generation and management."""
import pygame
import random
import math
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y, WEAPON_NAMES
from background import Background
from enemy import Slime, BushSpike, FlyingBat, ArmoredCrab, Boulder
from powerup import GemPickup, WeaponPickup, HeartPickup, ShieldPickup

# Theme ground/platform colours
THEME_COLORS = {
    'meadow':     {'plat': (87, 160, 50),   'plat2': (60, 120, 30),  'edge': (100, 200, 60)},
    'forest':     {'plat': (50, 100, 30),   'plat2': (40, 80, 20),   'edge': (70, 140, 40)},
    'desert':     {'plat': (210, 180, 100), 'plat2': (180, 150, 70), 'edge': (235, 205, 120)},
    'twilight':   {'plat': (80, 55, 90),    'plat2': (60, 35, 70),   'edge': (110, 75, 120)},
    'ice':        {'plat': (190, 220, 255), 'plat2': (160, 190, 230),'edge': (220, 240, 255)},
    'underwater': {'plat': (0, 70, 110),    'plat2': (0, 50, 90),    'edge': (0, 110, 160)},
    'volcano':    {'plat': (110, 35, 15),   'plat2': (85, 25, 8),    'edge': (160, 60, 20)},
    'sky':        {'plat': (255, 255, 255), 'plat2': (210, 215, 255),'edge': (230, 240, 255)},
    'cave':       {'plat': (75, 35, 115),   'plat2': (55, 15, 95),   'edge': (100, 55, 145)},
    'castle':     {'plat': (55, 35, 75),    'plat2': (35, 15, 55),   'edge': (80, 55, 100)},
}


class Level:
    def __init__(self, level_data):
        self.data = level_data
        self.world_width = level_data['length']
        self.platforms = []
        self.enemies = []
        self.powerups = []
        self.background = Background(level_data, self.world_width)
        self.goal_x = self.world_width - 250
        self._portal_anim = 0.0
        self._generate()

    # ------------------------------------------------------------------
    def _generate(self):
        d = self.data
        theme = d['theme']
        espeed = d['enemy_speed']
        num_enemies = d['enemies']
        level_id = d['id']

        # Ground platform (full width)
        self.platforms.append(pygame.Rect(0, GROUND_Y, self.world_width, 200))

        # Floating platforms
        rng = random.Random(level_id * 1337)
        x = 400
        while x < self.world_width - 300:
            w = rng.randint(80, 220)
            y = GROUND_Y - rng.randint(80, 260)
            self.platforms.append(pygame.Rect(x, y, w, 18))
            x += rng.randint(150, 350)

        # Enemies distributed across the level
        enemy_types = self._get_enemy_types(level_id)
        enemy_xs = [rng.randint(350, self.world_width - 400) for _ in range(num_enemies)]
        for i, ex in enumerate(enemy_xs):
            etype = enemy_types[i % len(enemy_types)]
            ey = GROUND_Y - etype.HEIGHT
            # Snap to nearest platform if close
            for plat in self.platforms[1:]:
                if abs(plat.centerx - ex) < 120:
                    ey = plat.top - etype.HEIGHT
                    ex = plat.centerx + rng.randint(-30, 30)
                    break
            self.enemies.append(etype(ex, ey, espeed))

        # Powerups
        gem_xs = [rng.randint(200, self.world_width - 200) for _ in range(18 + level_id * 2)]
        for gx in gem_xs:
            gy = GROUND_Y - 40
            for plat in self.platforms[1:]:
                if abs(plat.centerx - gx) < 60:
                    gy = plat.top - 28
                    break
            self.powerups.append(GemPickup(gx, gy))

        # Weapon pickups (one per 600px roughly)
        wx = 500
        widx = 1
        while wx < self.world_width - 300:
            wy = GROUND_Y - 45
            for plat in self.platforms[1:]:
                if abs(plat.centerx - wx) < 80:
                    wy = plat.top - 30
                    break
            self.powerups.append(WeaponPickup(wx, wy, widx % len(WEAPON_NAMES)))
            widx += 1
            wx += rng.randint(500, 900)

        # Hearts every ~2000px
        hx = 1000
        while hx < self.world_width - 300:
            self.powerups.append(HeartPickup(hx, GROUND_Y - 45))
            hx += rng.randint(1500, 2500)

        # Shield pickups
        for _ in range(2 + level_id // 3):
            sx = rng.randint(400, self.world_width - 400)
            self.powerups.append(ShieldPickup(sx, GROUND_Y - 45))

    def _get_enemy_types(self, level_id):
        if level_id == 1:
            return [Slime, BushSpike]
        elif level_id == 2:
            return [Slime, BushSpike, FlyingBat]
        elif level_id <= 4:
            return [Slime, BushSpike, FlyingBat, ArmoredCrab]
        elif level_id <= 6:
            return [Slime, FlyingBat, ArmoredCrab, Boulder]
        else:
            return [Slime, FlyingBat, ArmoredCrab, Boulder, BushSpike]

    # ------------------------------------------------------------------
    def update(self, camera_x, player, dt):
        self.background.update(camera_x, dt)
        self._portal_anim += dt
        for e in self.enemies:
            e.update(dt, player.world_x, self.platforms)
        for p in self.powerups:
            p.update(dt)

    def draw(self, surface, camera_x):
        self.background.draw(surface, camera_x)
        self._draw_platforms(surface, camera_x)
        for e in self.enemies:
            e.draw(surface, camera_x)
        for p in self.powerups:
            p.draw(surface, camera_x)
        self._draw_goal(surface, camera_x)

    # ------------------------------------------------------------------
    def _draw_platforms(self, surface, camera_x):
        theme = self.data['theme']
        tc = THEME_COLORS.get(theme, THEME_COLORS['meadow'])
        pc = tc['plat']
        pc2 = tc['plat2']
        edge = tc['edge']

        for plat in self.platforms[1:]:  # skip ground (drawn by background)
            sx = plat.x - int(camera_x)
            sy = plat.y
            if sx + plat.width < -10 or sx > SCREEN_WIDTH + 10:
                continue
            pygame.draw.rect(surface, pc, (sx, sy, plat.width, plat.height))
            pygame.draw.rect(surface, edge, (sx, sy, plat.width, 4))
            pygame.draw.rect(surface, pc2, (sx, sy + 4, plat.width, plat.height - 4))
            # Side shading
            pygame.draw.rect(surface, tuple(max(0, c - 30) for c in pc2),
                             (sx + plat.width - 3, sy, 3, plat.height))

    def _draw_goal(self, surface, camera_x):
        gx = int(self.goal_x - camera_x)
        gy = GROUND_Y
        if abs(gx) > SCREEN_WIDTH + 100:
            return
        t = self._portal_anim
        # Spinning portal ring
        radius = int(36 + 6 * math.sin(t * 3))
        for ring, col, alpha in [(radius + 8, (100, 50, 255, 60), 60),
                                  (radius, (180, 100, 255, 130), 130),
                                  (radius - 6, (230, 180, 255, 200), 200)]:
            ring_surf = pygame.Surface((ring * 2 + 4, ring * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, col[:3] + (alpha,), (ring + 2, ring + 2), ring, 5)
            surface.blit(ring_surf, (gx - ring - 2, gy - ring * 2 - 2))

        # Inner swirl
        for i in range(8):
            angle = t * 2 + i * math.pi / 4
            ix = gx + int((radius - 10) * math.cos(angle))
            iy = gy - radius - 4 + int((radius - 10) * math.sin(angle))
            pygame.draw.circle(surface, (200, 150, 255), (ix, iy), 4)

        # Star sign
        for i in range(5):
            angle2 = t + i * 2 * math.pi / 5
            sx2 = gx + int(18 * math.cos(angle2))
            sy2 = gy - radius - 4 + int(18 * math.sin(angle2))
            pygame.draw.circle(surface, (255, 240, 120), (sx2, sy2), 3)

        # "GOAL" label
        font = pygame.font.SysFont('Arial', 16, bold=True)
        lbl = font.render('GOAL', True, (255, 240, 120))
        surface.blit(lbl, (gx - lbl.get_width() // 2, gy - radius * 2 - 30))
