import pygame
import math
import random
from enum import Enum


# ============================
#  パーティクル（視覚効果）
# ============================
class Particle:
    def __init__(self, pos, color=(255, 255, 255)):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(
            random.uniform(-2, 2),
            random.uniform(-2, 2)
        )
        self.lifetime = random.randint(300, 600)
        self.timer = 0
        self.color = color
        self.size = random.randint(2, 5)

    def update(self, dt):
        self.timer += dt
        self.pos += self.velocity
        self.velocity *= 0.98

    def is_dead(self):
        return self.timer >= self.lifetime

    def draw(self, screen):
        alpha = int(255 * (1 - self.timer / self.lifetime))
        size = int(self.size * (1 - self.timer / self.lifetime))
        if size > 0:
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (size, size), size)
            screen.blit(surf, (self.pos.x - size, self.pos.y - size))


# ============================
#  パーティクル管理
# ============================
class ParticleManager:
    def __init__(self):
        self.particles = []

    def add_particles(self, pos, count=10, color=(255, 255, 255)):
        for _ in range(count):
            self.particles.append(Particle(pos, color))

    def update(self, dt):
        self.particles = [p for p in self.particles if not p.is_dead()]
        for p in self.particles:
            p.update(dt)

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)


# ============================
#  バトルボックス
# ============================
class BattleBox:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 4)


