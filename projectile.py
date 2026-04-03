"""Projectile types for Kitsune Adventure."""
import pygame
import math
import random
from constants import GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT


PROJ_SPEED = 9.0


class _BaseProjectile:
    def __init__(self, world_x, world_y, direction):
        self.world_x = float(world_x)
        self.world_y = float(world_y)
        self.direction = direction  # +1 or -1
        self.alive = True
        self._age = 0.0

    def _out_of_bounds(self):
        return (self.world_y > GROUND_Y + 100 or self.world_y < -200
                or self._age > 5.0)

    def update(self, dt, enemies, platforms):
        self._age += dt

    def draw(self, surface, camera_x):
        pass

    def _hit_enemies(self, enemies, damage_rect, damage=1):
        hit_any = False
        for e in enemies:
            if e.alive and e.get_rect().colliderect(damage_rect):
                e.hit()
                hit_any = True
        return hit_any


# ---------------------------------------------------------------------------
class NormalBullet(_BaseProjectile):
    R = 6

    def __init__(self, world_x, world_y, direction):
        super().__init__(world_x, world_y, direction)
        self.vel_x = PROJ_SPEED * 1.4 * direction
        self.vel_y = 0.0

    def update(self, dt, enemies, platforms):
        super().update(dt, enemies, platforms)
        self.world_x += self.vel_x * dt * 60
        if self._out_of_bounds():
            self.alive = False
            return
        r = pygame.Rect(int(self.world_x) - self.R, int(self.world_y) - self.R,
                        self.R * 2, self.R * 2)
        if self._hit_enemies(enemies, r):
            self.alive = False

    def draw(self, surface, camera_x):
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        pygame.draw.circle(surface, (255, 230, 50), (sx, sy), self.R)
        pygame.draw.circle(surface, (255, 255, 180), (sx - 1, sy - 1), self.R - 2)


# ---------------------------------------------------------------------------
class SpreadBullet(_BaseProjectile):
    R = 5
    ANGLES = [-15, 0, 15]  # degrees

    def __init__(self, world_x, world_y, direction, angle_deg=0):
        super().__init__(world_x, world_y, direction)
        rad = math.radians(angle_deg)
        spd = PROJ_SPEED * 1.2 * direction
        self.vel_x = spd * math.cos(rad)
        self.vel_y = spd * math.sin(rad)

    def update(self, dt, enemies, platforms):
        super().update(dt, enemies, platforms)
        self.world_x += self.vel_x * dt * 60
        self.world_y += self.vel_y * dt * 60
        if self._out_of_bounds():
            self.alive = False
            return
        r = pygame.Rect(int(self.world_x) - self.R, int(self.world_y) - self.R,
                        self.R * 2, self.R * 2)
        if self._hit_enemies(enemies, r):
            self.alive = False

    def draw(self, surface, camera_x):
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        pygame.draw.circle(surface, (50, 220, 255), (sx, sy), self.R)
        pygame.draw.circle(surface, (180, 245, 255), (sx - 1, sy - 1), self.R - 2)


# ---------------------------------------------------------------------------
class BounceBullet(_BaseProjectile):
    R = 7
    MAX_BOUNCES = 3

    def __init__(self, world_x, world_y, direction):
        super().__init__(world_x, world_y, direction)
        self.vel_x = PROJ_SPEED * direction
        self.vel_y = -4.0
        self._bounces = 0

    def update(self, dt, enemies, platforms):
        super().update(dt, enemies, platforms)
        self.vel_y += 0.4  # gravity
        self.world_x += self.vel_x * dt * 60
        self.world_y += self.vel_y * dt * 60
        # Bounce off ground
        if self.world_y + self.R >= GROUND_Y:
            self.world_y = GROUND_Y - self.R
            self.vel_y = -abs(self.vel_y) * 0.75
            self._bounces += 1
        # Bounce off platforms
        for plat in platforms:
            pr = pygame.Rect(int(self.world_x) - self.R, int(self.world_y) - self.R,
                             self.R * 2, self.R * 2)
            if pr.colliderect(plat) and self.vel_y > 0:
                self.world_y = plat.top - self.R
                self.vel_y = -abs(self.vel_y) * 0.75
                self._bounces += 1
        if self._bounces >= self.MAX_BOUNCES or self._out_of_bounds():
            self.alive = False
            return
        r = pygame.Rect(int(self.world_x) - self.R, int(self.world_y) - self.R,
                        self.R * 2, self.R * 2)
        if self._hit_enemies(enemies, r):
            self.alive = False

    def draw(self, surface, camera_x):
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        pygame.draw.circle(surface, (60, 200, 60), (sx, sy), self.R)
        pygame.draw.circle(surface, (180, 255, 180), (sx - 1, sy - 1), self.R - 3)
        # Trail dot
        tx = sx - int(self.vel_x * 0.5)
        ty = sy - int(self.vel_y * 0.5)
        pygame.draw.circle(surface, (60, 200, 60, 100), (tx, ty), self.R - 3)


