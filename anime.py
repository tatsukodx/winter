import pygame
import random
import math
from enum import Enum


class GBState(Enum):
    APPEAR = 0
    OPEN = 1
    DISAPPEAR = 2


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


class GasterBlaster:
    def __init__(self, pos=(300, 300)):
        # 出現：1
        appear_frames = [
            pygame.image.load("sprite/gasterblaster/1.png").convert_alpha()
        ]
        self.anim_appear = Animation(appear_frames, frame_duration=200, loop=False)

        # 開口：2 → 3 → 4
        open_frames = [
            pygame.image.load("sprite/gasterblaster/2.png").convert_alpha(),
            pygame.image.load("sprite/gasterblaster/3.png").convert_alpha(),
            pygame.image.load("sprite/gasterblaster/4.png").convert_alpha(),
        ]
        self.anim_open = Animation(open_frames, frame_duration=120, loop=False)

        # 発射：5 ↔ 6 ループ
        disappear_frames = [
            pygame.image.load("sprite/gasterblaster/5.png").convert_alpha(),
            pygame.image.load("sprite/gasterblaster/6.png").convert_alpha(),
        ]
        self.anim_disappear = Animation(disappear_frames, frame_duration=150, loop=True)

        # 状態
        self.state = GBState.APPEAR
        self.current_anim = self.anim_appear

        # 出現演出用
        self.final_pos = pygame.Vector2(pos)
        self.start_pos = pygame.Vector2(
            random.randint(0, 600),
            random.randint(0, 600)
        )
        self.current_pos = self.start_pos.copy()

        self.alpha = 0
        self.appear_time = 0
        self.appear_duration = 800  # ミリ秒

        # 回転（出現中のみ）
        self.target_angle = 0
        self.angle = self.target_angle + 360  # ← 1回転分の角度を持たせる

    def update(self, dt):
        # 出現ステート
        if self.state == GBState.APPEAR:
            self.appear_time += dt
            t = min(self.appear_time / self.appear_duration, 1)

            # 減速イージング（移動）
            ease_t = 1 - (1 - t) ** 2

            # 位置補間
            self.current_pos = self.start_pos.lerp(self.final_pos, ease_t)

            # フェードイン
            self.alpha = int(255 * ease_t)

            # ⭐ 出現中のイージング回転（1回転 → target_angle）
            diff = (self.target_angle - self.angle)
            diff = (diff + 180) % 360 - 180  # -180〜180 に正規化
            self.angle += diff / 6  # ← 残り角度 / 6

            # 出現完了 → 開口へ
            if t >= 1:
                self.state = GBState.OPEN
                self.current_anim = self.anim_open

        # 開口ステート
        elif self.state == GBState.OPEN:
            self.current_anim.update(dt)

            if self.current_anim.finished:
                self.state = GBState.DISAPPEAR
                self.current_anim = self.anim_disappear

        # 発射ステート（回転なし）
        elif self.state == GBState.DISAPPEAR:
            self.current_anim.update(dt)

    def draw(self, screen):
        frame = self.current_anim.get_frame().copy()

        # 出現中：透明度＋回転
        if self.state == GBState.APPEAR:
            frame.set_alpha(self.alpha)
            frame = pygame.transform.rotate(frame, self.angle)

        # 開口中：回転なし
        elif self.state == GBState.OPEN:
            pass

        # 発射中：target_angle の向きで固定
        elif self.state == GBState.DISAPPEAR:
            frame = pygame.transform.rotate(frame, self.target_angle)

        rect = frame.get_rect(center=self.current_pos)
        screen.blit(frame, rect)


def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    clock = pygame.time.Clock()

    gb = GasterBlaster(pos=(300, 300))

    # ⭐ 発射方向を指定（例：右向き）
    gb.target_angle = 0

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        gb.update(dt)

        screen.fill((0, 0, 0))
        gb.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
