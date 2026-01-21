import pygame
import random
import math
from enum import Enum


# ============================
#  ガスターブラスターの状態
# ============================
class GBState(Enum):
    APPEAR = 0
    OPEN = 1
    DISAPPEAR = 2


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
        self.width = 30
        self.speed = 5000
        self.max_length = 3000

        self.duration = duration      # ★ ここに反映
        self.fade_duration = 400
        self.timer = 0
        self.alpha = 255


    def update(self, dt):
        self.timer += dt

        # まずは通常の伸びる処理
        if self.length < self.max_length:
            self.length += self.speed * (dt / 1000)
            if self.length > self.max_length:
                self.length = self.max_length

        # 発射時間を過ぎたらフェードアウト開始
        if self.timer > self.duration:
            fade_t = (self.timer - self.duration) / self.fade_duration
            fade_t = min(fade_t, 1)

            self.alpha = int(255 * (1 - fade_t))

    def draw(self, screen, root_pos):
        if self.alpha <= 0:
            return

        rad = math.radians(self.angle)
        dir_vec = pygame.Vector2(math.cos(rad), -math.sin(rad))
        normal = pygame.Vector2(-dir_vec.y, dir_vec.x)

        half_w = self.width / 2

        p1 = root_pos + normal * half_w
        p2 = root_pos - normal * half_w
        p3 = p2 + dir_vec * self.length
        p4 = p1 + dir_vec * self.length

        # ポリゴン用の一時サーフェス
        min_x = min(p1.x, p2.x, p3.x, p4.x)
        max_x = max(p1.x, p2.x, p3.x, p4.x)
        min_y = min(p1.y, p2.y, p3.y, p4.y)
        max_y = max(p1.y, p2.y, p3.y, p4.y)

        w = int(max_x - min_x)
        h = int(max_y - min_y)

        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # ポリゴンをローカル座標に変換
        pts = [
            (p1.x - min_x, p1.y - min_y),
            (p2.x - min_x, p2.y - min_y),
            (p3.x - min_x, p3.y - min_y),
            (p4.x - min_x, p4.y - min_y),
        ]

        pygame.draw.polygon(surf, (255, 255, 255, self.alpha), pts)

        screen.blit(surf, (min_x, min_y))

# ============================
#  ガスターブラスター本体
# ============================
class GasterBlaster:
    def __init__(self, pos=(300, 300), beam_duration=600):
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
        self.beam = None
        
        self.snd_charge = pygame.mixer.Sound("sound/gasterblaster/charge.mp3")
        self.snd_fire = pygame.mixer.Sound("sound/gasterblaster/fire.mp3")
        self.snd_charge.play()
        
        self.beam_duration = beam_duration
        self.beam = None



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
                self.snd_fire.play()

        elif self.state == GBState.OPEN:
            self.current_anim.update(dt)
            if self.current_anim.finished:
                self.state = GBState.DISAPPEAR
                self.current_anim = self.anim_disappear
                self.beam = Beam(self.target_angle, self.beam_duration)  # ★ 渡す
                self.snd_fire.play()
                


        elif self.state == GBState.DISAPPEAR:
            self.current_anim.update(dt)
            if self.beam:
                self.beam.update(dt)

            back_vec = pygame.Vector2(
                math.cos(math.radians(self.target_angle + 180)),
                -math.sin(math.radians(self.target_angle + 180))
            )
            self.back_speed += 0.02 * dt
            self.current_pos += back_vec * self.back_speed

    def draw_beam_only(self, screen):
        if self.beam:
            mouth_offset = pygame.Vector2(0, 40).rotate(-(self.target_angle + 90))
            mouth_pos = self.current_pos + mouth_offset
            self.beam.draw(screen, mouth_pos)

    def draw_body_only(self, screen):
        frame = self.current_anim.get_frame().copy()

        if self.state == GBState.APPEAR:
            frame.set_alpha(self.alpha)
            frame = pygame.transform.rotate(frame, self.angle + 90)
        else:
            frame = pygame.transform.rotate(frame, self.target_angle + 90)

        rect = frame.get_rect(center=self.current_pos)
        screen.blit(frame, rect)


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
#  ガスターブラスター管理
# ============================
class ScheduledBlaster:
    def __init__(self, pos, angle, beam_duration):
        self.pos = pos
        self.angle = angle
        self.beam_duration = beam_duration