# ---------------------------------------------------------------------------
class HomingMissile(_BaseProjectile):
    R = 6

    def __init__(self, world_x, world_y, direction):
        super().__init__(world_x, world_y, direction)
        self.vel_x = PROJ_SPEED * 0.9 * direction
        self.vel_y = 0.0
        self._trail = []

    def update(self, dt, enemies, platforms):
        super().update(dt, enemies, platforms)
        # Steer toward nearest alive enemy
        nearest = None
        nearest_dist = 800
        for e in enemies:
            if e.alive:
                d = math.hypot(e.world_x - self.world_x, e.world_y - self.world_x)
                dist = math.hypot(e.world_x - self.world_x, e.world_y + 18 - self.world_y)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = e
        if nearest:
            dx = nearest.world_x - self.world_x
            dy = (nearest.world_y + 18) - self.world_y
            dist = math.hypot(dx, dy) or 1
            target_vx = dx / dist * PROJ_SPEED
            target_vy = dy / dist * PROJ_SPEED
            steer = 4.0 * dt
            self.vel_x += (target_vx - self.vel_x) * steer
            self.vel_y += (target_vy - self.vel_y) * steer
        self._trail.append((self.world_x, self.world_y))
        if len(self._trail) > 8:
            self._trail.pop(0)
        self.world_x += self.vel_x * dt * 60
        self.world_y += self.vel_y * dt * 60
        if self._out_of_bounds():
            self.alive = False
            return
        r = pygame.Rect(int(self.world_x) - self.R, int(self.world_y) - self.R,
                        self.R * 2, self.R * 2)
        if self._hit_enemies(enemies, r):
            self.alive = False

    def draw(self, surface, camera_x):
        for i, (tx, ty) in enumerate(self._trail):
            alpha = int(255 * (i / len(self._trail)))
            sx2 = int(tx - camera_x)
            sy2 = int(ty)
            r = max(1, self.R - 3 + i // 2)
            col = (alpha // 2, 0, alpha)
            pygame.draw.circle(surface, col, (sx2, sy2), r)
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        angle = math.atan2(self.vel_y, self.vel_x)
        tip = (sx + int(12 * math.cos(angle)), sy + int(12 * math.sin(angle)))
        left = (sx + int(6 * math.cos(angle + 2.2)), sy + int(6 * math.sin(angle + 2.2)))
        right = (sx + int(6 * math.cos(angle - 2.2)), sy + int(6 * math.sin(angle - 2.2)))
        pygame.draw.polygon(surface, (180, 50, 255), [tip, left, right])


# ---------------------------------------------------------------------------
class LaserBeam(_BaseProjectile):
    DURATION = 0.35

    def __init__(self, world_x, world_y, direction, platforms=None):
        super().__init__(world_x, world_y, direction)
        self._life = self.DURATION
        self._hit_x = world_x + direction * 1400  # default full range
        # Raycast against enemies will happen in update immediately
        self._initial_x = world_x
        self._dir = direction

    def update(self, dt, enemies, platforms):
        super().update(dt, enemies, platforms)
        self._life -= dt
        if self._life <= 0:
            self.alive = False
            return
        # Hit all enemies along beam on first frame
        if self._age <= dt * 2:
            beam_rect = pygame.Rect(
                min(self._initial_x, self._hit_x),
                int(self.world_y) - 6,
                abs(self._hit_x - self._initial_x),
                12
            )
            self._hit_enemies(enemies, beam_rect)

    def draw(self, surface, camera_x):
        alpha = self._life / self.DURATION
        sx_start = int(self._initial_x - camera_x)
        sx_end = int(self._hit_x - camera_x)
        sy = int(self.world_y)
        # Glow layers
        for width, col in [(10, (255, 50, 50, int(60 * alpha))),
                           (6, (255, 100, 50, int(120 * alpha))),
                           (3, (255, 220, 200, int(255 * alpha)))]:
            try:
                glow = pygame.Surface((SCREEN_WIDTH, width * 2), pygame.SRCALPHA)
                pygame.draw.line(glow, col, (sx_start, width), (sx_end, width), width)
                surface.blit(glow, (0, sy - width))
            except Exception:
                pygame.draw.line(surface, (255, 100, 50), (sx_start, sy), (sx_end, sy), 3)


# ---------------------------------------------------------------------------
class Bomb(_BaseProjectile):
    R = 9
    EXPLODE_R = 70

    def __init__(self, world_x, world_y, direction):
        super().__init__(world_x, world_y, direction)
        self.vel_x = PROJ_SPEED * 0.7 * direction
        self.vel_y = -10.0
        self._exploding = False
        self._explode_timer = 0.0
        self._explode_max = 0.5

    def update(self, dt, enemies, platforms):
        super().update(dt, enemies, platforms)
        if self._exploding:
            self._explode_timer += dt
            if self._explode_timer >= self._explode_max:
                self.alive = False
            return
        self.vel_y += 0.5
        self.world_x += self.vel_x * dt * 60
        self.world_y += self.vel_y * dt * 60
        # Check hit ground
        hit_ground = False
        if self.world_y + self.R >= GROUND_Y:
            hit_ground = True
        for plat in platforms:
            pr = pygame.Rect(int(self.world_x) - self.R, int(self.world_y) - self.R,
                             self.R * 2, self.R * 2)
            if pr.colliderect(plat):
                hit_ground = True
        if hit_ground or self._age > 3.0:
            self._start_explosion(enemies)
            return
        # Direct hit
        r = pygame.Rect(int(self.world_x) - self.R, int(self.world_y) - self.R,
                        self.R * 2, self.R * 2)
        if self._hit_enemies(enemies, r):
            self._start_explosion(enemies)

    def _start_explosion(self, enemies):
        self._exploding = True
        explode_rect = pygame.Rect(
            int(self.world_x) - self.EXPLODE_R, int(self.world_y) - self.EXPLODE_R,
            self.EXPLODE_R * 2, self.EXPLODE_R * 2
        )
        self._hit_enemies(enemies, explode_rect)

    def draw(self, surface, camera_x):
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        if self._exploding:
            prog = self._explode_timer / self._explode_max
            r = int(self.EXPLODE_R * prog)
            alpha = int(255 * (1 - prog))
            # Explosion rings
            if r > 0:
                exp_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(exp_surf, (255, 180, 0, alpha),
                                   (r + 2, r + 2), r)
                pygame.draw.circle(exp_surf, (255, 80, 0, alpha // 2),
                                   (r + 2, r + 2), max(1, r - 10))
                surface.blit(exp_surf, (sx - r - 2, sy - r - 2))
        else:
            # Bomb body
            pygame.draw.circle(surface, (60, 60, 60), (sx, sy), self.R)
            pygame.draw.circle(surface, (90, 90, 90), (sx - 2, sy - 2), self.R - 3)
            # Fuse
            fuse_anim = int(self._age * 6) % 2
            fuse_col = (255, 200, 0) if fuse_anim else (255, 100, 0)
            pygame.draw.line(surface, (80, 50, 20), (sx, sy - self.R), (sx + 4, sy - self.R - 8), 2)
            pygame.draw.circle(surface, fuse_col, (sx + 4, sy - self.R - 8), 3)


# ---------------------------------------------------------------------------
def create_projectiles(proj_data):
    """Factory function: create projectile(s) from a dict returned by player.shoot()."""
    ptype = proj_data['type']
    x = proj_data['x']
    y = proj_data['y']
    d = proj_data['dir']
    if ptype == 'Normal':
        return [NormalBullet(x, y, d)]
    elif ptype == 'Spread':
        projs = []
        for angle in [-15, 0, 15]:
            projs.append(SpreadBullet(x, y, d, angle * d))
        return projs
    elif ptype == 'Bounce':
        return [BounceBullet(x, y, d)]
    elif ptype == 'Homing':
        return [HomingMissile(x, y, d)]
    elif ptype == 'Laser':
        return [LaserBeam(x, y, d)]
    elif ptype == 'Bomb':
        return [Bomb(x, y, d)]
    return []
