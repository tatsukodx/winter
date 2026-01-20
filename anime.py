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
#  バトルボックス
# ============================
class BattleBox:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 4)  # 枠線のみ
        
        
# ============================
#  ソウル（プレイヤー）
# ============================
class Soul:
    def __init__(self, box: BattleBox):
        self.image = pygame.image.load("sprite/soul/soul.png").convert_alpha()
        self.pos = pygame.Vector2(
            box.rect.centerx,
            box.rect.centery
        )
        self.speed = 4
        self.box = box

    def update(self, keys):
        if keys[pygame.K_UP]:
            self.pos.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.pos.y += self.speed
        if keys[pygame.K_LEFT]:
            self.pos.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.pos.x += self.speed

        # ⭐ バトルボックス内に制限
        if self.pos.x < self.box.rect.left + 10:
            self.pos.x = self.box.rect.left + 10
        if self.pos.x > self.box.rect.right - 10:
            self.pos.x = self.box.rect.right - 10
        if self.pos.y < self.box.rect.top + 10:
            self.pos.y = self.box.rect.top + 10
        if self.pos.y > self.box.rect.bottom - 10:
            self.pos.y = self.box.rect.bottom - 10

    def draw(self, screen):
        rect = self.image.get_rect(center=self.pos)
        screen.blit(self.image, rect)

# ============================
#  ビーム（根本は毎フレーム更新）
# ============================
class Beam:
    def __init__(self, angle):
        self.angle = angle
        self.length = 0
        self.width = 30
        self.speed = 5000
        self.max_length = 3000

    def update(self, dt):
        self.length += self.speed * (dt / 1000)
        if self.length > self.max_length:
            self.length = self.max_length

    def draw(self, screen, root_pos):
        rad = math.radians(self.angle)

        end_x = root_pos.x + math.cos(rad) * self.length
        end_y = root_pos.y - math.sin(rad) * self.length

        pygame.draw.line(
            screen,
            (255, 255, 255),
            root_pos,
            (end_x, end_y),
            self.width
        )


# ============================
#  ガスターブラスター本体
# ============================
class GasterBlaster:
    def __init__(self, pos=(300, 300)):
        # 出現：1
        appear_frames = [
            pygame.image.load("sprite/gasterblaster/1.png").convert_alpha()
        ]
        self.anim_appear = Animation(appear_frames, 200, False)

        # 開口：2 → 3 → 4
        open_frames = [
            pygame.image.load("sprite/gasterblaster/2.png").convert_alpha(),
            pygame.image.load("sprite/gasterblaster/3.png").convert_alpha(),
            pygame.image.load("sprite/gasterblaster/4.png").convert_alpha(),
        ]
        self.anim_open = Animation(open_frames, 120, False)

        # 発射：5 ↔ 6
        disappear_frames = [
            pygame.image.load("sprite/gasterblaster/5.png").convert_alpha(),
            pygame.image.load("sprite/gasterblaster/6.png").convert_alpha(),
        ]
        self.anim_disappear = Animation(disappear_frames, 150, True)

        self.state = GBState.APPEAR
        self.current_anim = self.anim_appear

        # 出現演出
        self.final_pos = pygame.Vector2(pos)
        self.start_pos = pygame.Vector2(
            random.randint(0, 600),
            random.randint(0, 600)
        )
        self.current_pos = self.start_pos.copy()

        self.alpha = 0
        self.appear_time = 0
        self.appear_duration = 800

        # 回転
        self.target_angle = 0
        self.angle = self.target_angle + 360  # 1回転分

        # 発射後の後退
        self.back_speed = 0

        # ビーム
        self.beam = None

    def update(self, dt):
        # 出現
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

        # 開口
        elif self.state == GBState.OPEN:
            self.current_anim.update(dt)

            if self.current_anim.finished:
                self.state = GBState.DISAPPEAR
                self.current_anim = self.anim_disappear

                # ビーム生成（root_pos は毎フレーム更新）
                self.beam = Beam(self.target_angle)

        # 発射
        elif self.state == GBState.DISAPPEAR:
            self.current_anim.update(dt)

            if self.beam:
                self.beam.update(dt)

            # 後退
            back_vec = pygame.Vector2(
                math.cos(math.radians(self.target_angle + 180)),
                -math.sin(math.radians(self.target_angle + 180))
            )
            self.back_speed += 0.02 * dt
            self.current_pos += back_vec * self.back_speed

    # ビームだけ描画（背景）
    def draw_beam_only(self, screen):
        if self.beam:
            mouth_offset = pygame.Vector2(0, 40).rotate(-(self.target_angle + 90))
            mouth_pos = self.current_pos + mouth_offset
            self.beam.draw(screen, mouth_pos)

    # 本体だけ描画（前面）
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
#  ガスターブラスター管理クラス
# ============================
class ScheduledBlaster:
    def __init__(self, pos, angle, delay):
        self.pos = pos
        self.angle = angle
        self.delay = delay
        self.elapsed = 0


class GasterBlasterManager:
    def __init__(self):
        self.active = []
        self.scheduled = []

    def spawn_blaster(self, pos, angle, delay_ms):
        self.scheduled.append(ScheduledBlaster(pos, angle, delay_ms))

    def update(self, dt):
        # 予約処理
        for s in self.scheduled[:]:
            s.elapsed += dt
            if s.elapsed >= s.delay:
                gb = GasterBlaster(pos=s.pos)
                gb.target_angle = s.angle
                self.active.append(gb)
                self.scheduled.remove(s)

        # 本体更新
        for gb in self.active[:]:
            gb.update(dt)

            # 画面外に消えたら削除
            if gb.current_pos.x < -300 or gb.current_pos.x > 900 or \
               gb.current_pos.y < -300 or gb.current_pos.y > 900:
                self.active.remove(gb)

    def draw(self, screen):
        # ビーム（背景）
        for gb in self.active:
            gb.draw_beam_only(screen)

        # 本体（前面）
        for gb in self.active:
            gb.draw_body_only(screen)


# ============================
#  メイン
# ============================
def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    clock = pygame.time.Clock()

    # ⭐ バトルボックス
    box = BattleBox(150, 350, 300, 200)

    # ⭐ ソウル
    soul = Soul(box)

    # ⭐ ガスターブラスター管理
    manager = GasterBlasterManager()

    # 例：召喚
    manager.spawn_blaster((300, 300), 0, 1000)

    running = True
    while running:
        dt = clock.tick(60)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 更新
        soul.update(keys)
        manager.update(dt)

        # 描画
        screen.fill((0, 0, 0))
        box.draw(screen)
        soul.draw(screen)
        manager.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