class GasterBlasterManager:
    def __init__(self):
        self.active = []
        self.scheduled = []

    def spawn_blaster(self, pos, angle, beam_duration_ms):
        self.scheduled.append(ScheduledBlaster(pos, angle, beam_duration_ms))

    def check_collision_beam_soul(self, beam, soul, root_pos):
        if beam.length <= 0:
            return False

        soul_radius = 10
        beam_radius = beam.width / 2

        rad = math.radians(beam.angle)
        dir_vec = pygame.Vector2(math.cos(rad), -math.sin(rad))
        normal = pygame.Vector2(-dir_vec.y, dir_vec.x)

        # ビームの4頂点
        p1 = root_pos + normal * beam_radius
        p2 = root_pos - normal * beam_radius
        p3 = p2 + dir_vec * beam.length
        p4 = p1 + dir_vec * beam.length

        sp = soul.pos

        # ============================
        # ① ソウルの中心が矩形の内部にあるか判定
        # ============================
        def sign(a, b, c):
            return (a.x - c.x) * (b.y - c.y) - (b.x - c.x) * (a.y - c.y)

        b1 = sign(sp, p1, p2) < 0.0
        b2 = sign(sp, p2, p3) < 0.0
        b3 = sign(sp, p3, p4) < 0.0
        b4 = sign(sp, p4, p1) < 0.0

        inside = (b1 == b2 == b3 == b4)

        if inside:
            return True

        # ============================
        # ② ソウルが矩形の辺に近い場合（端の判定）
        # ============================
        def dist_point_to_segment(p, a, b):
            ab = b - a
            ap = p - a
            t = max(0, min(1, ap.dot(ab) / ab.length_squared()))
            closest = a + ab * t
            return (p - closest).length()

        # 4辺のどれかに近ければ当たり
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
        for s in self.scheduled[:]:
            gb = GasterBlaster(pos=s.pos, beam_duration=s.beam_duration)
            gb.target_angle = s.angle
            self.active.append(gb)
            self.scheduled.remove(s)

        for gb in self.active[:]:
            gb.update(dt)

            if gb.beam:
                mouth_offset = pygame.Vector2(0, 40).rotate(-(gb.target_angle + 90))
                root_pos = gb.current_pos + mouth_offset

                if self.check_collision_beam_soul(gb.beam, soul, root_pos):
                    soul.take_damage(5)

            if gb.current_pos.x < -300 or gb.current_pos.x > 900 or \
               gb.current_pos.y < -300 or gb.current_pos.y > 900:
                self.active.remove(gb)

    def draw(self, screen):
        for gb in self.active:
            gb.draw_beam_only(screen)
        for gb in self.active:
            gb.draw_body_only(screen)


# ============================
#  HPバー
# ============================
def draw_hp(screen, soul):
    pygame.draw.rect(screen, (255, 255, 255), (50, 50, 200, 20), 3)

    ratio = soul.hp / soul.max_hp
    width = int(194 * ratio)

    pygame.draw.rect(screen, (255, 255, 0), (53, 53, width, 14))


# ============================
#  メイン
# ============================
def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((600, 600))
    clock = pygame.time.Clock()

    box = BattleBox(150, 350, 300, 200)
    soul = Soul(box)
    manager = GasterBlasterManager()

    manager.spawn_blaster((300, 300), 0, 1000)
    manager.spawn_blaster((100, 500), 90, 2000)
    manager.spawn_blaster((500, 100), 225, 3000)
    for i in range(30):
        x = random.randint(0, 600)
        y = random.randint(0, 600)
        angle = random.randint(0, 360)
        delay = random.randint(4000, 10000)
        manager.spawn_blaster((x, y), angle, delay)

    running = True
    while running:
        dt = clock.tick(60)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        soul.update(keys, dt)
        manager.update(dt, soul)

        screen.fill((0, 0, 0))
        box.draw(screen)
        soul.draw(screen)
        manager.draw(screen)
        draw_hp(screen, soul)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