# ============================
#  ソウル（HP・無敵時間・点滅）
# ============================
class Soul:
    def __init__(self, box: BattleBox):
        self.normal_img = pygame.image.load("sprite/soul/soul.png").convert_alpha()
        self.damaged_img = pygame.image.load("sprite/soul/damaged.png").convert_alpha()

        self.image = self.normal_img
        self.pos = pygame.Vector2(box.rect.centerx, box.rect.centery)
        self.speed = 4
        self.box = box

        # HP
        self.max_hp = 92
        self.hp = 92

        # 無敵時間
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1000

        # 点滅
        self.flash_timer = 0
        self.flash_duration = 200

    def take_damage(self, amount):
        if not self.invincible:
            self.hp -= amount
            if self.hp < 0:
                self.hp = 0

            self.invincible = True
            self.invincible_timer = self.invincible_duration
            self.flash_timer = self.flash_duration
            self.image = self.damaged_img
            return True
        return False

    def update(self, keys, dt):
        if keys[pygame.K_UP]:
            self.pos.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.pos.y += self.speed
        if keys[pygame.K_LEFT]:
            self.pos.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.pos.x += self.speed

        # バトルボックス内に制限
        if self.pos.x < self.box.rect.left + 10:
            self.pos.x = self.box.rect.left + 10
        if self.pos.x > self.box.rect.right - 10:
            self.pos.x = self.box.rect.right - 10
        if self.pos.y < self.box.rect.top + 10:
            self.pos.y = self.box.rect.top + 10
        if self.pos.y > self.box.rect.bottom - 10:
            self.pos.y = self.box.rect.bottom - 10

        # 無敵時間
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
                self.image = self.normal_img

        # 点滅
        if self.flash_timer > 0:
            self.flash_timer -= dt
            if (self.flash_timer // 50) % 2 == 0:
                self.image.set_alpha(255)
            else:
                self.image.set_alpha(100)
        else:
            self.image.set_alpha(255)

    def draw(self, screen):
        rect = self.image.get_rect(center=self.pos)
        screen.blit(self.image, rect)

    def reset(self):
        self.hp = self.max_hp
        self.pos = pygame.Vector2(self.box.rect.centerx, self.box.rect.centery)
        self.invincible = False
        self.invincible_timer = 0
        self.flash_timer = 0
        self.image = self.normal_img


# ============================
#  アニメーション管理
# ============================
class Animation:
    def __init__(self, frames, frame_duration=100, loop=False):
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
        self.current_time = 0
        self.current_frame = 0
        self.finished = False

    def update(self, dt):
        if self.finished:
            return

        self.current_time += dt
        if self.current_time >= self.frame_duration:
            self.current_time = 0
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True

    def get_frame(self):
        return self.frames[self.current_frame]


# ============================
#  ビーム（ポリゴン方式）
# ============================
class Beam:
    def __init__(self, angle, duration=600):
        self.angle = angle
        self.length = 0
        self.hitbox_width = 30
        self.draw_width = 30
        self.speed = 5000
        self.max_length = 3000
        self.duration = duration
        self.fade_duration = 400
        self.timer = 0
        self.alpha = 255

    def update(self, dt):
        self.timer += dt

        if self.length < self.max_length:
            self.length += self.speed * (dt / 1000)
            if self.length > self.max_length:
                self.length = self.max_length

        pulse = (math.sin(self.timer * 0.02) + 1) * 0.5
        self.draw_width = 20 + pulse * 20

        if self.timer > self.duration:
            fade_t = (self.timer - self.duration) / self.fade_duration
            fade_t = min(fade_t, 1)
            self.alpha = int(255 * (1 - fade_t))

    def draw(self, screen, root_pos):
        if self.alpha <= 0:
            return

        rad = math.radians(self.angle - 90)
        dir_vec = pygame.Vector2(math.cos(rad), math.sin(rad))
        normal = pygame.Vector2(-dir_vec.y, dir_vec.x)

        half_w = self.draw_width / 2

        p1 = root_pos + normal * half_w
        p2 = root_pos - normal * half_w
        p3 = p2 + dir_vec * self.length
        p4 = p1 + dir_vec * self.length

        min_x = min(p1.x, p2.x, p3.x, p4.x)
        max_x = max(p1.x, p2.x, p3.x, p4.x)
        min_y = min(p1.y, p2.y, p3.y, p4.y)
        max_y = max(p1.y, p2.y, p3.y, p4.y)

        w = int(max_x - min_x)
        h = int(max_y - min_y)

        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        pts = [
            (p1.x - min_x, p1.y - min_y),
            (p2.x - min_x, p2.y - min_y),
            (p3.x - min_x, p3.y - min_y),
            (p4.x - min_x, p4.y - min_y),
        ]

        pygame.draw.polygon(surf, (255, 255, 255, self.alpha), pts)
        screen.blit(surf, (min_x, min_y))


# ============================
#  ガスターブラスターの状態
# ============================
class GBState(Enum):
    APPEAR = 0
    OPEN = 1
    DISAPPEAR = 2


# ============================
#  ガスターブラスター本体
# ============================
class GasterBlaster:
    def __init__(self, pos, beam_duration, open_delay,
              snd_charge, snd_fire,
              ch_charge, ch_fire,
              manager):

        self.anim_appear = Animation([
            pygame.image.load("sprite/gasterblaster/1.png").convert_alpha()
        ], 200, False)

        self.anim_open = Animation([
            pygame.image.load("sprite/gasterblaster/2.png").convert_alpha(),
            pygame.image.load("sprite/gasterblaster/3.png").convert_alpha(),
            pygame.image.load("sprite/gasterblaster/4.png").convert_alpha(),
        ], 120, False)

        self.anim_disappear = Animation([
            pygame.image.load("sprite/gasterblaster/5.png").convert_alpha(),
            pygame.image.load("sprite/gasterblaster/6.png").convert_alpha(),
        ], 150, True)

        self.state = GBState.APPEAR
        self.current_anim = self.anim_appear

        self.final_pos = pygame.Vector2(pos)
        self.start_pos = pygame.Vector2(
            random.randint(0, 600),
            random.randint(0, 600)
        )
        self.current_pos = self.start_pos.copy()

        self.alpha = 0
        self.appear_time = 0
        self.appear_duration = 800

        self.target_angle = 0
        self.angle = self.target_angle + 360

        self.back_speed = 0

        self.beam_duration = beam_duration
        self.beam = None
        
        self.snd_charge = snd_charge
        self.snd_fire = snd_fire
        self.ch_charge = ch_charge
        self.ch_fire = ch_fire
        self.manager = manager

        now = pygame.time.get_ticks()
        if now - self.manager.last_sound_time >= self.manager.sound_cooldown:
            self.ch_charge.play(self.snd_charge)
            self.manager.last_sound_time = now

        self.open_delay = open_delay
        self.open_timer = 0

    def update(self, dt):
        if self.state == GBState.APPEAR:
            self.appear_time += dt
            t = min(self.appear_time / self.appear_duration, 1)
            ease_t = 1 - (1 - t) ** 2

            self.current_pos = self.start_pos.lerp(self.final_pos, ease_t)
            self.alpha = int(255 * ease_t)

            diff = (self.angle - self.target_angle)
            self.angle -= diff / 6

            if t >= 1:
                self.state = GBState.OPEN
                self.current_anim = self.anim_open

        elif self.state == GBState.OPEN:
            if self.open_timer < self.open_delay:
                self.open_timer += dt
                return

            self.current_anim.update(dt)

            if self.current_anim.finished:
                self.state = GBState.DISAPPEAR
                self.current_anim = self.anim_disappear
                self.beam = Beam(self.target_angle, self.beam_duration)
                now = pygame.time.get_ticks()
                if now - self.manager.last_sound_time >= self.manager.sound_cooldown:
                    self.ch_fire.play(self.snd_fire)
                    self.manager.last_sound_time = now

        elif self.state == GBState.DISAPPEAR:
            self.current_anim.update(dt)
            if self.beam:
                self.beam.update(dt)

            back_vec = pygame.Vector2(
                math.cos(math.radians(-self.target_angle - 90)),
                -math.sin(math.radians(-self.target_angle - 90))
            )
            self.back_speed += 0.02 * dt
            self.current_pos += back_vec * self.back_speed

    def draw_beam_only(self, screen):
        if self.beam:
            mouth_offset = pygame.Vector2(40, 0).rotate(self.target_angle-90)
            mouth_pos = self.current_pos + mouth_offset
            self.beam.draw(screen, mouth_pos)

    def draw_body_only(self, screen):
        frame = self.current_anim.get_frame().copy()

        if self.state == GBState.APPEAR:
            frame.set_alpha(self.alpha)
            frame = pygame.transform.rotate(frame, -self.angle+180)
        else:
            frame = pygame.transform.rotate(frame, -self.target_angle+180)

        rect = frame.get_rect(center=self.current_pos)
        screen.blit(frame, rect)


# ============================
#  ガスターブラスター管理
# ============================
class ScheduledBlaster:
    def __init__(self, pos, angle, open_delay, beam_duration):
        self.pos = pos
        self.angle = angle
        self.open_delay = open_delay
        self.beam_duration = beam_duration
        self.spawned = False


class GasterBlasterManager:
    def __init__(self, snd_charge, snd_fire, ch_charge, ch_fire):
        self.snd_charge = snd_charge
        self.snd_fire = snd_fire
        self.ch_charge = ch_charge
        self.ch_fire = ch_fire

        self.blasters = []
        self.scheduled = []
        self.active = []
        self.commands = []
        self.command_timer = 0
        self.last_sound_time = 0
        self.sound_cooldown = 100

    def spawn(self, pos, angle, beam_duration=600, open_delay=0):
        gb = GasterBlaster(
            pos,
            beam_duration,
            open_delay,
            self.snd_charge,
            self.snd_fire,
            self.ch_charge,
            self.ch_fire,
            self
        )
        gb.target_angle = angle
        self.blasters.append(gb)

    def sequence(self, commands):
        self.commands = commands
        self.command_timer = 0

    def spawn_blaster(self, pos, angle, fire_delay_ms, beam_duration_ms=600):
        self.scheduled.append(ScheduledBlaster(pos, angle, fire_delay_ms, beam_duration_ms))

    def check_collision_beam_soul(self, beam, soul, root_pos):
        if beam.length <= 0:
            return False

        soul_radius = 10
        beam_radius = beam.hitbox_width / 2

        rad = math.radians(beam.angle)
        dir_vec = pygame.Vector2(math.cos(rad), -math.sin(rad))
        normal = pygame.Vector2(-dir_vec.y, dir_vec.x)

        p1 = root_pos + normal * beam_radius
        p2 = root_pos - normal * beam_radius
        p3 = p2 + dir_vec * beam.length
        p4 = p1 + dir_vec * beam.length

        sp = soul.pos

        def sign(a, b, c):
            return (a.x - c.x) * (b.y - c.y) - (b.x - c.x) * (a.y - c.y)

        b1 = sign(sp, p1, p2) < 0.0
        b2 = sign(sp, p2, p3) < 0.0
        b3 = sign(sp, p3, p4) < 0.0
        b4 = sign(sp, p4, p1) < 0.0

        inside = (b1 == b2 == b3 == b4)

        if inside:
            return True

        def dist_point_to_segment(p, a, b):
            ab = b - a
            ap = p - a
            t = max(0, min(1, ap.dot(ab) / ab.length_squared()))
            closest = a + ab * t
            return (p - closest).length()

        if dist_point_to_segment(sp, p1, p2) <= soul_radius:
            return True
        if dist_point_to_segment(sp, p2, p3) <= soul_radius:
            return True
        if dist_point_to_segment(sp, p3, p4) <= soul_radius:
            return True
        if dist_point_to_segment(sp, p4, p1) <= soul_radius:
            return True

        return False

    def update(self, dt, soul, particle_manager):
        if self.commands:
            cmd = self.commands[0]

            if cmd[0] == "wait":
                self.command_timer += dt
                if self.command_timer >= cmd[1]:
                    self.command_timer = 0
                    self.commands.pop(0)

            elif cmd[0] == "spawn":
                _, pos, angle, fire_delay = cmd
                self.spawn_blaster(pos, angle, fire_delay)
                self.commands.pop(0)

        for s in self.scheduled:
            if not s.spawned:
                gb = GasterBlaster(
                    pos=s.pos,
                    beam_duration=s.beam_duration,
                    open_delay=s.open_delay,
                    snd_charge=self.snd_charge,
                    snd_fire=self.snd_fire,
                    ch_charge=self.ch_charge,
                    ch_fire=self.ch_fire,
                    manager=self
                )

                gb.target_angle = s.angle
                self.active.append(gb)
                s.spawned = True

        for gb in self.active[:]:
            gb.update(dt)

            if gb.beam:
                mouth_offset = pygame.Vector2(0, 40).rotate(-(gb.target_angle + 90))
                root_pos = gb.current_pos + mouth_offset

                if self.check_collision_beam_soul(gb.beam, soul, root_pos):
                    if soul.take_damage(5):
                        particle_manager.add_particles(soul.pos, 20, (255, 100, 100))

            if gb.current_pos.x < -300 or gb.current_pos.x > 900 or \
               gb.current_pos.y < -300 or gb.current_pos.y > 900:
                self.active.remove(gb)

    def draw(self, screen):
        for gb in self.active:
            gb.draw_beam_only(screen)
        for gb in self.active:
            gb.draw_body_only(screen)

    def clear(self):
        self.active.clear()
        self.scheduled.clear()
        self.commands.clear()


# ============================
#  ゲームステート
# ============================
class GameState(Enum):
    PLAYING = 0
    GAME_OVER = 1


# ============================
#  スコア管理
# ============================
class ScoreManager:
    def __init__(self):
        self.score = 0
        self.combo = 0
        self.combo_timer = 0
        self.combo_duration = 3000
        self.high_score = 0

    def update(self, dt, soul_alive):
        if soul_alive:
            self.score += dt // 10
            self.combo_timer += dt
            if self.combo_timer >= 1000:
                self.combo += 1
                self.combo_timer = 0
        else:
            self.combo = 0
            self.combo_timer = 0

    def reset_combo(self):
        self.combo = 0
        self.combo_timer = 0

    def update_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score

    def reset(self):
        self.score = 0
        self.combo = 0
        self.combo_timer = 0


# ============================
#  難易度管理
# ============================
class DifficultyManager:
    def __init__(self):
        self.level = 1
        self.score_threshold = 1000

    def update(self, score):
        self.level = 1 + score // self.score_threshold

    def get_attack_cooldown(self):
        base = 1000
        reduction = min(500, self.level * 50)
        return max(500, base - reduction)

    def get_beam_duration(self):
        base = 800
        increase = min(400, self.level * 30)
        return base + increase


# ============================
#  UI描画
# ============================
class UIManager:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 32)
        self.font_small = pygame.font.SysFont(None, 24)

    def draw_hud(self, soul, score_manager, difficulty_manager):
        # HP バー
        hp_width = 200
        hp_height = 20
        hp_ratio = soul.hp / soul.max_hp
        
        pygame.draw.rect(self.screen, (100, 100, 100), (10, 10, hp_width, hp_height))
        pygame.draw.rect(self.screen, (255, 0, 0), (10, 10, hp_width * hp_ratio, hp_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (10, 10, hp_width, hp_height), 2)

        hp_text = self.font_small.render(f"HP: {soul.hp}/{soul.max_hp}", True, (255, 255, 255))
        self.screen.blit(hp_text, (220, 12))

        # スコア
        score_text = self.font_medium.render(f"Score: {score_manager.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 40))

        # コンボ
        if score_manager.combo > 0:
            combo_text = self.font_medium.render(f"Combo: {score_manager.combo}x", True, (255, 200, 0))
            self.screen.blit(combo_text, (10, 75))

        # レベル
        level_text = self.font_small.render(f"Level: {difficulty_manager.level}", True, (200, 200, 255))
        self.screen.blit(level_text, (self.screen.get_width() - 120, 10))

        # ハイスコア
        high_score_text = self.font_small.render(f"High: {score_manager.high_score}", True, (255, 255, 100))
        self.screen.blit(high_score_text, (self.screen.get_width() - 150, 35))

    def draw_game_over(self, score_manager):
        # 半透明背景
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # ゲームオーバー文字
        game_over_text = self.font_large.render("GAME OVER", True, (255, 50, 50))
        rect = game_over_text.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(game_over_text, rect)

        # スコア
        score_text = self.font_medium.render(f"Final Score: {score_manager.score}", True, (255, 255, 255))
        rect = score_text.get_rect(center=(self.screen.get_width() // 2, 280))
        self.screen.blit(score_text, rect)

        # ハイスコア
        if score_manager.score == score_manager.high_score and score_manager.score > 0:
            new_record = self.font_medium.render("NEW RECORD!", True, (255, 255, 0))
            rect = new_record.get_rect(center=(self.screen.get_width() // 2, 320))
            self.screen.blit(new_record, rect)

        # 操作説明
        retry_text = self.font_small.render("Press R to Retry", True, (200, 200, 200))
        rect = retry_text.get_rect(center=(self.screen.get_width() // 2, 400))
        self.screen.blit(retry_text, rect)

        quit_text = self.font_small.render("Press ESC to Quit", True, (200, 200, 200))
        rect = quit_text.get_rect(center=(self.screen.get_width() // 2, 430))
        self.screen.blit(quit_text, rect)


# ============================
#  攻撃パターン管理
# ============================
class AttackPatternManager:
    def __init__(self, manager, box, difficulty_manager):
        self.manager = manager
        self.box = box
        self.difficulty = difficulty_manager
        self.attack_state = None
        self.attack_cooldown = 0
        self.attack_timer = 0
        self.attack_count = 0

    def update(self, dt):
        self.attack_timer += dt

        if self.attack_state is None:
            if self.attack_cooldown <= 0:
                self.attack_state = random.choice(["cross", "triple", "chain", "circle", "spiral"])
                self.attack_timer = 0
                self.attack_count = 0
            else:
                self.attack_cooldown -= dt
        else:
            self._execute_pattern(dt)

    def _execute_pattern(self, dt):
        beam_duration = self.difficulty.get_beam_duration()
        
        if self.attack_state == "cross":
            commands = []
            commands.append(("spawn", (self.box.rect.centerx, self.box.rect.top - 50), 0, beam_duration))
            commands.append(("spawn", (self.box.rect.centerx, self.box.rect.bottom + 50), 180, beam_duration))
            commands.append(("spawn", (self.box.rect.left - 50, self.box.rect.centery), 270, beam_duration))
            commands.append(("spawn", (self.box.rect.right + 50, self.box.rect.centery), 90, beam_duration))
            commands.append(("wait", 1500))
            self.manager.sequence(commands)
            self.attack_state = None
            self.attack_cooldown = self.difficulty.get_attack_cooldown()

        elif self.attack_state == "triple":
            commands = []
            for a in [0, 120, 240]:
                commands.append(("spawn", (self.box.rect.centerx, self.box.rect.centery), a, beam_duration))
            commands.append(("wait", 1200))
            self.manager.sequence(commands)
            self.attack_state = None
            self.attack_cooldown = self.difficulty.get_attack_cooldown()

        elif self.attack_state == "chain":
            if self.attack_timer >= 300:
                self.attack_timer = 0
                commands = []
                angle = random.choice([0, 90, 180, 270])
                commands.append(("spawn", (self.box.rect.centerx, self.box.rect.centery), angle, beam_duration))
                self.manager.sequence(commands)
                self.attack_count += 1
                if self.attack_count >= 5:
                    self.attack_state = None
                    self.attack_cooldown = self.difficulty.get_attack_cooldown()

        elif self.attack_state == "circle":
            commands = []
            for i in range(8):
                commands.append(("spawn", (self.box.rect.centerx, self.box.rect.centery), i * 45, beam_duration))
            commands.append(("wait", 1500))
            self.manager.sequence(commands)
            self.attack_state = None
            self.attack_cooldown = self.difficulty.get_attack_cooldown()

        elif self.attack_state == "spiral":
            if self.attack_timer >= 200:
                self.attack_timer = 0
                angle = self.attack_count * 30
                commands = []
                commands.append(("spawn", (self.box.rect.centerx, self.box.rect.centery), angle, beam_duration))
                self.manager.sequence(commands)
                self.attack_count += 1
                if self.attack_count >= 12:
                    self.attack_state = None
                    self.attack_cooldown = self.difficulty.get_attack_cooldown()

    def reset(self):
        self.attack_state = None
        self.attack_cooldown = 0
        self.attack_timer = 0
        self.attack_count = 0


# ============================
#  メインループ
# ============================
def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    
    snd_charge = pygame.mixer.Sound("sound/gasterblaster/charge.wav")
    snd_fire = pygame.mixer.Sound("sound/gasterblaster/fire.wav")
    
    CHANNEL_CHARGE = pygame.mixer.Channel(0)
    CHANNEL_FIRE = pygame.mixer.Channel(1)

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Gaster Blaster - Enhanced Edition")
    clock = pygame.time.Clock()

    # ゲーム要素の初期化
    box = BattleBox(200, 150, 400, 300)
    soul = Soul(box)

    manager = GasterBlasterManager(
        snd_charge, snd_fire,
        CHANNEL_CHARGE, CHANNEL_FIRE
    )

    particle_manager = ParticleManager()
    score_manager = ScoreManager()
    difficulty_manager = DifficultyManager()
    ui_manager = UIManager(screen)
    attack_manager = AttackPatternManager(manager, box, difficulty_manager)

    game_state = GameState.PLAYING

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                if game_state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        # リセット
                        soul.reset()
                        score_manager.reset()
                        difficulty_manager = DifficultyManager()
                        attack_manager = AttackPatternManager(manager, box, difficulty_manager)
                        manager.clear()
                        particle_manager.particles.clear()
                        game_state = GameState.PLAYING

        keys = pygame.key.get_pressed()

        if game_state == GameState.PLAYING:
            soul.update(keys, dt)
            manager.update(dt, soul, particle_manager)
            particle_manager.update(dt)
            score_manager.update(dt, soul.hp > 0)
            difficulty_manager.update(score_manager.score)
            attack_manager.update(dt)

            # ゲームオーバー判定
            if soul.hp <= 0:
                game_state = GameState.GAME_OVER
                score_manager.update_high_score()

        # 描画
        screen.fill((0, 0, 0))
        box.draw(screen)
        manager.draw(screen)
        particle_manager.draw(screen)
        soul.draw(screen)
        ui_manager.draw_hud(soul, score_manager, difficulty_manager)

        if game_state == GameState.GAME_OVER:
            ui_manager.draw_game_over(score_manager)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
