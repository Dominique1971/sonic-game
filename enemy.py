"""Enemy types for Kitsune Adventure."""
import pygame
import math
import random
from constants import GRAVITY, MAX_FALL_SPEED, GROUND_Y


class _BaseEnemy:
    WIDTH = 36
    HEIGHT = 36

    def __init__(self, world_x, world_y, health, speed):
        self.world_x = float(world_x)
        self.world_y = float(world_y)
        self.vel_x = speed
        self.vel_y = 0.0
        self.health = health
        self.max_health = health
        self.alive = True
        self._anim_t = 0.0
        self._dir = 1

    def get_rect(self):
        return pygame.Rect(
            int(self.world_x - self.WIDTH // 2),
            int(self.world_y),
            self.WIDTH, self.HEIGHT
        )

    def _apply_gravity_and_platforms(self, platforms):
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        self.world_y += self.vel_y
        on_ground = False
        rect = self.get_rect()
        for plat in platforms:
            if rect.colliderect(plat) and self.vel_y > 0:
                if rect.bottom - plat.top < 16:
                    self.world_y = plat.top - self.HEIGHT
                    self.vel_y = 0
                    on_ground = True
        if self.world_y + self.HEIGHT >= GROUND_Y:
            self.world_y = GROUND_Y - self.HEIGHT
            self.vel_y = 0
            on_ground = True
        return on_ground

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.alive = False

    def update(self, dt, player_world_x, platforms):
        pass

    def draw(self, surface, camera_x):
        pass


# ---------------------------------------------------------------------------
class Slime(_BaseEnemy):
    POINTS = 100

    def __init__(self, world_x, world_y, speed=1.0):
        super().__init__(world_x, world_y, 1, speed * 0.8)
        self._walk_timer = 0.0
        self._squash = 0.0  # 0=normal, >0=squash after land

    def update(self, dt, player_world_x, platforms):
        if not self.alive:
            return
        self._anim_t += dt
        # Patrol left/right
        self.world_x += self.vel_x * self._dir * dt * 60
        # Turn at edges (simple: reverse after ~120px)
        self._walk_timer += dt
        if self._walk_timer > 2.0:
            self._walk_timer = 0.0
            self._dir *= -1
        on_ground = self._apply_gravity_and_platforms(platforms)
        if on_ground:
            self._squash = min(1.0, self._squash + dt * 4)
        else:
            self._squash = max(0.0, self._squash - dt * 6)
        # Bound check
        if self.world_x < 0:
            self.world_x = 0
            self._dir = 1

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        # Squash-and-stretch
        bounce = math.sin(self._anim_t * 3) * 3
        squash_y = int(4 * self._squash)
        w, h = 34, 28 - squash_y
        body_rect = (sx - w // 2, sy + squash_y + int(bounce), w, h)
        pygame.draw.ellipse(surface, (60, 180, 60), body_rect)
        pygame.draw.ellipse(surface, (80, 210, 80),
                            (sx - w // 2 + 4, sy + squash_y + int(bounce), w - 8, h - 4))
        # Eyes
        ey = sy + squash_y + int(bounce) + 6
        pygame.draw.circle(surface, (255, 255, 255), (sx - 8, ey), 5)
        pygame.draw.circle(surface, (255, 255, 255), (sx + 8, ey), 5)
        pygame.draw.circle(surface, (10, 10, 10), (sx - 7, ey), 3)
        pygame.draw.circle(surface, (10, 10, 10), (sx + 9, ey), 3)
        # Wobbly mouth
        mouth_y = ey + 8
        wave_pts = [(sx - 8 + i * 4, mouth_y + int(3 * math.sin(i + self._anim_t * 4))) for i in range(5)]
        if len(wave_pts) >= 2:
            pygame.draw.lines(surface, (10, 10, 10), False, wave_pts, 2)


# ---------------------------------------------------------------------------
class BushSpike(_BaseEnemy):
    """Stationary spike bush – cannot be killed."""
    POINTS = 0

    def __init__(self, world_x, world_y, speed=1.0):
        super().__init__(world_x, world_y, 9999, 0)
        self.WIDTH = 44
        self.HEIGHT = 38

    def hit(self):
        pass  # immortal

    def update(self, dt, player_world_x, platforms):
        self._anim_t += dt

    def draw(self, surface, camera_x):
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        # Brown base
        pygame.draw.ellipse(surface, (100, 60, 20), (sx - 22, sy + 22, 44, 16))
        # Spiky triangles
        spike_cols = [(30, 80, 20), (40, 100, 25), (20, 70, 15)]
        for i in range(6):
            angle = i * math.pi / 3 + self._anim_t * 0.5
            r = 18
            tip_x = sx + int(r * math.cos(angle))
            tip_y = sy + 18 + int(r * math.sin(angle))
            col = spike_cols[i % 3]
            pygame.draw.polygon(surface, col, [
                (sx, sy + 18),
                (tip_x - 5, tip_y),
                (tip_x + 5, tip_y),
            ])
        # Centre
        pygame.draw.circle(surface, (30, 90, 20), (sx, sy + 18), 10)


# ---------------------------------------------------------------------------
class FlyingBat(_BaseEnemy):
    POINTS = 150

    def __init__(self, world_x, world_y, speed=1.0):
        super().__init__(world_x, world_y, 1, speed * 1.2)
        self._origin_y = world_y
        self._sine_offset = random.uniform(0, math.pi * 2)
        self.WIDTH = 40
        self.HEIGHT = 24

    def update(self, dt, player_world_x, platforms):
        if not self.alive:
            return
        self._anim_t += dt
        self.world_x += self.vel_x * self._dir * dt * 60
        self._walk_timer = getattr(self, '_walk_timer', 0) + dt
        if self._walk_timer > 3.0:
            self._walk_timer = 0
            self._dir *= -1
        # Sine wave flight
        self.world_y = self._origin_y + math.sin(self._anim_t * 2 + self._sine_offset) * 40

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        flap = int(8 * math.sin(self._anim_t * 8))
        # Wings
        wing_col = (90, 30, 110)
        pygame.draw.polygon(surface, wing_col, [
            (sx, sy + 10), (sx - 22, sy - 5 + flap), (sx - 12, sy + 14)
        ])
        pygame.draw.polygon(surface, wing_col, [
            (sx, sy + 10), (sx + 22, sy - 5 + flap), (sx + 12, sy + 14)
        ])
        # Body
        pygame.draw.ellipse(surface, (70, 20, 90), (sx - 8, sy + 3, 16, 14))
        # Eyes
        pygame.draw.circle(surface, (220, 60, 60), (sx - 4, sy + 8), 3)
        pygame.draw.circle(surface, (220, 60, 60), (sx + 4, sy + 8), 3)
        # Ears
        pygame.draw.polygon(surface, (90, 30, 110), [
            (sx - 6, sy + 3), (sx - 9, sy - 5), (sx - 2, sy + 3)
        ])
        pygame.draw.polygon(surface, (90, 30, 110), [
            (sx + 6, sy + 3), (sx + 9, sy - 5), (sx + 2, sy + 3)
        ])


# ---------------------------------------------------------------------------
class ArmoredCrab(_BaseEnemy):
    POINTS = 200

    def __init__(self, world_x, world_y, speed=1.0):
        super().__init__(world_x, world_y, 2, speed * 1.3)
        self.WIDTH = 48
        self.HEIGHT = 34
        self._flash = 0

    def hit(self):
        self.health -= 1
        self._flash = 10
        if self.health <= 0:
            self.alive = False

    def update(self, dt, player_world_x, platforms):
        if not self.alive:
            return
        self._anim_t += dt
        # Chase player slowly
        dx = player_world_x - self.world_x
        self._dir = 1 if dx > 0 else -1
        self.world_x += self.vel_x * self._dir * dt * 60
        self._apply_gravity_and_platforms(platforms)
        if self._flash > 0:
            self._flash -= 1

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        body_col = (220, 80, 30) if self._flash % 2 == 0 else (255, 200, 150)
        # Shell highlight
        shell_col = (240, 120, 40) if self.health == 2 else (180, 80, 20)
        # Body
        pygame.draw.ellipse(surface, body_col, (sx - 22, sy + 4, 44, 28))
        pygame.draw.ellipse(surface, shell_col, (sx - 16, sy, 32, 20))
        # Claws
        claw_bob = int(3 * math.sin(self._anim_t * 4))
        pygame.draw.ellipse(surface, body_col, (sx - 38, sy + 8 + claw_bob, 18, 12))
        pygame.draw.ellipse(surface, body_col, (sx + 20, sy + 8 - claw_bob, 18, 12))
        # Eyes on stalks
        pygame.draw.line(surface, body_col, (sx - 8, sy + 2), (sx - 10, sy - 6), 2)
        pygame.draw.circle(surface, (10, 10, 10), (sx - 10, sy - 8), 4)
        pygame.draw.line(surface, body_col, (sx + 8, sy + 2), (sx + 10, sy - 6), 2)
        pygame.draw.circle(surface, (10, 10, 10), (sx + 10, sy - 8), 4)
        # Health dots
        for i in range(self.health):
            pygame.draw.circle(surface, (255, 50, 50), (sx - 5 + i * 10, sy - 16), 4)


# ---------------------------------------------------------------------------
class Boulder(_BaseEnemy):
    POINTS = 250

    def __init__(self, world_x, world_y, speed=1.0):
        super().__init__(world_x, world_y, 1, speed * 0.7)
        self._rotation = 0.0
        self.WIDTH = 40
        self.HEIGHT = 40

    def update(self, dt, player_world_x, platforms):
        if not self.alive:
            return
        # Roll toward player
        dx = player_world_x - self.world_x
        self._dir = 1 if dx > 0 else -1
        self.world_x += self.vel_x * self._dir * dt * 60
        self._apply_gravity_and_platforms(platforms)
        self._rotation += self.vel_x * self._dir * dt * 3

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        r = 18
        # Main circle
        pygame.draw.circle(surface, (130, 110, 90), (sx, sy + r), r)
        pygame.draw.circle(surface, (160, 140, 115), (sx, sy + r), r - 4)
        # Rock texture lines (rotate with movement)
        for i in range(4):
            angle = self._rotation + i * math.pi / 2
            x1 = sx + int((r - 4) * math.cos(angle))
            y1 = sy + r + int((r - 4) * math.sin(angle))
            x2 = sx + int((r // 2) * math.cos(angle + math.pi))
            y2 = sy + r + int((r // 2) * math.sin(angle + math.pi))
            pygame.draw.line(surface, (90, 70, 55), (x1, y1), (x2, y2), 2)
        # Shine
        pygame.draw.circle(surface, (185, 165, 140), (sx - 5, sy + r - 7), 5)
