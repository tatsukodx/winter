print("pygame 起動したよ")
import pygame
import sys
import math
import random

pygame.mixer.init = lambda *args, **kwargs: None

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sans-like Gaster Blaster Test")
clock = pygame.time.Clock()

# プレイヤー
player = pygame.Rect(WIDTH // 2, HEIGHT // 2, 30, 30)
PLAYER_SPEED = 5

# ガスターブラスター画像（6枚アニメーション）
gb_frames = []
for i in range(1, 7):
    img = pygame.image.load(f"sprite/gasterblaster/{i}.png").convert_alpha()
    img = pygame.transform.scale(img, (120, 120))
    gb_frames.append(img)

ANIM_SPEED = 80  # msごとに次のフレームへ（調整可）


class GasterBlaster:
    def __init__(self):
        # 出現位置（画面外）
        self.x = random.choice([-100, WIDTH + 100])
        self.y = random.randint(50, HEIGHT - 50)

        # プレイヤー方向の角度
        dx = player.centerx - self.x
        dy = player.centery - self.y
        self.angle = math.degrees(math.atan2(-dy, dx))

        # アニメーション
        self.frame = 0
        self.last_anim = pygame.time.get_ticks()

        # 回転済み画像を保持
        self.rotated_frames = [
            pygame.transform.rotate(frame, self.angle) for frame in gb_frames
        ]

        self.rect = self.rotated_frames[0].get_rect(center=(self.x, self.y))

        # ビーム関連
        self.beam_active = False
        self.beam_duration = 300  # ms
        self.beam_start = None

    def update(self):
      now = pygame.time.get_ticks()

      # アニメーション更新
      if now - self.last_anim > ANIM_SPEED:
          self.last_anim = now
          self.frame += 1

          # 最終フレームに到達したらビーム発射
          if self.frame >= len(self.rotated_frames):
              self.frame = len(self.rotated_frames) - 1
              if not self.beam_active:
                  self.beam_active = True
                  self.beam_start = now

      # ビーム終了後は消滅
      if self.beam_active and self.beam_start is not None:
          if now - self.beam_start > self.beam_duration:
              return False

      return True

    def draw(self, surface):
        surface.blit(self.rotated_frames[self.frame], self.rect)

        # ビーム描画
        if self.beam_active:
            length = 2000
            rad = math.radians(self.angle)
            x2 = self.rect.centerx + math.cos(rad) * length
            y2 = self.rect.centery - math.sin(rad) * length

            pygame.draw.line(surface, (255, 255, 255), self.rect.center, (x2, y2), 12)

    def check_hit(self, player_rect):
        if not self.beam_active:
            return False

        # ビームの線分とプレイヤー中心点の距離で判定
        rad = math.radians(self.angle)
        x2 = self.rect.centerx + math.cos(rad) * 2000
        y2 = self.rect.centery - math.sin(rad) * 2000

        px, py = player_rect.center
        dist = abs((y2 - self.rect.centery) * px - (x2 - self.rect.centerx) * py +
                   x2 * self.rect.centery - y2 * self.rect.centerx) / \
               math.hypot(x2 - self.rect.centerx, y2 - self.rect.centery)

        return dist < 20  # 当たり判定の太さ


def main():
    blasters = []
    last_spawn = 0

    while True:
        dt = clock.tick(60)

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # プレイヤー操作
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            player.x += PLAYER_SPEED
        if keys[pygame.K_UP]:
            player.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            player.y += PLAYER_SPEED

        # 画面外に出ないように
        player.clamp_ip(screen.get_rect())

        # ガスターブラスター生成（1.5秒ごと）
        now = pygame.time.get_ticks()
        if now - last_spawn > 1500:
            last_spawn = now
            blasters.append(GasterBlaster())

        # ブラスター更新＆削除
        blasters = [b for b in blasters if b.update()]

        # 当たり判定
        for b in blasters:
            if b.check_hit(player):
                print("GAME OVER")
                pygame.quit()
                sys.exit()

        # 描画
        screen.fill((0, 0, 0))
        pygame.draw.rect(screen, (255, 255, 255), player)

        for b in blasters:
            b.draw(screen)

        pygame.display.flip()


if __name__ == "__main__":
    main()