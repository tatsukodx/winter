import pygame
import math
import random
from enum import Enum


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

        # ★ 当たり判定用（固定）
        self.hitbox_width = 30

        # ★ 描画用（変動）
        self.draw_width = 30

        self.speed = 5000
        self.max_length = 3000

        self.duration = duration
        self.fade_duration = 400
        self.timer = 0
        self.alpha = 255

    def update(self, dt):
        self.timer += dt

        # 伸びる
        if self.length < self.max_length:
            self.length += self.speed * (dt / 1000)
            if self.length > self.max_length:
                self.length = self.max_length

        # ★ 見た目の太さを脈動させる（本家風）
        pulse = (math.sin(self.timer * 0.02) + 1) * 0.5  # 0〜1
        self.draw_width = 20 + pulse * 20  # 20〜40 の間で変化

        # フェードアウト
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

        # ★ 描画は draw_width を使う
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
#  音声管理システム（1つだけ再生）
# ============================
class SoundManager:
    def __init__(self):
        # ★ チャンネル数を設定
        pygame.mixer.set_num_channels(8)
        
        # 音声をロード
        self.charge_sound = pygame.mixer.Sound("sound/gasterblaster/charge.wav")
        self.fire_sound = pygame.mixer.Sound("sound/gasterblaster/fire.wav")
        
        # ★ 音量を適切に設定
        self.charge_sound.set_volume(0.6)
        self.fire_sound.set_volume(0.6)
        
        # ★ 専用チャンネル
        self.charge_channel = pygame.mixer.Channel(0)
        self.fire_channel = pygame.mixer.Channel(1)
        
        # ★ 最後に再生した時刻
        self.last_charge_time = 0
        self.last_fire_time = 0
        
        # ★ 最小間隔（ミリ秒）
        self.min_interval = 50  # 50ms以内は再生しない
    
    def play_charge(self):
        """チャージ音を再生（同時再生されている場合はスキップ）"""
        current_time = pygame.time.get_ticks()
        
        # ★ すでに再生中、または最小間隔内の場合はスキップ
        if self.charge_channel.get_busy() or \
           (current_time - self.last_charge_time) < self.min_interval:
            return None
        
        # ★ 再生
        self.charge_channel.play(self.charge_sound)
        self.last_charge_time = current_time
        return self.charge_channel
    
    def play_fire(self):
        """発射音を再生（同時再生されている場合はスキップ）"""
        current_time = pygame.time.get_ticks()
        
        # ★ すでに再生中、または最小間隔内の場合はスキップ
        if self.fire_channel.get_busy() or \
           (current_time - self.last_fire_time) < self.min_interval:
            return None
        
        # ★ 再生
        self.fire_channel.play(self.fire_sound)
        self.last_fire_time = current_time
        return self.fire_channel


