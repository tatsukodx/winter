import pygame
import math
import random

# ============================================================
# Animation
# ============================================================
class Animation:
    def __init__(self, frames, duration, loop):
        self.frames = frames
        self.duration = duration
        self.loop = loop
        self.timer = 0
        self.index = 0
        self.finished = False

    def update(self, dt):
        if self.finished:
            return

        self.timer += dt
        if self.timer >= self.duration:
            self.timer = 0
            self.index += 1

            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1
                    self.finished = True

    def get(self):
        return self.frames[self.index]


# ============================================================
# Beam（太さ対応 OBB 当たり判定＋フェードアウト）
# ============================================================
class Beam:
    def __init__(self, angle, duration):
        self.angle = angle
        self.length = 0
        self.width = 30
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

        # フェードアウト
        if self.timer > self.duration:
            t = (self.timer - self.duration) / self.fade_duration
            t = min(t, 1)
            self.alpha = int(255 * (1 - t))

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


# ============================================================
# GasterBlaster
# ============================================================
class GBState:
    APPEAR = 0
    OPEN = 1
    DISAPPEAR = 2


class GasterBlaster:
    def __init__(self, pos=(300, 300), beam_duration=600, fire_delay=1000):
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
        self.start_pos = pygame.Vector2(random.randint(0, 600), random.randint(0, 600))
        self.current_pos = self.start_pos.copy()

        self.alpha = 0
        self.appear_time = 0
        self.appear_duration = 800

        self.target_angle = 0
        self.angle = self.target_angle + 360

        self.beam_duration = beam_duration
        self.fire_delay = fire_delay
        self.fire_timer = 0

        self.beam = None

        self.snd_charge = pygame.mixer.Sound("sound/gasterblaster/charge.mp3")
        self.snd_fire = pygame.mixer.Sound("sound/gasterblaster/fire.mp3")
        self.snd_charge.play()

    def update(self, dt):
        # APPEAR
        if self.state == GBState.APPEAR:
            self.appear_time += dt
            t = min(self.appear_time / self.appear_duration, 1)

            self.current_pos = self.start_pos.lerp(self.final_pos, t)
            self.alpha = int(255 * t)
            self.angle = self.target_angle + (1 - t) * 360

            if t >= 1:
                self.state = GBState.OPEN
                self.current_anim = self.anim_open

        # OPEN（開ききったら fire_delay 待ち → 発射）
        elif self.state == GBState.OPEN:
            self.current_anim.update(dt)

            if self.current_anim.finished:
                self.fire_timer += dt
                if self.fire_timer >= self.fire_delay:
                    self.state = GBState.DISAPPEAR
                    self.current_anim = self.anim_disappear
                    self.beam = Beam(self.target_angle, self.beam_duration)
                    self.snd_fire.play()

        # DISAPPEAR
        elif self.state == GBState.DISAPPEAR:
            self.current_anim.update(dt)
            if self.beam:
                self.beam.update(dt)

    def draw(self, screen):
        img = self.current_anim.get().copy()
        img.set_alpha(self.alpha)

        rotated = pygame.transform.rotate(img, self.angle)
        rect = rotated.get_rect(center=self.current_pos)
        screen.blit(rotated, rect)

        if self.beam:
            mouth_offset = pygame.Vector2(0, 40).rotate(-(self.target_angle + 90))
            root_pos = self.current_pos + mouth_offset
            self.beam.draw(screen, root_pos)


# ============================================================
# ScheduledBlaster
# ============================================================
class ScheduledBlaster:
    def __init__(self, pos, angle, fire_delay):
        self.pos = pos
        self.angle = angle
        self.fire_delay = fire_delay
        self.spawned = False


# ============================================================
# GasterBlasterManager（sequence対応）
# ============================================================
class GasterBlasterManager:
    def __init__(self):
        self.scheduled = []
        self.active = []
        self.commands = []
        self.command_timer = 0

    def spawn_blaster(self, pos, angle, fire_delay):
        self.scheduled.append(ScheduledBlaster(pos, angle, fire_delay))

    def sequence(self, commands):
        self.commands = commands
        self.command_timer = 0

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

        # 1体ずつ出現
        for s in self.scheduled:
            if not s.spawned:
                gb = GasterBlaster(pos=s.pos, beam_duration=600, fire_delay=s.fire_delay)
                gb.target_angle = s.angle
                self.active.append(gb)
                s.spawned = True
                break

        # 既存ブラスター更新
        for gb in self.active[:]:
            gb.update(dt)

            # ビームが完全に消えたら削除
            if gb.beam and gb.beam.alpha <= 0:
                self.active.remove(gb)

    def draw(self, screen):
        for gb in self.active:
            gb.draw(screen)

def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    # ソウル（仮）
    class Soul:
        def __init__(self):
            self.pos = pygame.Vector2(400, 300)
        def take_damage(self, dmg):
            print("damage:", dmg)

    soul = Soul()

    manager = GasterBlasterManager()

    # ★ 達仁がやりたい「delay(1000)」式の攻撃パターン
    manager.sequence([
        ("spawn", (300, 300), 0, 1000),
        ("wait", 1000),
        ("spawn", (100, 500), 90, 1000),
        ("wait", 1000),
        ("spawn", (500, 100), 225, 1000),
    ])

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 更新
        manager.update(dt, soul)

        # 描画
        screen.fill((0, 0, 0))
        manager.draw(screen)
        pygame.display.flip()

    pygame.quit()