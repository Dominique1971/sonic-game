"""Main Game class – Kitsune Adventure."""
import pygame
import sys
import math
import random

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    MAX_LIVES, WEAPON_NAMES, LEVELS, GROUND_Y, INVINCIBILITY_DURATION
)
from player import Player
from level import Level
from projectile import create_projectiles
from sound import SoundManager
from powerup import GemPickup, WeaponPickup, HeartPickup, ShieldPickup


# ---------------------------------------------------------------------------
# Particle
# ---------------------------------------------------------------------------
class Particle:
    def __init__(self, world_x, world_y, vx, vy, color, life, r=3):
        self.world_x = float(world_x)
        self.world_y = float(world_y)
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.r = r
        self.alive = True

    def update(self, dt):
        self.world_x += self.vx * dt * 60
        self.world_y += self.vy * dt * 60
        self.vy += 0.2
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x)
        sy = int(self.world_y)
        if -20 < sx < SCREEN_WIDTH + 20:
            alpha_r = max(0, self.life / self.max_life)
            r = max(1, int(self.r * alpha_r))
            c = tuple(int(ch * alpha_r) for ch in self.color[:3])
            pygame.draw.circle(surface, c, (sx, sy), r)


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont('Arial', 72, bold=True)
        self.font_med = pygame.font.SysFont('Arial', 36, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 22)
        self.font_tiny = pygame.font.SysFont('Arial', 16)
        self.sound = SoundManager()
        self.state = 'menu'
        self.current_level_idx = 0
        self.player = None
        self.level = None
        self.projectiles = []
        self.camera_x = 0.0
        self.particles = []
        self._level_name_timer = 0.0
        self._menu_anim = 0.0
        self._complete_timer = 0.0
        self._gameover_timer = 0.0
        self._selected_option = 0  # for menu
        self._persistent_score = 0  # score carries across levels
        self._saved_lives = MAX_LIVES

    # ------------------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # cap dt to avoid spiral of death
            self._handle_events()
            self._update(dt)
            self._draw()

    # ------------------------------------------------------------------
    def _start_level(self, level_idx):
        self.current_level_idx = level_idx
        data = LEVELS[level_idx]
        self.level = Level(data)
        if self.player is None:
            self.player = Player(world_x=120)
            self.player.score = self._persistent_score
            self.player.lives = self._saved_lives
        else:
            wx = 120
            self.player.world_x = wx
            self.player.world_y = GROUND_Y - Player.HEIGHT
            self.player.vel_x = 0
            self.player.vel_y = 0
            self.player.invincible_timer = INVINCIBILITY_DURATION
        self.projectiles = []
        self.particles = []
        self.camera_x = 0.0
        self._level_name_timer = 3.0
        self.state = 'playing'
        self.sound.play_music(data['theme'])

    def _respawn_player(self):
        self.player.world_x = 120
        self.player.world_y = GROUND_Y - Player.HEIGHT
        self.player.vel_x = 0
        self.player.vel_y = 0
        self.player.invincible_timer = INVINCIBILITY_DURATION * 2
        self.projectiles = []

    # ------------------------------------------------------------------
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)

    def _handle_key(self, key):
        if self.state == 'menu':
            if key == pygame.K_RETURN or key == pygame.K_SPACE:
                self._persistent_score = 0
                self._saved_lives = MAX_LIVES
                self.player = None
                self._start_level(0)
            if key == pygame.K_m:
                self.sound.toggle()

        elif self.state == 'playing':
            if key == pygame.K_SPACE or key == pygame.K_UP:
                if self.player:
                    jumped = self.player.jump()
                    if jumped:
                        self.sound.play('jump')
            if key == pygame.K_RETURN:
                if self.player:
                    proj_data_list = self.player.shoot()
                    for pd in proj_data_list:
                        new_projs = create_projectiles(pd)
                        self.projectiles.extend(new_projs)
                        if new_projs:
                            wname = pd['type']
                            self.sound.play(f'shoot_{wname.lower()}')
            if key == pygame.K_p:
                self.state = 'paused'
            if key == pygame.K_ESCAPE:
                self.state = 'menu'
                self.sound.stop_music()

        elif self.state == 'paused':
            if key == pygame.K_p or key == pygame.K_ESCAPE:
                self.state = 'playing'

        elif self.state == 'level_complete':
            if self._complete_timer <= 0:
                if key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._advance_level()

        elif self.state == 'game_over':
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = 'menu'
                self.player = None
                self.sound.stop_music()

        elif self.state == 'victory':
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = 'menu'
                self.player = None
                self.sound.stop_music()

    # ------------------------------------------------------------------
    def _update(self, dt):
        self._menu_anim += dt
        if self.state == 'playing':
            self._update_game(dt)
        elif self.state == 'level_complete':
            self._complete_timer = max(0, self._complete_timer - dt)
        elif self.state == 'game_over':
            self._gameover_timer = max(0, self._gameover_timer - dt)

    def _update_game(self, dt):
        if not self.player or not self.level:
            return

        keys = pygame.key.get_pressed()
        self.player.update(self.level.platforms, dt, keys)

        # Update level
        self.level.update(self.camera_x, self.player, dt)

        # Update projectiles
        alive_projs = []
        for proj in self.projectiles:
            proj.update(dt, self.level.enemies, self.level.platforms)
            if proj.alive:
                alive_projs.append(proj)
            else:
                # Spawn hit particles
                from projectile import Bomb
                if isinstance(proj, Bomb) and proj._exploding:
                    self._spawn_particles(proj.world_x, proj.world_y,
                                         (255, 150, 0), 20, 5)
        self.projectiles = alive_projs

        # Update particles
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

        # Smooth camera
        target_cam = self.player.world_x - SCREEN_WIDTH * 0.35
        target_cam = max(0, min(target_cam, self.level.world_width - SCREEN_WIDTH))
        self.camera_x += (target_cam - self.camera_x) * 0.12

        # Check collisions
        self._check_collisions()

        # Level name banner timer
        if self._level_name_timer > 0:
            self._level_name_timer -= dt

        # Check level goal
        if self.player.world_x >= self.level.goal_x:
            self._level_complete()

        # Check player fell off
        if self.player.world_y > GROUND_Y + 200:
            self._player_die()

    def _check_collisions(self):
        if not self.player:
            return
        player_rect = self.player.get_world_rect()

        # Player vs enemies
        for e in self.level.enemies:
            if not e.alive:
                continue
            if player_rect.colliderect(e.get_rect()):
                if self.player.invincible_timer <= 0:
                    died = self.player.take_damage()
                    self.sound.play('player_hurt')
                    self._spawn_particles(
                        self.player.world_x, self.player.world_y + 20,
                        (255, 100, 50), 15, 4
                    )
                    if died:
                        self._player_die()
                        return

        # Player vs powerups
        for p in self.level.powerups:
            if not p.alive:
                continue
            if player_rect.colliderect(p.get_rect()):
                self._collect_powerup(p)

        # Projectiles vs enemies – scoring
        for e in self.level.enemies:
            if not e.alive and e.health <= 0:
                if hasattr(e, '_scored') and not e._scored:
                    e._scored = True
                    pts = getattr(e.__class__, 'POINTS', 100)
                    self.player.score += pts
                    self.sound.play('enemy_die')
                    self._spawn_particles(
                        e.world_x, e.world_y + 15,
                        (255, 220, 0), 12, 3
                    )

    def _collect_powerup(self, p):
        p.alive = False
        if isinstance(p, GemPickup):
            self.player.score += GemPickup.POINTS
            self.sound.play('collect_gem')
            self._spawn_particles(p.world_x, p.world_y, (255, 215, 0), 8, 3)
        elif isinstance(p, WeaponPickup):
            self.player.weapon = p.weapon_index
            # Refill ammo
            wname = WEAPON_NAMES[p.weapon_index]
            base_ammo = {'Spread': 20, 'Bounce': 15, 'Homing': 10, 'Laser': 8, 'Bomb': 6}
            if wname in base_ammo:
                self.player.ammo[wname] = self.player.ammo.get(wname, 0) + base_ammo[wname]
            self._spawn_particles(p.world_x, p.world_y, (180, 100, 255), 8, 3)
        elif isinstance(p, HeartPickup):
            self.player.lives = min(MAX_LIVES, self.player.lives + 1)
            self.sound.play('collect_gem')
            self._spawn_particles(p.world_x, p.world_y, (255, 80, 80), 10, 3)
        elif isinstance(p, ShieldPickup):
            self.player.invincible_timer = max(
                self.player.invincible_timer, INVINCIBILITY_DURATION * 2 + 60)
            self._spawn_particles(p.world_x, p.world_y, (50, 150, 255), 10, 3)

    def _player_die(self):
        self.player.lives -= 1
        self._spawn_particles(
            self.player.world_x, self.player.world_y + 20,
            (255, 60, 60), 25, 5
        )
        if self.player.lives < 0:
            self.sound.play('game_over')
            self.sound.stop_music()
            self.state = 'game_over'
            self._gameover_timer = 1.0
        else:
            self._respawn_player()

    def _level_complete(self):
        self._persistent_score = self.player.score
        self._saved_lives = self.player.lives
        self.sound.play('level_up')
        self.state = 'level_complete'
        self._complete_timer = 2.0

    def _advance_level(self):
        next_idx = self.current_level_idx + 1
        if next_idx >= len(LEVELS):
            self.sound.stop_music()
            self.state = 'victory'
        else:
            self._start_level(next_idx)

    def _spawn_particles(self, world_x, world_y, color, count=10, r=3):
        for _ in range(count):
            vx = random.uniform(-3, 3)
            vy = random.uniform(-5, -1)
            life = random.uniform(0.4, 1.0)
            self.particles.append(Particle(world_x, world_y, vx, vy, color, life, r))

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _draw(self):
        if self.state == 'menu':
            self._draw_menu()
        elif self.state == 'playing':
            self._draw_game()
        elif self.state == 'paused':
            self._draw_game()
            self._draw_pause_overlay()
        elif self.state == 'level_complete':
            self._draw_game()
            self._draw_level_complete()
        elif self.state == 'game_over':
            self._draw_game_over()
        elif self.state == 'victory':
            self._draw_victory()
        pygame.display.flip()

    def _draw_game(self):
        self.screen.fill((0, 0, 0))
        if self.level:
            self.level.draw(self.screen, int(self.camera_x))
        for proj in self.projectiles:
            proj.draw(self.screen, int(self.camera_x))
        for p in self.particles:
            p.draw(self.screen, int(self.camera_x))
        if self.player:
            self.player.draw(self.screen, int(self.camera_x))
        self._draw_hud()
        if self._level_name_timer > 0:
            self._draw_level_banner()

    def _draw_hud(self):
        if not self.player:
            return
        # Score
        score_surf = self.font_med.render(f'SCORE  {self.player.score:07d}', True, (255, 255, 255))
        self._draw_text_shadow(self.screen, self.font_med,
                                f'SCORE  {self.player.score:07d}', SCREEN_WIDTH // 2, 12)

        # Lives (heart icons)
        for i in range(max(0, self.player.lives + 1)):
            hx = 20 + i * 32
            hy = 18
            s = 9
            pygame.draw.circle(self.screen, (240, 60, 80), (hx - s // 2, hy - 2), s // 2 + 1)
            pygame.draw.circle(self.screen, (240, 60, 80), (hx + s // 2, hy - 2), s // 2 + 1)
            pygame.draw.polygon(self.screen, (240, 60, 80), [
                (hx - s, hy - 2), (hx + s, hy - 2), (hx, hy + s - 2)
            ])

        # Weapon
        wname = WEAPON_NAMES[self.player.weapon]
        if wname == 'Normal':
            ammo_str = '∞'
        else:
            ammo_str = str(self.player.ammo.get(wname, 0))
        from powerup import WEAPON_COLORS
        wcol = WEAPON_COLORS.get(wname, (255, 255, 255))
        wlbl = self.font_small.render(f'[{wname}] {ammo_str}', True, wcol)
        self.screen.blit(wlbl, (SCREEN_WIDTH - wlbl.get_width() - 12, 10))

        # Level
        if self.level:
            lvl_lbl = self.font_tiny.render(
                f'Level {self.current_level_idx + 1}: {self.level.data["name"]}',
                True, (220, 220, 220))
            self.screen.blit(lvl_lbl, (SCREEN_WIDTH - lvl_lbl.get_width() - 12, 38))

        # Controls reminder (very small)
        hint = self.font_tiny.render('←→ Move  ↑/Space Jump  Enter Shoot  P Pause', True, (160, 160, 160))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 22))

    def _draw_text_shadow(self, surface, font, text, x, y, color=(255, 255, 255), shadow=(0, 0, 0)):
        s = font.render(text, True, shadow)
        surface.blit(s, (x - s.get_width() // 2 + 2, y + 2))
        s2 = font.render(text, True, color)
        surface.blit(s2, (x - s2.get_width() // 2, y))

    def _draw_level_banner(self):
        alpha = min(1.0, self._level_name_timer) * min(1.0, 3.0 - self._level_name_timer) / 1.0
        alpha = max(0, min(1, alpha))
        banner = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
        banner.fill((0, 0, 0, int(160 * alpha)))
        self.screen.blit(banner, (0, SCREEN_HEIGHT // 2 - 40))
        name = self.level.data['name'] if self.level else ''
        lbl = self.font_med.render(f'Level {self.current_level_idx + 1} – {name}',
                                    True, (255, 230, 100))
        lbl.set_alpha(int(255 * alpha))
        self.screen.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2,
                                SCREEN_HEIGHT // 2 - lbl.get_height() // 2))

    def _draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 40, 160))
        self.screen.blit(overlay, (0, 0))
        self._draw_text_shadow(self.screen, self.font_large, 'PAUSED',
                                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
                                (255, 240, 100))
        hint = self.font_small.render('Press P to resume', True, (200, 200, 200))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                 SCREEN_HEIGHT // 2 + 30))

    def _draw_level_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 40, 0, 180))
        self.screen.blit(overlay, (0, 0))
        self._draw_text_shadow(self.screen, self.font_large, 'LEVEL COMPLETE!',
                                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70,
                                (100, 255, 100))
        sc = self.font_med.render(f'Score: {self.player.score:07d}', True, (255, 230, 50))
        self.screen.blit(sc, (SCREEN_WIDTH // 2 - sc.get_width() // 2,
                               SCREEN_HEIGHT // 2))
        if self._complete_timer <= 0:
            cont = self.font_small.render('Press ENTER to continue', True, (200, 255, 200))
            if int(self._menu_anim * 2) % 2 == 0:
                self.screen.blit(cont, (SCREEN_WIDTH // 2 - cont.get_width() // 2,
                                         SCREEN_HEIGHT // 2 + 60))

    def _draw_game_over(self):
        self.screen.fill((20, 5, 5))
        # Animated background
        for i in range(12):
            angle = self._menu_anim * 0.5 + i * math.pi / 6
            r = 250 + 50 * math.sin(angle)
            x = SCREEN_WIDTH // 2 + int(r * math.cos(angle))
            y = SCREEN_HEIGHT // 2 + int(r * math.sin(angle))
            pygame.draw.circle(self.screen, (80, 10, 10), (x, y), 8)

        self._draw_text_shadow(self.screen, self.font_large, 'GAME OVER',
                                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80,
                                (255, 60, 60), (100, 0, 0))
        if self.player:
            sc = self.font_med.render(f'Final Score: {self.player.score:07d}', True, (255, 200, 100))
            self.screen.blit(sc, (SCREEN_WIDTH // 2 - sc.get_width() // 2,
                                   SCREEN_HEIGHT // 2 + 10))
        if self._gameover_timer <= 0:
            cont = self.font_small.render('Press ENTER to return to menu', True, (255, 150, 150))
            if int(self._menu_anim * 2) % 2 == 0:
                self.screen.blit(cont, (SCREEN_WIDTH // 2 - cont.get_width() // 2,
                                         SCREEN_HEIGHT // 2 + 80))

    def _draw_victory(self):
        # Rainbow background
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            hue = (t * 360 + self._menu_anim * 60) % 360
            r, g, b = self._hsv_to_rgb(hue, 0.6, 0.3)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Particles
        for p in self.particles:
            p.draw(self.screen, 0)

        self._draw_text_shadow(self.screen, self.font_large, 'YOU WIN!',
                                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100,
                                (255, 240, 80), (100, 80, 0))
        self._draw_text_shadow(self.screen, self.font_med, 'Kitsune Adventure Complete!',
                                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20,
                                (255, 255, 255))
        if self.player:
            sc = self.font_med.render(f'Final Score: {self.player.score:07d}', True, (255, 220, 60))
            self.screen.blit(sc, (SCREEN_WIDTH // 2 - sc.get_width() // 2,
                                   SCREEN_HEIGHT // 2 + 40))
        cont = self.font_small.render('Press ENTER to return to menu', True, (220, 255, 220))
        if int(self._menu_anim * 2) % 2 == 0:
            self.screen.blit(cont, (SCREEN_WIDTH // 2 - cont.get_width() // 2,
                                     SCREEN_HEIGHT // 2 + 110))
        # Victory sparkles
        if random.random() < 0.3:
            wx = random.uniform(0, SCREEN_WIDTH)
            wy = random.uniform(0, SCREEN_HEIGHT)
            col = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
            self._spawn_particles_screen(wx, wy, col, 5, 4)

    def _spawn_particles_screen(self, x, y, color, count, r):
        """Spawn particles in screen coords (used for victory screen)."""
        for _ in range(count):
            vx = random.uniform(-2, 2)
            vy = random.uniform(-3, -0.5)
            life = random.uniform(0.5, 1.2)
            self.particles.append(Particle(x, y, vx, vy, color, life, r))

    def _draw_menu(self):
        t = self._menu_anim
        # Sky gradient background
        for y in range(SCREEN_HEIGHT):
            frac = y / SCREEN_HEIGHT
            r = int(30 + 90 * frac + 20 * math.sin(t * 0.5 + frac * 3))
            g = int(10 + 50 * frac)
            b = int(80 + 100 * frac)
            pygame.draw.line(self.screen, (min(255, r), min(255, g), min(255, b)),
                             (0, y), (SCREEN_WIDTH, y))

        # Floating particles
        for i in range(20):
            px = int((i * 350 + t * 30 * (1 + i % 3 * 0.2)) % SCREEN_WIDTH)
            py = int((i * 150 + t * 15) % SCREEN_HEIGHT)
            brightness = int(150 + 80 * math.sin(t * 2 + i))
            pygame.draw.circle(self.screen, (brightness, brightness // 2, 255),
                               (px, py), 2 + i % 3)

        # Animated clouds
        for i in range(5):
            cx = int((i * 400 + t * 25) % (SCREEN_WIDTH + 200)) - 100
            cy = 80 + i * 60
            for dx, dy, r in [(-25, 0, 22), (0, -12, 28), (25, 0, 22), (12, 8, 18)]:
                pygame.draw.circle(self.screen, (200, 210, 255), (cx + dx, cy + dy), r)

        # Title shadow + glow
        title = 'KITSUNE ADVENTURE'
        for off in [(3, 3), (2, 2), (1, 1)]:
            t_surf = self.font_large.render(title, True, (100, 30, 0))
            self.screen.blit(t_surf, (SCREEN_WIDTH // 2 - t_surf.get_width() // 2 + off[0],
                                       80 + off[1]))
        title_surf = self.font_large.render(title, True, (255, 180, 40))
        glow_size = int(3 + 2 * math.sin(t * 2))
        for gs in range(glow_size, 0, -1):
            g_surf = self.font_large.render(title, True,
                                             (255, 100 + gs * 20, 0))
            g_surf.set_alpha(40)
            self.screen.blit(g_surf, (SCREEN_WIDTH // 2 - g_surf.get_width() // 2 + gs,
                                       80 + gs))
        self.screen.blit(title_surf,
                         (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 80))

        # Subtitle
        sub = self.font_small.render('A 2D Platformer Adventure', True, (200, 220, 255))
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 170))

        # Fox drawing on menu
        self._draw_menu_fox(SCREEN_WIDTH // 2, 290, t)

        # Press Enter blinking
        if int(t * 2) % 2 == 0:
            start_surf = self.font_med.render('Press ENTER to Start', True, (255, 240, 100))
            self.screen.blit(start_surf,
                             (SCREEN_WIDTH // 2 - start_surf.get_width() // 2, 430))

        # Controls
        controls = [
            '← → Arrow Keys: Move',
            '↑ / Space: Jump',
            'Enter: Shoot',
            'P: Pause    M: Toggle Music    ESC: Menu',
        ]
        for i, ctrl in enumerate(controls):
            c_surf = self.font_tiny.render(ctrl, True, (180, 200, 230))
            self.screen.blit(c_surf,
                             (SCREEN_WIDTH // 2 - c_surf.get_width() // 2, 510 + i * 22))

        # Level count info
        info = self.font_tiny.render('10 Levels  •  6 Weapons  •  5 Enemy Types', True, (150, 180, 210))
        self.screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, SCREEN_HEIGHT - 30))

    def _draw_menu_fox(self, cx, cy, t):
        """Draw an animated fox on the menu screen."""
        bob = int(6 * math.sin(t * 2))
        sy = cy + bob
        # Tail
        wave = int(8 * math.sin(t * 3))
        tail_pts = [(cx - 8, sy + 20), (cx - 30, sy + 5 + wave),
                    (cx - 38, sy + 28 + wave), (cx - 18, sy + 42)]
        if len(tail_pts) >= 3:
            pygame.draw.polygon(self.screen, (230, 110, 30), tail_pts)
            tip_cx = (tail_pts[1][0] + tail_pts[2][0]) // 2
            tip_cy = (tail_pts[1][1] + tail_pts[2][1]) // 2
            pygame.draw.circle(self.screen, (255, 245, 220), (tip_cx, tip_cy), 9)
        # Body
        pygame.draw.ellipse(self.screen, (230, 110, 30), (cx - 18, sy + 12, 36, 30))
        pygame.draw.ellipse(self.screen, (255, 235, 210), (cx - 10, sy + 18, 20, 20))
        # Legs
        pygame.draw.rect(self.screen, (210, 95, 20), (cx - 12, sy + 36, 10, 14))
        pygame.draw.rect(self.screen, (210, 95, 20), (cx + 2, sy + 36, 10, 14))
        # Head
        hx = cx + 4
        pygame.draw.circle(self.screen, (235, 115, 35), (hx, sy + 10), 17)
        # Ears
        ear_bob = int(3 * math.sin(t * 4))
        pygame.draw.polygon(self.screen, (235, 115, 35), [
            (hx - 12, sy + 1), (hx - 5, sy - 16 + ear_bob), (hx + 2, sy + 1)
        ])
        pygame.draw.polygon(self.screen, (240, 160, 160), [
            (hx - 10, sy + 1), (hx - 5, sy - 11 + ear_bob), (hx, sy + 1)
        ])
        pygame.draw.polygon(self.screen, (235, 115, 35), [
            (hx + 6, sy + 1), (hx + 14, sy - 14 + ear_bob), (hx + 18, sy + 3)
        ])
        pygame.draw.polygon(self.screen, (240, 160, 160), [
            (hx + 8, sy + 1), (hx + 14, sy - 9 + ear_bob), (hx + 16, sy + 3)
        ])
        # Eyes
        eye_blink = (int(t * 3) % 12 == 0)
        if eye_blink:
            pygame.draw.line(self.screen, (20, 20, 20), (hx + 2, sy + 10), (hx + 10, sy + 10), 2)
        else:
            pygame.draw.circle(self.screen, (255, 255, 255), (hx + 6, sy + 10), 6)
            pygame.draw.circle(self.screen, (20, 20, 20), (hx + 6, sy + 10), 4)
            pygame.draw.circle(self.screen, (255, 255, 255), (hx + 8, sy + 8), 2)
        # Nose + smile
        pygame.draw.circle(self.screen, (255, 120, 130), (hx, sy + 18), 3)
        pygame.draw.arc(self.screen, (180, 60, 60),
                        pygame.Rect(hx - 5, sy + 17, 10, 6), math.pi, 2 * math.pi, 2)

    @staticmethod
    def _hsv_to_rgb(h, s, v):
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