# ============================
#  ガスターブラスター本体
# ============================
class GasterBlaster:
    def __init__(self, pos, beam_duration, open_delay, sound_manager, manager):

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
        
        self.sound_manager = sound_manager
        self.manager = manager

        # ★ チャンネルを保持
        self.my_channel = None
        
        # ★ チャージ音を再生（同時の場合はスキップされる）
        self.my_channel = self.sound_manager.play_charge()
        
        self.open_delay = open_delay
        self.open_timer = 0
        self.fired = False

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
            # ★ 開口まで待つ
            if self.open_timer < self.open_delay:
                self.open_timer += dt
                return

            # ★ 開口アニメを進める
            self.current_anim.update(dt)

            # 開口アニメが終わったら即発射
            if self.current_anim.finished and not self.fired:
                self.state = GBState.DISAPPEAR
                self.current_anim = self.anim_disappear
                self.beam = Beam(self.target_angle, self.beam_duration)
                
                # ★ 発射音を再生（同時の場合はスキップされる）
                self.sound_manager.play_fire()
                
                self.fired = True

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
    def __init__(self, sound_manager):
        self.sound_manager = sound_manager

        self.blasters = []
        self.scheduled = []
        self.active = []
        self.commands = []
        self.command_timer = 0

    def spawn(self, pos, angle, beam_duration=600, open_delay=0):
        gb = GasterBlaster(
            pos,
            beam_duration,
            open_delay,
            self.sound_manager,
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

        # ビームの4頂点
        p1 = root_pos + normal * beam_radius
        p2 = root_pos - normal * beam_radius
        p3 = p2 + dir_vec * beam.length
        p4 = p1 + dir_vec * beam.length

        sp = soul.pos

        # ① ソウルの中心が矩形の内部にあるか判定
        def sign(a, b, c):
            return (a.x - c.x) * (b.y - c.y) - (b.x - c.x) * (a.y - c.y)

        b1 = sign(sp, p1, p2) < 0.0
        b2 = sign(sp, p2, p3) < 0.0
        b3 = sign(sp, p3, p4) < 0.0
        b4 = sign(sp, p4, p1) < 0.0

        inside = (b1 == b2 == b3 == b4)

        if inside:
            return True

        # ② ソウルが矩形の辺に近い場合（端の判定）
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

    def update(self, dt, soul):
        # シーケンス処理
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

        # まだ spawn されていない ScheduledBlaster を GasterBlaster に変換
        for s in self.scheduled:
            if not s.spawned:
                gb = GasterBlaster(
                    pos=s.pos,
                    beam_duration=s.beam_duration,
                    open_delay=s.open_delay,
                    sound_manager=self.sound_manager,
                    manager=self
                )
                gb.target_angle = s.angle
                self.active.append(gb)
                s.spawned = True

        # 既存ブラスター更新
        for gb in self.active[:]:
            gb.update(dt)

            if gb.beam:
                mouth_offset = pygame.Vector2(0, 40).rotate(-(gb.target_angle + 90))
                root_pos = gb.current_pos + mouth_offset

                if self.check_collision_beam_soul(gb.beam, soul, root_pos):
                    soul.take_damage(5)

            # 画面外に大きく出たら削除
            if gb.current_pos.x < -300 or gb.current_pos.x > 900 or \
               gb.current_pos.y < -300 or gb.current_pos.y > 900:
                self.active.remove(gb)

    def draw(self, screen):
        for gb in self.active:
            gb.draw_beam_only(screen)
        for gb in self.active:
            gb.draw_body_only(screen)


# ============================
#  メインループ
# ============================
def main():
    pygame.init()
    
    # ★ 音声初期化を先に実行
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Gaster Blaster Test")
    clock = pygame.time.Clock()

    box = BattleBox(200, 150, 400, 300)
    soul = Soul(box)

    # ★ 音声管理システムを初期化
    sound_manager = SoundManager()
    
    # ★ マネージャーに音声管理システムを渡す
    manager = GasterBlasterManager(sound_manager)

    font = pygame.font.SysFont(None, 24)

    running = True
    attack_state = None
    attack_cooldown = 0
    attack_timer = 0
    attack_count = 0
    
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        soul.update(keys, dt)

        # ============================
        # ランダム攻撃パターン制御
        # ============================
        attack_timer += dt

        if attack_state is None:
            if attack_cooldown <= 0:
                attack_state = random.choice(["cross", "triple", "chain", "circle"])
                attack_timer = 0
                attack_count = 0
            else:
                attack_cooldown -= dt

        else:
            if attack_state == "cross":
                commands = []
                commands.append(("spawn", (box.rect.centerx, box.rect.top - 50), 0, 800))
                commands.append(("spawn", (box.rect.centerx, box.rect.bottom + 50), 180, 800))
                commands.append(("spawn", (box.rect.left - 50, box.rect.centery), 270, 800))
                commands.append(("spawn", (box.rect.right + 50, box.rect.centery), 90, 800))
                commands.append(("wait", 1500))
                manager.sequence(commands)
                attack_state = None
                attack_cooldown = 1000

            elif attack_state == "triple":
                commands = []
                for a in [0, 120, 240]:
                    commands.append(("spawn", (box.rect.centerx, box.rect.centery), a, 800))
                commands.append(("wait", 1200))
                manager.sequence(commands)
                attack_state = None
                attack_cooldown = 1200

            elif attack_state == "chain":
                if attack_timer >= 300:
                    attack_timer = 0
                    commands = []
                    angle = random.choice([0, 90, 180, 270])
                    commands.append(("spawn", (box.rect.centerx, box.rect.centery), angle, 800))
                    manager.sequence(commands)
                    attack_count += 1
                    if attack_count >= 5:
                        attack_state = None
                        attack_cooldown = 1500

            elif attack_state == "circle":
                commands = []
                for i in range(8):
                    commands.append(("spawn", (box.rect.centerx, box.rect.centery), i * 45, 800))
                commands.append(("wait", 1500))
                manager.sequence(commands)
                attack_state = None
                attack_cooldown = 1500

        manager.update(dt, soul)

        screen.fill((0, 0, 0))
        box.draw(screen)
        manager.draw(screen)
        soul.draw(screen)

        hp_text = font.render(f"HP: {soul.hp}/{soul.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (10, 10))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
