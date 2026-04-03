"""Power-up pickups for Kitsune Adventure."""
import pygame
import math
from constants import WEAPON_NAMES


# Colors per weapon
WEAPON_COLORS = {
    'Normal': (255, 230, 50),
    'Spread': (50, 220, 255),
    'Bounce': (60, 200, 60),
    'Homing': (180, 50, 255),
    'Laser': (255, 60, 60),
    'Bomb': (255, 140, 30),
}


class GemPickup:
    POINTS = 50
    WIDTH = 20
    HEIGHT = 20

    def __init__(self, world_x, world_y):
        self.world_x = float(world_x)
        self.world_y = float(world_y)
        self.alive = True
        self._anim_t = 0.0

    def get_rect(self):
        return pygame.Rect(int(self.world_x) - 10, int(self.world_y) - 10, 20, 20)

    def update(self, dt):
        self._anim_t += dt

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y + math.sin(self._anim_t * 3) * 4)
        # Star shape (rotating gem)
        angle_offset = self._anim_t * 2
        outer_r = 10
        inner_r = 5
        pts = []
        for i in range(10):
            angle = angle_offset + i * math.pi / 5
            r = outer_r if i % 2 == 0 else inner_r
            pts.append((sx + int(r * math.cos(angle)), sy + int(r * math.sin(angle))))
        if len(pts) >= 3:
            pygame.draw.polygon(surface, (255, 215, 0), pts)
            pygame.draw.polygon(surface, (255, 240, 120), pts[:5])
        # Sparkle
        if int(self._anim_t * 8) % 3 == 0:
            pygame.draw.line(surface, (255, 255, 200), (sx, sy - 14), (sx, sy - 8), 2)
            pygame.draw.line(surface, (255, 255, 200), (sx - 14, sy), (sx - 8, sy), 2)


class WeaponPickup:
    WIDTH = 22
    HEIGHT = 22

    def __init__(self, world_x, world_y, weapon_index):
        self.world_x = float(world_x)
        self.world_y = float(world_y)
        self.alive = True
        self.weapon_index = weapon_index % len(WEAPON_NAMES)
        self._anim_t = 0.0
        self._color = WEAPON_COLORS.get(WEAPON_NAMES[self.weapon_index], (200, 200, 200))

    def get_rect(self):
        return pygame.Rect(int(self.world_x) - 11, int(self.world_y) - 11, 22, 22)

    def update(self, dt):
        self._anim_t += dt

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y + math.sin(self._anim_t * 2.5) * 5)
        col = self._color
        # Glowing orb
        glow_size = int(18 + 4 * math.sin(self._anim_t * 3))
        glow_surf = pygame.Surface((glow_size * 2 + 4, glow_size * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*col, 60), (glow_size + 2, glow_size + 2), glow_size)
        surface.blit(glow_surf, (sx - glow_size - 2, sy - glow_size - 2))
        # Core
        pygame.draw.circle(surface, col, (sx, sy), 11)
        pygame.draw.circle(surface, tuple(min(255, c + 80) for c in col), (sx - 3, sy - 3), 5)
        # Letter indicator
        name = WEAPON_NAMES[self.weapon_index]
        font = pygame.font.SysFont('Arial', 11, bold=True)
        lbl = font.render(name[0], True, (10, 10, 10))
        surface.blit(lbl, (sx - lbl.get_width() // 2, sy - lbl.get_height() // 2))


class HeartPickup:
    WIDTH = 22
    HEIGHT = 20

    def __init__(self, world_x, world_y):
        self.world_x = float(world_x)
        self.world_y = float(world_y)
        self.alive = True
        self._anim_t = 0.0

    def get_rect(self):
        return pygame.Rect(int(self.world_x) - 11, int(self.world_y) - 10, 22, 20)

    def update(self, dt):
        self._anim_t += dt

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y + math.sin(self._anim_t * 3) * 4)
        scale = 1.0 + 0.1 * math.sin(self._anim_t * 4)
        s = int(10 * scale)
        # Heart shape using two circles + triangle
        pygame.draw.circle(surface, (240, 50, 80), (sx - s // 2, sy - 2), s // 2 + 1)
        pygame.draw.circle(surface, (240, 50, 80), (sx + s // 2, sy - 2), s // 2 + 1)
        pygame.draw.polygon(surface, (240, 50, 80), [
            (sx - s, sy - 2),
            (sx + s, sy - 2),
            (sx, sy + s),
        ])
        # Highlight
        pygame.draw.circle(surface, (255, 150, 170), (sx - s // 2 + 1, sy - 3), max(2, s // 4))


class ShieldPickup:
    WIDTH = 22
    HEIGHT = 24

    def __init__(self, world_x, world_y):
        self.world_x = float(world_x)
        self.world_y = float(world_y)
        self.alive = True
        self._anim_t = 0.0

    def get_rect(self):
        return pygame.Rect(int(self.world_x) - 11, int(self.world_y) - 12, 22, 24)

    def update(self, dt):
        self._anim_t += dt

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y + math.sin(self._anim_t * 2.5) * 4)
        # Glowing shield shape
        glow_surf = pygame.Surface((34, 38), pygame.SRCALPHA)
        pygame.draw.polygon(glow_surf, (50, 150, 255, 60), [
            (17, 2), (32, 10), (32, 22), (17, 36), (2, 22), (2, 10)
        ])
        surface.blit(glow_surf, (sx - 17, sy - 19))
        # Shield body
        pygame.draw.polygon(surface, (50, 120, 220), [
            (sx, sy - 12), (sx + 10, sy - 6), (sx + 10, sy + 4),
            (sx, sy + 13), (sx - 10, sy + 4), (sx - 10, sy - 6)
        ])
        pygame.draw.polygon(surface, (100, 180, 255), [
            (sx, sy - 9), (sx + 7, sy - 4), (sx + 7, sy + 2),
            (sx, sy + 9), (sx - 7, sy + 2), (sx - 7, sy - 4)
        ])
        # Star in centre
        pygame.draw.circle(surface, (200, 230, 255), (sx, sy), 4)
