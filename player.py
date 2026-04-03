"""Player – the orange fox Kitsune."""
import pygame
import math
from constants import (
    GRAVITY, JUMP_FORCE, MAX_FALL_SPEED, PLAYER_SPEED,
    GROUND_Y, INVINCIBILITY_DURATION, MAX_LIVES, WEAPON_NAMES, SCREEN_WIDTH
)


class Player:
    WIDTH = 36
    HEIGHT = 50

    def __init__(self, world_x=100, world_y=None):
        self.world_x = float(world_x)
        self.world_y = float(world_y if world_y is not None else GROUND_Y - self.HEIGHT)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.lives = MAX_LIVES
        self.score = 0
        self.weapon = 0
        self.ammo = {'Spread': 20, 'Bounce': 15, 'Homing': 10, 'Laser': 8, 'Bomb': 6}
        self.invincible_timer = 0
        self.health = 1
        self.anim_frame = 0
        self._anim_counter = 0
        self._shoot_cooldown = 0
        self._jump_held = False
        self._jump_buffer = 0
        self._coyote_time = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def rect(self):
        return pygame.Rect(
            int(self.world_x - self.WIDTH // 2),
            int(self.world_y),
            self.WIDTH,
            self.HEIGHT
        )

    def get_world_rect(self):
        return self.rect

    # ------------------------------------------------------------------
    def jump(self):
        if self.on_ground or self._coyote_time > 0:
            self.vel_y = JUMP_FORCE
            self.on_ground = False
            self._coyote_time = 0
            return True
        if self._jump_buffer == 0:
            self._jump_buffer = 8
        return False

    def _get_current_weapon_name(self):
        return WEAPON_NAMES[self.weapon]

    def shoot(self):
        """Return list of new projectile dicts for game.py to instantiate."""
        if self._shoot_cooldown > 0:
            return []
        wname = self._get_current_weapon_name()
        # Consume ammo for non-normal weapons
        if wname != 'Normal':
            if self.ammo.get(wname, 0) <= 0:
                self.weapon = 0
                wname = 'Normal'
            else:
                self.ammo[wname] -= 1

        self._shoot_cooldown = 12 if wname == 'Normal' else 18
        cx = self.world_x + (20 if self.facing_right else -20)
        cy = self.world_y + self.HEIGHT // 3

        return [{'type': wname, 'x': cx, 'y': cy, 'dir': 1 if self.facing_right else -1}]

    # ------------------------------------------------------------------
    def update(self, platforms, dt, keys=None):
        # Input
        if keys:
            if keys[pygame.K_RIGHT]:
                self.vel_x = PLAYER_SPEED
                self.facing_right = True
            elif keys[pygame.K_LEFT]:
                self.vel_x = -PLAYER_SPEED
                self.facing_right = False
            else:
                self.vel_x *= 0.75

        # Gravity
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)

        # Move X
        self.world_x += self.vel_x
        self.world_x = max(self.WIDTH // 2, self.world_x)

        # Move Y
        prev_y = self.world_y
        self.world_y += self.vel_y
        self.on_ground = False

        # Platform collisions
        prect = self.rect
        for plat in platforms:
            if prect.colliderect(plat):
                # Landing on top
                if self.vel_y > 0 and prev_y + self.HEIGHT <= plat.top + 8:
                    self.world_y = plat.top - self.HEIGHT
                    self.vel_y = 0
                    self.on_ground = True
                    if self._jump_buffer > 0:
                        self.vel_y = JUMP_FORCE
                        self.on_ground = False
                        self._jump_buffer = 0
                # Hitting ceiling
                elif self.vel_y < 0 and prev_y >= plat.bottom - 8:
                    self.world_y = plat.bottom
                    self.vel_y = 0

        # Ground
        ground_plat_y = GROUND_Y
        if self.world_y + self.HEIGHT >= ground_plat_y:
            self.world_y = ground_plat_y - self.HEIGHT
            self.vel_y = 0
            self.on_ground = True
            if self._jump_buffer > 0:
                self.vel_y = JUMP_FORCE
                self.on_ground = False
                self._jump_buffer = 0

        # Coyote time
        if self.on_ground:
            self._coyote_time = 6
        else:
            self._coyote_time = max(0, self._coyote_time - 1)

        # Timers
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1
        if self._jump_buffer > 0:
            self._jump_buffer -= 1

        # Animation
        self._anim_counter += 1
        if abs(self.vel_x) > 0.5 and self.on_ground:
            if self._anim_counter >= 8:
                self._anim_counter = 0
                self.anim_frame = (self.anim_frame + 1) % 4
        else:
            self.anim_frame = 0

    def take_damage(self):
        """Return True if the hit was registered (player is not invincible)."""
        if self.invincible_timer > 0:
            return False
        self.invincible_timer = INVINCIBILITY_DURATION
        return True

    def is_dead(self):
        return self.lives <= 0

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self, surface, camera_x):
        # Blink when invincible
        if self.invincible_timer > 0 and (self.invincible_timer // 5) % 2 == 0:
            return

        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        fr = self.facing_right
        jumping = not self.on_ground
        running = abs(self.vel_x) > 0.5 and self.on_ground

        # Tail
        self._draw_tail(surface, sx, sy, fr, jumping)

        # Body
        body_color = (230, 110, 30)
        body_rect = pygame.Rect(sx - 18, sy + 16, 36, 30)
        pygame.draw.ellipse(surface, body_color, body_rect)
        # White belly
        pygame.draw.ellipse(surface, (255, 235, 210), (sx - 10, sy + 22, 20, 20))

        # Legs
        self._draw_legs(surface, sx, sy, fr, running, jumping)

        # Head
        hx = sx + (4 if fr else -4)
        hy = sy + 2
        head_color = (235, 115, 35)
        pygame.draw.circle(surface, head_color, (hx, hy + 14), 17)

        # Ears
        ear_col = (235, 115, 35)
        ear_inner = (240, 160, 160)
        ear_tilt = -5 if jumping else 0
        if fr:
            # Left ear
            pygame.draw.polygon(surface, ear_col, [
                (hx - 12, hy + 1),
                (hx - 5, hy - 16 + ear_tilt),
                (hx + 2, hy + 1)
            ])
            pygame.draw.polygon(surface, ear_inner, [
                (hx - 10, hy + 1),
                (hx - 5, hy - 11 + ear_tilt),
                (hx + 0, hy + 1)
            ])
            # Right ear
            pygame.draw.polygon(surface, ear_col, [
                (hx + 6, hy + 1),
                (hx + 14, hy - 14 + ear_tilt),
                (hx + 18, hy + 3)
            ])
            pygame.draw.polygon(surface, ear_inner, [
                (hx + 8, hy + 1),
                (hx + 14, hy - 9 + ear_tilt),
                (hx + 16, hy + 3)
            ])
        else:
            pygame.draw.polygon(surface, ear_col, [
                (hx - 18, hy + 3),
                (hx - 14, hy - 14 + ear_tilt),
                (hx - 6, hy + 1)
            ])
            pygame.draw.polygon(surface, ear_inner, [
                (hx - 16, hy + 3),
                (hx - 14, hy - 9 + ear_tilt),
                (hx - 8, hy + 1)
            ])
            pygame.draw.polygon(surface, ear_col, [
                (hx - 2, hy + 1),
                (hx + 5, hy - 16 + ear_tilt),
                (hx + 12, hy + 1)
            ])
            pygame.draw.polygon(surface, ear_inner, [
                (hx - 0, hy + 1),
                (hx + 5, hy - 11 + ear_tilt),
                (hx + 10, hy + 1)
            ])

        # Eyes
        eye_ox = 6 if fr else -6
        # White of eye
        pygame.draw.circle(surface, (255, 255, 255), (hx + eye_ox, hy + 14), 6)
        # Pupil
        pygame.draw.circle(surface, (20, 20, 20), (hx + eye_ox, hy + 14), 4)
        # Glint
        pygame.draw.circle(surface, (255, 255, 255), (hx + eye_ox + 2, hy + 12), 2)
        # Cheek blush
        blush_col = (255, 180, 160)
        pygame.draw.ellipse(surface, blush_col, (hx + eye_ox - 4, hy + 19, 8, 5))

        # Nose
        pygame.draw.circle(surface, (255, 120, 130), (hx, hy + 22), 3)

        # Mouth smile
        pygame.draw.arc(surface, (180, 60, 60),
                        pygame.Rect(hx - 5, hy + 21, 10, 6), math.pi, 2 * math.pi, 2)

    def _draw_tail(self, surface, sx, sy, fr, jumping):
        tail_col = (235, 115, 35)
        tail_tip = (255, 245, 230)
        if jumping:
            # Fan out tail
            if fr:
                pts = [(sx - 10, sy + 30), (sx - 35, sy + 10),
                       (sx - 40, sy + 40), (sx - 20, sy + 50)]
            else:
                pts = [(sx + 10, sy + 30), (sx + 35, sy + 10),
                       (sx + 40, sy + 40), (sx + 20, sy + 50)]
        else:
            wave = int(4 * math.sin(self.anim_frame * 1.2))
            if fr:
                pts = [(sx - 8, sy + 32), (sx - 30, sy + 20 + wave),
                       (sx - 38, sy + 40 + wave), (sx - 18, sy + 52)]
            else:
                pts = [(sx + 8, sy + 32), (sx + 30, sy + 20 + wave),
                       (sx + 38, sy + 40 + wave), (sx + 18, sy + 52)]
        if len(pts) >= 3:
            pygame.draw.polygon(surface, tail_col, pts)
            # White tip
            tip_cx = (pts[1][0] + pts[2][0]) // 2
            tip_cy = (pts[1][1] + pts[2][1]) // 2
            pygame.draw.circle(surface, tail_tip, (tip_cx, tip_cy), 8)

    def _draw_legs(self, surface, sx, sy, fr, running, jumping):
        leg_col = (210, 95, 20)
        paw_col = (180, 70, 10)
        if jumping:
            # Tuck legs
            pygame.draw.rect(surface, leg_col, (sx - 12, sy + 40, 10, 12))
            pygame.draw.rect(surface, leg_col, (sx + 2, sy + 40, 10, 12))
            return
        offsets = [0, 4, 0, -4]
        leg_y_off = offsets[self.anim_frame] if running else 0
        # Left leg
        pygame.draw.rect(surface, leg_col, (sx - 13, sy + 40, 10, 14))
        pygame.draw.ellipse(surface, paw_col, (sx - 16, sy + 52 - leg_y_off, 14, 7))
        # Right leg
        pygame.draw.rect(surface, leg_col, (sx + 3, sy + 40, 10, 14))
        pygame.draw.ellipse(surface, paw_col, (sx + 2, sy + 52 + leg_y_off, 14, 7))
