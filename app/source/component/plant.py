import random
import math

import pygame as pg

from .. import constants as c
from .. import tool
from .face_projectile import GrinSeed, targetable
from .sun_gas_effects import SunGasCloud, play_puff


class Car(pg.sprite.Sprite):
    def __init__(self, x: int, y: int, map_y: int):
        pg.sprite.Sprite.__init__(self)

        rect = tool.GFX[c.CAR].get_rect()
        width, height = rect.w, rect.h
        self.image = tool.get_image(tool.GFX[c.CAR], 0, 0, width, height)
        self.mask = pg.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y
        self.map_y = map_y
        self.state = c.IDLE
        self.dead = False

    def update(self, game_info: dict):
        self.current_time = game_info[c.CURRENT_TIME]
        if self.state == c.WALK:
            self.rect.x += 5
        if self.rect.x > c.SCREEN_WIDTH + 25:
            self.dead = True

    def setWalk(self):
        if self.state == c.IDLE:
            self.state = c.WALK
            # 播放音效
            c.SOUND_CAR_WALKING.play()

    def draw(self, surface):
        surface.blit(self.image, self.rect)


# 豌豆及孢子类普通子弹
class Bullet(pg.sprite.Sprite):
    def __init__(
        self,
        x: int,
        start_y: int,
        dest_y: int,
        name: str,
        damage: int,
        effect: str = None,
        passed_torchwood_x: int = None,
        damage_type: str = c.ZOMBIE_DEAFULT_DAMAGE,
    ):
        pg.sprite.Sprite.__init__(self)

        self.name = name
        self.frames = []
        self.frame_index = 0
        self.load_images()
        self.frame_num = len(self.frames)
        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = start_y
        self.dest_y = dest_y
        self.y_vel = 15 if (dest_y > start_y) else -15
        self.x_vel = 10
        self.damage = damage
        self.damage_type = damage_type
        self.effect = effect
        self.state = c.FLY
        self.current_time = 0
        self.animate_timer = 0
        self.animate_interval = 70
        self.passed_torchwood_x = (
            passed_torchwood_x  # 记录最近通过的火炬树横坐标，如果没有缺省为None
        )

    def loadFrames(self, frames, name):
        frame_list = tool.GFX[name]
        if name in c.PLANT_RECT:
            data = c.PLANT_RECT[name]
            x, y, width, height = (
                data['x'],
                data['y'],
                data['width'],
                data['height'],
            )
        else:
            x, y = 0, 0
            rect = frame_list[0].get_rect()
            width, height = rect.w, rect.h

        for frame in frame_list:
            frames.append(tool.get_image(frame, x, y, width, height))

    def load_images(self):
        self.fly_frames = []
        self.explode_frames = []

        fly_name = self.name
        if self.name in c.BULLET_INDEPENDENT_BOOM_IMG:
            explode_name = f'{self.name}Explode'
        else:
            explode_name = 'PeaNormalExplode'

        self.loadFrames(self.fly_frames, fly_name)
        self.loadFrames(self.explode_frames, explode_name)

        self.frames = self.fly_frames

    def update(self, game_info):
        self.current_time = game_info[c.CURRENT_TIME]
        if self.state == c.FLY:
            if self.rect.y != self.dest_y:
                self.rect.y += self.y_vel
                if self.y_vel * (self.dest_y - self.rect.y) < 0:
                    self.rect.y = self.dest_y
            self.rect.x += self.x_vel
            if self.rect.x >= c.SCREEN_WIDTH + 20:
                self.kill()
        elif self.state == c.EXPLODE:
            if (self.current_time - self.explode_timer) > 250:
                self.kill()
        if self.current_time - self.animate_timer >= self.animate_interval:
            self.frame_index += 1
            self.animate_timer = self.current_time
            if self.frame_index >= self.frame_num:
                self.frame_index = 0
            self.image = self.frames[self.frame_index]

    def setExplode(self, play_sound=True):
        if self.state != c.FLY:
            return
        self.state = c.EXPLODE
        self.explode_timer = self.current_time
        self.frames = self.explode_frames
        self.frame_num = len(self.frames)
        self.image = self.frames[0]
        self.mask = pg.mask.from_surface(self.image)

        # 播放子弹爆炸音效
        if not play_sound:
            return
        if self.name == c.BULLET_FIREBALL:
            c.SOUND_FIREPEA_EXPLODE.play()
        else:
            c.SOUND_BULLET_EXPLODE.play()

    def draw(self, surface):
        surface.blit(self.image, self.rect)


# 大喷菇的烟雾
# 仅有动画效果，不参与攻击运算
class Fume(pg.sprite.Sprite):
    def __init__(self, x, y):
        pg.sprite.Sprite.__init__(self)
        self.name = c.FUME
        self.timer = 0
        self.frame_index = 0
        self.load_images()
        self.frame_num = len(self.frames)
        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def load_images(self):
        self.fly_frames = []

        fly_name = self.name

        self.loadFrames(self.fly_frames, fly_name)

        self.frames = self.fly_frames

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self, game_info):
        self.current_time = game_info[c.CURRENT_TIME]
        if self.current_time - self.timer >= 100:
            self.frame_index += 1
            if self.frame_index >= self.frame_num:
                self.frame_index = self.frame_num - 1
                self.kill()
            self.timer = self.current_time
        self.image = self.frames[self.frame_index]

    def loadFrames(self, frames, name):
        frame_list = tool.GFX[name]
        x, y = 0, 0
        rect = frame_list[0].get_rect()
        width, height = rect.w, rect.h

        for frame in frame_list:
            frames.append(tool.get_image(frame, x, y, width, height))


# 杨桃的子弹
class StarBullet(Bullet):
    def __init__(
        self,
        x,
        start_y,
        damage,
        direction,
        level,
        damage_type=c.ZOMBIE_DEAFULT_DAMAGE,
    ):    # direction指星星飞行方向
        Bullet.__init__(
            self,
            x,
            start_y,
            start_y,
            c.BULLET_STAR,
            damage,
            damage_type=damage_type,
        )
        self.level = level
        self.map_y = self.level.map.getMapIndex(
            self.rect.x, self.rect.centery
        )[1]
        self.direction = direction

    def update(self, game_info):
        self.current_time = game_info[c.CURRENT_TIME]
        if self.state == c.FLY:
            if self.direction == c.STAR_FORWARD_UP:
                self.rect.x += 8
                self.rect.y -= 6
            elif self.direction == c.STAR_FORWARD_DOWN:
                self.rect.x += 7
                self.rect.y += 7
            elif self.direction == c.STAR_UPWARD:
                self.rect.y -= 10
            elif self.direction == c.STAR_DOWNWARD:
                self.rect.y += 10
            else:
                self.rect.x -= 10
            self.handleMapYPosition()
            if (
                (self.rect.x > c.SCREEN_WIDTH + 20)
                or (self.rect.right < -20)
                or (self.rect.y > c.SCREEN_HEIGHT)
                or (self.rect.y < 0)
            ):
                self.kill()
        elif self.state == c.EXPLODE:
            if (self.current_time - self.explode_timer) >= 250:
                self.kill()

    # 这里用的是坚果保龄球的代码改一下，实现子弹换行
    def handleMapYPosition(self):
        if self.direction == c.STAR_UPWARD:
            map_y1 = self.level.map.getMapIndex(
                self.rect.x, self.rect.centery + 40
            )[1]
        else:
            map_y1 = self.level.map.getMapIndex(
                self.rect.x, self.rect.centery + 20
            )[1]
        if (self.map_y != map_y1) and (
            0 <= map_y1 <= self.level.map_y_len - 1
        ):    # 换行
            self.level.bullet_groups[self.map_y].remove(self)
            self.level.bullet_groups[map_y1].add(self)
            self.map_y = map_y1


class Plant(pg.sprite.Sprite):
    def __init__(self, x, y, name, health, bullet_group, scale=1):
        pg.sprite.Sprite.__init__(self)

        self.frames = []
        self.frame_index = 0
        self.loadImages(name, scale)
        self.frame_num = len(self.frames)
        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y

        self.name = name
        self.health = health
        self.max_health = health
        self.healthy_frames = self.frames
        self.state = c.IDLE
        self.bullet_group = bullet_group
        self.animate_timer = 0
        self.animate_interval = 70  # 帧播放间隔
        self.hit_timer = 0
        # 被铲子指向时间
        self.highlight_time = 0

        self.attack_check = c.CHECK_ATTACK_ALWAYS

    def loadFrames(self, frames, name, scale=1, color=c.BLACK):
        frame_list = tool.GFX[name]
        if name in c.PLANT_RECT:
            data = c.PLANT_RECT[name]
            x, y, width, height = (
                data['x'],
                data['y'],
                data['width'],
                data['height'],
            )
        else:
            x, y = 0, 0
            rect = frame_list[0].get_rect()
            width, height = rect.w, rect.h

        for frame in frame_list:
            frames.append(
                tool.get_image(frame, x, y, width, height, color, scale)
            )

    def loadImages(self, name, scale):
        self.loadFrames(self.frames, name, scale)

    def changeFrames(self, frames):
        # change image frames and modify rect position
        self.frames = frames
        self.frame_num = len(self.frames)
        self.frame_index = 0

        bottom = self.rect.bottom
        x = self.rect.x
        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.bottom = bottom
        self.rect.x = x

    def update(self, game_info):
        self.current_time = game_info[c.CURRENT_TIME]
        self.handleState()
        self.animation()

    def handleState(self):
        if self.state == c.IDLE:
            self.idling()
        elif self.state == c.ATTACK:
            self.attacking()
        elif self.state == c.DIGEST:
            self.digest()

    def idling(self):
        pass

    def attacking(self):
        pass

    def digest(self):
        pass

    def animation(self):
        if (self.current_time - self.animate_timer) > self.animate_interval:
            self.frame_index += 1
            if self.frame_index >= self.frame_num:
                self.frame_index = 0
            self.animate_timer = self.current_time

        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)
        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif (self.current_time - self.hit_timer) < 200:
            self.image.set_alpha(192)
        else:
            self.image.set_alpha(255)

    def canAttack(self, zombie):
        if (zombie.name == c.SNORKELZOMBIE) and (
            zombie.frames == zombie.swim_frames
        ):
            return False
        if (
            self.state != c.SLEEP
            and zombie.state != c.DIE
            and self.rect.x <= zombie.rect.right
            and zombie.rect.x <= c.SCREEN_WIDTH - 24
        ):
            return True
        return False

    def setAttack(self):
        self.state = c.ATTACK

    def setIdle(self):
        self.state = c.IDLE
        self.is_attacked = False

    def setSleep(self):
        self.state = c.SLEEP
        self.changeFrames(self.sleep_frames)

    def setDamage(self, damage, zombie):
        if not zombie.losthead:
            self.health -= damage
        self.hit_timer = self.current_time
        if (
            (self.name == c.HYPNOSHROOM)
            and (self.state != c.SLEEP)
            and (zombie.name not in {c.ZOMBONI, '投石车僵尸（未实现）', '加刚特尔（未实现）'})
        ):
            self.zombie_to_hypno = zombie

    def heal(self, amount):
        """Restore living plants without resurrecting or changing their maximum HP."""
        if self.health <= 0 or not self.alive() or not math.isfinite(self.max_health):
            return 0
        restored = max(0, min(amount, self.max_health - self.health))
        self.health += restored
        if restored:
            thresholds = {
                c.WALLNUT: (c.WALLNUT_CRACKED1_HEALTH, c.WALLNUT_CRACKED2_HEALTH),
                c.PUMPKINHEAD: (c.WALLNUT_CRACKED1_HEALTH, c.WALLNUT_CRACKED2_HEALTH),
                c.TALLNUT: (c.TALLNUT_CRACKED1_HEALTH, c.TALLNUT_CRACKED2_HEALTH),
                c.GARLIC: (c.GARLIC_CRACKED1_HEALTH, c.GARLIC_CRACKED2_HEALTH),
            }
            if self.name in thresholds:
                first, second = thresholds[self.name]
                self.cracked1, self.cracked2 = self.health <= first, self.health <= second
                frames = (self.cracked2_frames if self.cracked2 else
                          self.cracked1_frames if self.cracked1 else self.healthy_frames)
                if self.frames is not frames:
                    self.changeFrames(frames)
                    self.image = frames[0]
                    self.mask = pg.mask.from_surface(self.image)
        return restored

    def getPosition(self):
        return self.rect.centerx, self.rect.bottom


class Sun(Plant):
    def __init__(self, x, y, dest_x, dest_y, is_big=True):
        if is_big:
            scale = 0.9
            self.sun_value = c.SUN_VALUE
        else:
            scale = 0.6
            self.sun_value = 15
        Plant.__init__(self, x, y, c.SUN, 0, None, scale)
        self.move_speed = 1
        self.dest_x = dest_x
        self.dest_y = dest_y
        self.die_timer = 0

    def handleState(self):
        if self.rect.centerx != self.dest_x:
            self.rect.centerx += (
                self.move_speed
                if self.rect.centerx < self.dest_x
                else -self.move_speed
            )
        if self.rect.bottom != self.dest_y:
            self.rect.bottom += (
                self.move_speed
                if self.rect.bottom < self.dest_y
                else -self.move_speed
            )

        if (
            self.rect.centerx == self.dest_x
            and self.rect.bottom == self.dest_y
        ):
            if self.die_timer == 0:
                self.die_timer = self.current_time
            elif (self.current_time - self.die_timer) > c.SUN_LIVE_TIME:
                self.state = c.DIE
                self.kill()

    def checkCollision(self, x, y):
        if self.state == c.DIE:
            return False
        if (
            x >= self.rect.x
            and x <= self.rect.right
            and y >= self.rect.y
            and y <= self.rect.bottom
        ):
            self.state = c.DIE
            self.kill()
            return True
        return False


class GasSun(Sun):
    """Gas condenses into a sun, then ejects along an arc and bounces."""

    def __init__(self, x, y, dest_x, dest_y, now):
        super().__init__(x, y, dest_x, dest_y)
        self.launch_x, self.launch_y = x, y
        self.born = now
        self.image = pg.Surface(self.rect.size, pg.SRCALPHA)

    def handleState(self):
        age = self.current_time - self.born
        if age < 500:
            self.rect.centerx, self.rect.bottom = self.launch_x, self.launch_y
        elif age < 1600:
            progress = (age - 500) / 1100
            self.rect.centerx = round(self.launch_x + (self.dest_x - self.launch_x) * progress)
            self.rect.bottom = round(self.launch_y + (self.dest_y - self.launch_y) * progress
                                     - math.sin(progress * math.pi) * 64)
        elif age < 1900:
            progress = (age - 1600) / 300
            self.rect.centerx = self.dest_x
            self.rect.bottom = self.dest_y - round(math.sin(progress * math.pi) * 10)
        else:
            self.rect.centerx, self.rect.bottom = self.dest_x, self.dest_y
            super().handleState()

    def animation(self):
        age = self.current_time - self.born
        if age < 0:
            self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
            return
        super().animation()
        if age >= 1900:
            self.rect = self.image.get_rect(midbottom=(self.dest_x, self.rect.bottom))
            return
        anchor = self.rect.midbottom
        size = 108
        canvas = pg.Surface((size, size), pg.SRCALPHA)
        progress = min(1, age / 500)
        # The sun is visibly formed, rather than appearing full-size at once.
        radius = round(7 + progress * 29)
        for ring in range(3):
            color = (155, 214, 55, 90) if progress < .5 else (255, 210, 45, 75)
            pg.draw.circle(canvas, color, (54, 54), radius + 8 - ring * 3, 2)
        for index in range(8):
            angle = age / 160 + index * math.tau / 8
            reach = radius + 7
            point = (54 + math.cos(angle) * reach, 54 + math.sin(angle) * reach)
            pg.draw.circle(canvas, (255, 244, 124, 220), point, 2)
        scale = .1 + .75 * progress
        token = pg.transform.rotozoom(self.image.convert_alpha(), -age / 18, scale)
        token.set_alpha(round(80 + progress * 175))
        canvas.blit(token, token.get_rect(center=(54, 54)))
        self.image = canvas
        self.rect = canvas.get_rect(midbottom=anchor)
        self.mask = pg.mask.from_surface(canvas)

    def checkCollision(self, x, y):
        # Invisible gas and an unformed sun cannot be collected prematurely.
        if getattr(self, 'current_time', 0) < self.born + 500:
            return False
        return super().checkCollision(x, y)


class SunFlower(Plant):
    def __init__(self, x, y, sun_group):
        Plant.__init__(self, x, y, c.SUNFLOWER, c.PLANT_HEALTH, None)
        self.sun_timer = 0
        self.sun_group = sun_group
        self.attack_check = c.CHECK_ATTACK_NEVER

    def idling(self):
        if self.sun_timer == 0:
            self.sun_timer = self.current_time - (c.FLOWER_SUN_INTERVAL - 6000)
        elif (self.current_time - self.sun_timer) > c.FLOWER_SUN_INTERVAL:
            self.sun_group.add(
                Sun(
                    self.rect.centerx,
                    self.rect.bottom,
                    self.rect.right,
                    self.rect.bottom + self.rect.h // 2,
                )
            )
            self.sun_timer = self.current_time


class GasSunFlower(Plant):
    """大头屁日葵：保留喷烟动画，每轮产出一颗阳光。"""

    def __init__(self, x, y, sun_group, effect_group):
        super().__init__(x, y, c.GASSUNFLOWER, c.GASSUNFLOWER_HEALTH, None)
        self.sun_group = sun_group
        self.effect_group = effect_group
        self.attack_check = c.CHECK_ATTACK_NEVER
        self.idle_frames = self.frames
        self.charge_frames = tool.GFX[c.GASSUNFLOWER + 'Charge']
        self.release_frames = tool.GFX[c.GASSUNFLOWER + 'Release']
        self.next_burst = None
        self.last_burst = None

    def update(self, game_info):
        self.current_time = game_info[c.CURRENT_TIME]
        if self.health <= 0:
            return
        if self.next_burst is None:
            self.next_burst = self.current_time + c.GASSUNFLOWER_FIRST_SUN_DELAY
        if self.current_time >= self.next_burst:
            self._produce(game_info.get(c.SOUND_VOLUME, 1))
            self.last_burst = self.current_time
            self.next_burst = self.current_time + c.GASSUNFLOWER_SUN_INTERVAL
        if self.last_burst is not None and self.current_time - self.last_burst < 1100:
            frames = self.release_frames
            index = min(7, int((self.current_time - self.last_burst) / 140))
        elif self.next_burst - self.current_time <= 1200:
            frames = self.charge_frames
            index = min(7, max(0, int((1200 - self.next_burst + self.current_time) / 150)))
        else:
            frames = self.idle_frames
            index = int(self.current_time / 110) % len(frames)
        self.frames = frames
        self.frame_num = len(frames)
        self.frame_index = index
        self.image = frames[index].copy()
        self.mask = pg.mask.from_surface(self.image)
        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif self.current_time - self.hit_timer < 200:
            self.image.set_alpha(192)

    def _produce(self, volume):
        # Facing right puts the rear on the left; keep the sun collectible
        # even when planted in the leftmost column.
        from . import plant_layout
        x, bottom = plant_layout.point(self, (self.rect.centerx - 28, self.rect.bottom - 25))
        direction = -1
        self.effect_group.add(SunGasCloud((x, bottom), self.current_time, direction))
        for index in range(c.GASSUNFLOWER_SUN_COUNT):
            dest_x = max(30, min(c.SCREEN_WIDTH - 30, x + direction * (40 + index * 42)))
            dest_y = max(105, min(c.SCREEN_HEIGHT - 25, self.rect.bottom + 10 - index * 5))
            # The 108px forming-sun canvas is bottom-anchored; offset it so
            # the glowing center forms in the rear cloud, not over the face.
            origin_x = max(30, min(c.SCREEN_WIDTH - 30, x + 26 * direction))
            self.sun_group.add(GasSun(origin_x, bottom + 54, dest_x, dest_y,
                                      self.current_time + 220 + index * 200))
        play_puff(volume)


class PortraitHealer(Plant):
    """Heal after 2 seconds, then every 15 seconds; no revival or overhealing."""

    def __init__(self, x, y, level):
        super().__init__(x, y, c.PORTRAITHEALER, c.PORTRAITHEALER_HEALTH, None)
        self.level = level
        self.attack_check = c.CHECK_ATTACK_NEVER
        self.next_heal = level.current_time + c.PORTRAITHEALER_FIRST_HEAL_DELAY
        self.last_heal = None
        self.phase = 'Idle'
        self.pulse_count = 0
        self.neutral_mask = self.mask.copy()

    def loadImages(self, name, scale):
        self.frames = tool.GFX[name]

    def pulse(self, now):
        from .portrait_healer import HealingWave, HealingBar
        cell = self.level.map.getMapIndex(*self.getPosition())
        recipients = []
        for row in range(max(0, cell[1] - 1), min(self.level.map_y_len, cell[1] + 2)):
            for target in self.level.plant_groups[row]:
                if (target.name not in c.PLANT_CARD_INDEX or target.health <= 0
                        or target.state == c.DIE or not target.alive()
                        or not math.isfinite(target.max_health)
                        or not math.isfinite(target.health)
                        or getattr(target, 'start_boom', False)
                        or getattr(target, 'triggered_at', None) is not None):
                    continue
                tx, ty = self.level.map.getMapIndex(*target.getPosition())
                if abs(tx - cell[0]) > 1 or abs(ty - cell[1]) > 1:
                    continue
                if now < getattr(target, 'next_portrait_heal', 0):
                    continue
                before = target.health
                amount = target.heal(min(target.max_health * c.PORTRAITHEALER_FRACTION,
                                         c.PORTRAITHEALER_MAX_HEAL))
                if amount:
                    target.next_portrait_heal = now + c.PORTRAITHEALER_RECIPIENT_COOLDOWN
                    from .plant_layout import root as visual_root
                    recipients.append((visual_root(target), amount))
                    # One health bar per recipient, including overlapping healer pulses.
                    previous = getattr(target, 'healing_bar', None)
                    if previous is not None and previous.alive():
                        displayed = previous.displayed_health(now)
                        previous.kill()
                    else:
                        displayed = before
                    bar = HealingBar(target, displayed, now)
                    target.healing_bar = bar
                    self.level.heal_effects.add(bar)
                    if target.name == c.PORTRAITTALLNUT:
                        target.update({c.CURRENT_TIME: now})
        self.level.heal_effects.add(HealingWave(self.level, cell, recipients, now))
        self.last_heal = now
        self.pulse_count += 1

    def update(self, game_info):
        self.current_time = now = game_info[c.CURRENT_TIME]
        if self.health <= 0 or not self.alive() or self.state == c.SLEEP:
            return
        if now >= self.next_heal:
            self.pulse(now)
            self.next_heal += ((now - self.next_heal) // c.PORTRAITHEALER_INTERVAL + 1) * c.PORTRAITHEALER_INTERVAL
        since = None if self.last_heal is None else now - self.last_heal
        if since is not None and since < 700:
            phase, t = 'Release', since / 700
        elif since is not None and since < 1300:
            phase, t = 'Recover', (since - 700) / 600
        elif self.next_heal - now <= 1200:
            phase, t = 'Charge', 1 - (self.next_heal - now) / 1200
        else:
            phase, t = 'Idle', (now % 2400) / 2400
        self.phase = phase
        self.frames = tool.GFX[self.name + phase]
        self.frame_num = len(self.frames)
        self.frame_index = max(0, min(self.frame_num - 1, int(t * (self.frame_num - 1))))
        self.image = self.frames[self.frame_index].copy()
        if now - self.hit_timer < 180:
            self.image.fill((30, 10, 8, 0), special_flags=pg.BLEND_RGBA_ADD)
        if now - self.highlight_time < 100:
            self.image.set_alpha(150)
        self.mask = self.neutral_mask


class PeaShooter(Plant):
    def __init__(self, x, y, bullet_group):
        Plant.__init__(self, x, y, c.PEASHOOTER, c.PLANT_HEALTH, bullet_group)
        self.shoot_timer = 0

    def attacking(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.current_time - 700
        elif (self.current_time - self.shoot_timer) >= 1400:
            self.bullet_group.add(
                Bullet(
                    self.rect.right - 15,
                    self.rect.y,
                    self.rect.y,
                    c.BULLET_PEA,
                    c.BULLET_DAMAGE_NORMAL,
                    effect=None,
                )
            )
            self.shoot_timer = self.current_time
            # 播放发射音效
            c.SOUND_SHOOT.play()

    def setAttack(self):
        self.state = c.ATTACK
        if self.shoot_timer != 0:
            self.shoot_timer = self.current_time - 700


class GrinDevourer(Plant):
    """保留跨行追踪，但只发射低伤害、非穿透的单颗子弹。"""

    def __init__(self, x, y, level):
        Plant.__init__(
            self, x, y, c.GRINDEVOURER, c.GRINDEVOURER_HEALTH, None
        )
        self.idle_frames = self.frames
        self.attack_frames = tool.GFX[f'{c.GRINDEVOURER}Attack']
        self.level = level
        self.bullet_groups = level.bullet_groups
        self.shoot_timer = None
        self.last_shot = None
        self.animate_interval = 110

    def loadImages(self, name, scale):
        self.frames = tool.GFX[name]

    def attacking(self):
        if self.shoot_timer is None:
            self.shoot_timer = self.current_time
        elif (
            self.current_time - self.shoot_timer
            >= c.GRINDEVOURER_SHOOT_INTERVAL
        ):
            # 一次只发一颗；留在种植行的子弹组中，仍可跨行追踪。
            _, row = self.level.map.getMapIndex(self.rect.centerx, self.rect.bottom)
            muzzle_x, muzzle_y = tool.GFX[self.name + 'Muzzle']
            from .plant_layout import point as visual_point
            origin = visual_point(self, (self.rect.centerx + muzzle_x, self.rect.bottom + muzzle_y))
            self.bullet_groups[row].add(
                GrinSeed(*origin,
                         self.level, row, self.current_time)
            )
            self.shoot_timer = self.current_time
            self.last_shot = self.current_time
            c.SOUND_SHOOT.play()

    def canAttack(self, zombie):
        # 无视种植行，只要场上存在可攻击僵尸就会进入攻击状态。
        return targetable(zombie)

    def setAttack(self):
        if self.state != c.ATTACK:
            self.state = c.ATTACK

    def setIdle(self):
        if self.state != c.IDLE:
            self.state = c.IDLE

    def animation(self):
        from .grin_animation import WINDUP_MS, FIRE_MS, RECOVER_MS

        now = self.current_time
        since_shot = None if self.last_shot is None else now - self.last_shot
        if since_shot is not None and since_shot < FIRE_MS:
            phase, progress = 'Fire', since_shot / FIRE_MS
        elif since_shot is not None and since_shot < FIRE_MS + RECOVER_MS:
            phase, progress = 'Recover', (since_shot - FIRE_MS) / RECOVER_MS
        elif self.state == c.ATTACK and self.shoot_timer is not None:
            remaining = c.GRINDEVOURER_SHOOT_INTERVAL - (now - self.shoot_timer)
            if remaining <= WINDUP_MS:
                phase, progress = 'Attack', 1 - max(0, remaining) / WINDUP_MS
            else:
                phase, progress = '', (now % 1920) / 1920
        else:
            phase, progress = '', (now % 1920) / 1920
        frames = tool.GFX[self.name + phase]
        self.animation_phase = phase or 'Idle'
        self.frame_index = min(len(frames) - 1, max(0, int(progress * len(frames))))
        self.frames, self.frame_num = frames, len(frames)
        self.image = frames[self.frame_index].copy()
        if 0 <= now - self.hit_timer < 200:
            self.image.fill((45, 20, 10, 0), special_flags=pg.BLEND_RGBA_ADD)
        if now - self.highlight_time < 100:
            self.image.set_alpha(150)
        self.mask = pg.mask.from_surface(self.image)


class HeadphoneBoxer(Plant):
    """Short-range three-hit combo; damage happens on the punch contact frames."""

    def __init__(self, x, y, level, row):
        super().__init__(x, y, c.HEADPHONEBOXER, c.HEADPHONEBOXER_HEALTH, None)
        self.level, self.row = level, row
        self.attack_check = c.CHECK_ATTACK_NEVER
        self.combo_started = None
        self.next_combo = 0
        self.hit_index = 0
        self.facing = 1
        self.pose_index = 0
        self.last_contact = None
        self.neutral_mask = pg.mask.from_surface(tool.GFX[self.name + 'Poses'][0])

    def loadImages(self, name, scale):
        self.frames = tool.GFX[name]

    def _targets(self, direction=None):
        result = []
        for enemy in self.level.zombie_groups[self.row]:
            if not targetable(enemy):
                continue
            dx = enemy.rect.centerx - self.rect.centerx
            if not (-c.HEADPHONEBOXER_BACK_RANGE <= dx <= c.HEADPHONEBOXER_FRONT_RANGE):
                continue
            if direction is not None and dx * direction < 0:
                continue
            result.append(enemy)
        return sorted(result, key=lambda e: abs(e.rect.centerx - self.rect.centerx))

    def update(self, game_info):
        from .headphone_boxer import PunchImpact, play_punch

        self.current_time = now = game_info[c.CURRENT_TIME]
        if self.health <= 0:
            return
        if self.combo_started is None and now >= self.next_combo:
            targets = self._targets()
            if targets:
                self.combo_started, self.hit_index = now, 0
                self.facing = 1 if targets[0].rect.centerx >= self.rect.centerx else -1
                self.state = c.ATTACK
        if self.combo_started is not None:
            age = now - self.combo_started
            while self.hit_index < len(c.HEADPHONEBOXER_HITS) and age >= c.HEADPHONEBOXER_HITS[self.hit_index][0]:
                _, damage = c.HEADPHONEBOXER_HITS[self.hit_index]
                self.hit_index += 1
                targets = self._targets(self.facing)
                if targets:
                    enemy = targets[0]
                    enemy.setDamage(damage, damage_type=c.ZOMBIE_DEAFULT_DAMAGE)
                    self.last_contact = now
                    point = (max(enemy.rect.left + 5, min(enemy.rect.right - 5, self.rect.centerx + self.facing * 75)),
                             max(enemy.rect.top + 10, min(enemy.rect.bottom - 10, self.rect.bottom - 65)))
                    heavy = self.hit_index == len(c.HEADPHONEBOXER_HITS)
                    self.level.bullet_groups[self.row].add(PunchImpact(point, now, self.facing, heavy))
                    play_punch(game_info.get(c.SOUND_VOLUME, 1), heavy)
            if age >= c.HEADPHONEBOXER_COMBO_MS:
                self.next_combo = self.combo_started + c.HEADPHONEBOXER_COMBO_MS
                self.combo_started = None
                self.state = c.IDLE
            else:
                self.pose_index = (2 if age < 250 else 3 if age < 430 else
                                   2 if age < 550 else 4 if age < 720 else
                                   5 if age < 900 else 6 if age < 1100 else 7)
        if self.combo_started is None:
            self.pose_index = 0
            image = self.frames[(now // 90) % len(self.frames)].copy()
        else:
            image = tool.GFX[self.name + 'Poses'][self.pose_index].copy()
        neutral = tool.GFX[self.name + 'Poses'][0]
        if self.facing < 0:
            image = pg.transform.flip(image, True, False)
            self.mask = pg.mask.from_surface(pg.transform.flip(neutral, True, False))
        else:
            self.mask = self.neutral_mask
        if 0 <= now - self.hit_timer < 200:
            image.fill((45, 22, 12, 0), special_flags=pg.BLEND_RGBA_ADD)
        if now - self.highlight_time < 100:
            image.set_alpha(150)
        self.image = image


class RepeaterPea(Plant):
    def __init__(self, x, y, bullet_group):
        Plant.__init__(self, x, y, c.REPEATERPEA, c.PLANT_HEALTH, bullet_group)
        self.shoot_timer = 0

        # 是否发射第一颗
        self.first_shot = False

    def attacking(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.current_time - 700
        elif self.current_time - self.shoot_timer >= 1400:
            self.first_shot = True
            self.bullet_group.add(
                Bullet(
                    self.rect.right - 15,
                    self.rect.y,
                    self.rect.y,
                    c.BULLET_PEA,
                    c.BULLET_DAMAGE_NORMAL,
                    effect=None,
                )
            )
            self.shoot_timer = self.current_time
            # 播放发射音效
            c.SOUND_SHOOT.play()
        elif self.first_shot and (self.current_time - self.shoot_timer) > 100:
            self.first_shot = False
            self.bullet_group.add(
                Bullet(
                    self.rect.right - 15,
                    self.rect.y,
                    self.rect.y,
                    c.BULLET_PEA,
                    c.BULLET_DAMAGE_NORMAL,
                    effect=None,
                )
            )
            # 播放发射音效
            c.SOUND_SHOOT.play()

    def setAttack(self):
        self.state = c.ATTACK
        if self.shoot_timer != 0:
            self.shoot_timer = self.current_time - 700


class PortraitThreepeater(Plant):
    """Three human mouths shoot into the three adjacent, valid lawn lanes."""
    CHARGE_MS = 350

    def __init__(self, x, y, level):
        super().__init__(x, y, c.PORTRAITTHREEPEATER, c.PLANT_HEALTH, None)
        self.level = level
        self.col, self.row = level.map.getMapIndex(x, y)
        self.current_time = level.current_time
        self.attack_check = c.CHECK_ATTACK_NEVER
        self.next_shot = None
        self.last_shot = None
        self.volley_count = 0
        self.phase = 'Idle'
        self.neutral_mask = self.mask.copy()
        self.mask = self.neutral_mask

    def loadImages(self, name, scale):
        self.frames = tool.GFX[name]

    def lanes(self):
        return [(head, row) for head, row in enumerate(range(self.row - 1, self.row + 2))
                if 0 <= row < self.level.map_y_len
                and self.level.map.map[row][self.col][c.MAP_PLOT_TYPE] != c.MAP_UNAVAILABLE]

    def has_targets(self):
        return any(targetable(z) and not getattr(z, 'is_hypno', False)
                   and z.rect.right >= self.rect.centerx
                   for _, row in self.lanes() for z in self.level.zombie_groups[row])

    def fire(self, now):
        from .portrait_threepeater import PortraitPea, MuzzlePuff, COLORS
        from .plant_layout import point as visual_point
        mouths = tool.GFX[self.name + 'Mouths']
        for head, row in self.lanes():
            mx, my = mouths[head]
            start = visual_point(self, (self.rect.x + mx, self.rect.y + my))
            dest_y = self.level.map.getMapGridPos(self.col, row)[1] - 55
            pea = PortraitPea(start, dest_y, row, head, now, self.level)
            self.level.bullet_groups[row].add(pea)
            self.level.head_group.add(MuzzlePuff(start, COLORS[head], now))
        c.SOUND_SHOOT.play()
        self.volley_count += 1
        self.last_shot = now

    def update(self, game_info):
        now = self.current_time = game_info[c.CURRENT_TIME]
        if not self.alive() or self.health <= 0 or self.state in (c.SLEEP, c.DIE):
            return
        active = self.has_targets()
        self.state = c.ATTACK if active else c.IDLE
        if not active:
            self.next_shot = None
        elif self.next_shot is None:
            self.next_shot = now + self.CHARGE_MS
        if active and now >= self.next_shot:
            self.fire(now)
            self.next_shot = now + c.PORTRAITTHREEPEATER_INTERVAL
        since = None if self.last_shot is None else now - self.last_shot
        if since is not None and since < 180:
            phase, t = 'Shoot', since / 180
        elif since is not None and since < 500:
            phase, t = 'Recover', (since - 180) / 320
        elif self.next_shot is not None and self.next_shot - now <= self.CHARGE_MS:
            phase, t = 'Charge', 1 - (self.next_shot - now) / self.CHARGE_MS
        else:
            phase, t = 'Idle', now % 2400 / 2400
        self.phase = phase
        self.frames = tool.GFX[self.name + phase]
        self.frame_num = len(self.frames)
        self.frame_index = min(self.frame_num - 1, max(0, int(t * (self.frame_num - 1))))
        self.image = self.frames[self.frame_index].copy()
        if now - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif now - self.hit_timer < 200:
            self.image.set_alpha(192)
        self.mask = self.neutral_mask


class ThreePeaShooter(Plant):
    def __init__(self, x, y, bullet_groups, map_y, background_type):
        Plant.__init__(self, x, y, c.THREEPEASHOOTER, c.PLANT_HEALTH, None)
        self.shoot_timer = 0
        self.map_y = map_y
        self.bullet_groups = bullet_groups
        self.background_type = background_type

    def attacking(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.current_time - 700
        if (self.current_time - self.shoot_timer) >= 1400:
            offset_y = 9  # modify bullet in the same y position with bullets of other plants
            for i in range(3):
                tmp_y = self.map_y + (i - 1)
                if self.background_type in c.POOL_EQUIPPED_BACKGROUNDS:
                    if tmp_y < 0 or tmp_y >= c.GRID_POOL_Y_LEN:
                        continue
                else:
                    if tmp_y < 0 or tmp_y >= c.GRID_Y_LEN:
                        continue
                if self.background_type in {
                    c.BACKGROUND_POOL,
                    c.BACKGROUND_FOG,
                    c.BACKGROUND_ROOF,
                    c.BACKGROUND_ROOFNIGHT,
                }:
                    dest_y = (
                        self.rect.y + (i - 1) * c.GRID_POOL_Y_SIZE + offset_y
                    )
                else:
                    dest_y = self.rect.y + (i - 1) * c.GRID_Y_SIZE + offset_y
                self.bullet_groups[tmp_y].add(
                    Bullet(
                        self.rect.right - 15,
                        self.rect.y,
                        dest_y,
                        c.BULLET_PEA,
                        c.BULLET_DAMAGE_NORMAL,
                        effect=None,
                    )
                )
            self.shoot_timer = self.current_time
            # 播放发射音效
            c.SOUND_SHOOT.play()

    def setAttack(self):
        self.state = c.ATTACK
        if self.shoot_timer != 0:
            self.shoot_timer = self.current_time - 700


class SnowPeaShooter(Plant):
    def __init__(self, x, y, bullet_group):
        Plant.__init__(
            self, x, y, c.SNOWPEASHOOTER, c.PLANT_HEALTH, bullet_group
        )
        self.shoot_timer = 0

    def attacking(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.current_time - 700
        elif (self.current_time - self.shoot_timer) >= 1400:
            self.bullet_group.add(
                Bullet(
                    self.rect.right - 15,
                    self.rect.y,
                    self.rect.y,
                    c.BULLET_PEA_ICE,
                    c.BULLET_DAMAGE_NORMAL,
                    effect=c.BULLET_EFFECT_ICE,
                )
            )
            self.shoot_timer = self.current_time
            # 播放发射音效
            c.SOUND_SHOOT.play()
            # 播放冰子弹音效
            c.SOUND_SNOWPEA_SPARKLES.play()

    def setAttack(self):
        self.state = c.ATTACK
        if self.shoot_timer != 0:
            self.shoot_timer = self.current_time - 700


class WallNut(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.WALLNUT, c.WALLNUT_HEALTH, None)
        self.load_images()
        self.cracked1 = False
        self.cracked2 = False
        self.attack_check = c.CHECK_ATTACK_NEVER

    def load_images(self):
        self.cracked1_frames = []
        self.cracked2_frames = []

        cracked1_frames_name = self.name + '_cracked1'
        cracked2_frames_name = self.name + '_cracked2'

        self.loadFrames(self.cracked1_frames, cracked1_frames_name)
        self.loadFrames(self.cracked2_frames, cracked2_frames_name)

    def idling(self):
        if (not self.cracked1) and self.health <= c.WALLNUT_CRACKED1_HEALTH:
            self.changeFrames(self.cracked1_frames)
            self.cracked1 = True
        elif (not self.cracked2) and self.health <= c.WALLNUT_CRACKED2_HEALTH:
            self.changeFrames(self.cracked2_frames)
            self.cracked2 = True


class CherryBomb(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.CHERRYBOMB, c.INF, None)
        self.state = c.ATTACK
        self.start_boom = False
        self.boomed = False
        self.bomb_timer = 0
        self.explode_y_range = 1
        self.explode_x_range = c.GRID_X_SIZE * 1.5

    def setBoom(self):
        frame = tool.GFX[c.BOOM_IMAGE]
        rect = frame.get_rect()
        width, height = rect.w, rect.h

        old_rect = self.rect
        image = tool.get_image(frame, 0, 0, width, height, c.BLACK, 1)
        self.image = image
        self.mask = pg.mask.from_surface(self.image)
        self.rect = image.get_rect()
        self.rect.centerx = old_rect.centerx
        self.rect.centery = old_rect.centery
        self.start_boom = True

    def animation(self):
        if self.start_boom:
            if self.bomb_timer == 0:
                self.bomb_timer = self.current_time
                # 播放爆炸音效
                c.SOUND_BOMB.play()
            elif (self.current_time - self.bomb_timer) > 500:
                self.health = 0
        else:
            if (self.current_time - self.animate_timer) > 100:
                self.frame_index += 1
                if self.frame_index >= self.frame_num:
                    self.setBoom()
                    return
                self.animate_timer = self.current_time

            self.image = self.frames[self.frame_index]
            self.mask = pg.mask.from_surface(self.image)

        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif (self.current_time - self.hit_timer) < 200:
            self.image.set_alpha(192)
        else:
            self.image.set_alpha(255)


class PortraitCherryBomb(Plant):
    """Two portrait fruits: idle, warning, then one area-damage event."""

    FUSE_MS = 2400

    def __init__(self, x, y, effect_group):
        super().__init__(x, y, c.PORTRAITCHERRYBOMB, c.INF, effect_group)
        self.state = c.ATTACK
        self.start_boom = False
        self.boomed = False
        self.born = None
        self.explode_y_range = 1
        self.explode_x_range = c.GRID_X_SIZE * 1.5

    def animation(self):
        from .portrait_cherry import PortraitCherryBlast

        if self.born is None:
            self.born = self.current_time
        age = self.current_time - self.born
        if age >= self.FUSE_MS:
            if not self.start_boom:
                self.start_boom = True
                from .plant_layout import point as visual_point
                origin = visual_point(self, (self.rect.centerx, self.rect.bottom - 50))
                self.bullet_group.add(PortraitCherryBlast(
                    *origin,
                    self.current_time, tool.GFX[c.PORTRAITCHERRYBOMB][0]))
                c.SOUND_BOMB.play()
                # Keep the original planting rect so damage and map cleanup
                # use the correct row; the independent effect outlives us.
                self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
                self.health = 0
            return
        key = self.name if age < 1200 else self.name + 'Warning'
        frames = tool.GFX[key]
        index = (age // 75) % len(frames) if age < 1200 else min(15, (age - 1200) // 75)
        self.image = frames[index].copy()
        self.mask = pg.mask.from_surface(self.image)
        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)


class PortraitChomper(Plant):
    """One forward target, timed bite, then exactly ten seconds of digestion."""
    REACH = 135
    BITE_MS = 550
    ATTACK_MS = 850
    DIGEST_MS = 10000

    def __init__(self, x, y, level):
        super().__init__(x, y, c.PORTRAITCHOMPER, c.PLANT_HEALTH, None)
        self.level = level
        self.current_time = level.current_time
        self.attack_check = c.CHECK_ATTACK_NEVER
        self.row = level.map.getMapIndex(x, y)[1]
        self.attack_zombie = None
        self.bite_started = None
        self.consumed_at = None
        self.digest_until = None
        self.eaten_count = 0
        self.phase = 'Idle'
        self.neutral_mask = self.mask.copy()

    def loadImages(self, name, scale):
        self.frames = tool.GFX[name]

    def valid_target(self, zombie):
        if (zombie is None or not targetable(zombie) or getattr(zombie, 'losthead', False)
                or getattr(zombie, 'is_hypno', False)
                or zombie not in self.level.zombie_groups[self.row]):
            return False
        if zombie.name == c.POLE_VAULTING_ZOMBIE and not zombie.jumped:
            return False
        if zombie.name == c.SNORKELZOMBIE and zombie.frames == zombie.swim_frames:
            return False
        return 0 <= zombie.rect.centerx - self.rect.centerx <= self.REACH

    def canAttack(self, zombie):
        return self.alive() and self.health > 0 and self.state == c.IDLE and self.valid_target(zombie)

    def setAttack(self, zombie, zombie_group=None):
        if self.canAttack(zombie):
            self.attack_zombie = zombie
            self.bite_started = self.current_time
            self.state = c.ATTACK

    def update(self, game_info):
        now = self.current_time = game_info[c.CURRENT_TIME]
        if not self.alive() or self.health <= 0 or self.state in (c.SLEEP, c.DIE):
            return
        if self.state == c.DIGEST and now >= self.digest_until:
            self.state = c.IDLE
            self.attack_zombie = None
            self.bite_started = None
        if self.state == c.IDLE:
            targets = [z for z in self.level.zombie_groups[self.row] if self.valid_target(z)]
            if targets:
                self.setAttack(min(targets, key=lambda z: z.rect.centerx))
        if self.state == c.ATTACK and now - self.bite_started >= self.BITE_MS:
            victim = self.attack_zombie
            if self.valid_target(victim):
                from .portrait_chomper import GulpedZombie
                self.level.head_group.add(GulpedZombie(victim, self, now))
                victim.health = 0
                victim.kill()
                self.attack_zombie = None
                self.consumed_at = now
                self.digest_until = now + self.DIGEST_MS
                self.eaten_count += 1
                self.state = c.DIGEST
                c.SOUND_BIGCHOMP.play()
            else:
                # A projectile/another chomper took the prey: no fake cooldown.
                self.state = c.IDLE
                self.attack_zombie = None
                self.bite_started = None
        attack_age = None if self.bite_started is None else now - self.bite_started
        if attack_age is not None and attack_age < self.ATTACK_MS:
            phase, progress = 'Attack', attack_age / self.ATTACK_MS
        elif self.state == c.DIGEST:
            remaining = self.digest_until - now
            if remaining <= 600:
                phase, progress = 'Swallow', 1 - remaining / 600
            else:
                phase, progress = 'Chew', ((now - self.consumed_at) % 800) / 800
        else:
            phase, progress = 'Idle', (now % 2200) / 2200
        self.phase = phase
        self.frames = tool.GFX[c.PORTRAITCHOMPER + phase]
        self.frame_num = len(self.frames)
        self.frame_index = min(self.frame_num - 1, int(progress * self.frame_num))
        self.image = self.frames[self.frame_index].copy()
        if now - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif now - self.hit_timer < 200:
            self.image.set_alpha(192)
        self.mask = self.neutral_mask


class Chomper(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.CHOMPER, c.PLANT_HEALTH, None)
        self.animate_interval = 140
        self.digest_timer = 0
        self.digest_interval = 15000
        self.attack_zombie = None
        self.zombie_group = None
        self.should_diggest = False

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.attack_frames = []
        self.digest_frames = []
        self.animate_interval = 100   # 本身动画播放较慢

        idle_name = name
        attack_name = name + 'Attack'
        digest_name = name + 'Digest'

        frame_list = [self.idle_frames, self.attack_frames, self.digest_frames]
        name_list = [idle_name, attack_name, digest_name]
        scale_list = [1, 1, 1]
        # rect_list = [(0, 0, 100, 114), None, None]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, scale_list[i])

        self.frames = self.idle_frames

    def canAttack(self, zombie):
        if (zombie.name in {c.POLE_VAULTING_ZOMBIE}) and (not zombie.jumped):
            return False
        if (zombie.name == c.SNORKELZOMBIE) and (
            zombie.frames == zombie.swim_frames
        ):
            return False
        elif (
            self.state == c.IDLE
            and zombie.state != c.DIGEST
            and self.rect.x <= zombie.rect.centerx
            and (not zombie.losthead)
            and (self.rect.x + c.GRID_X_SIZE * 2.7 >= zombie.rect.centerx)
        ):
            return True
        return False

    def setIdle(self):
        self.state = c.IDLE
        self.changeFrames(self.idle_frames)

    def setAttack(self, zombie, zombie_group):
        self.attack_zombie = zombie
        self.zombie_group = zombie_group
        self.state = c.ATTACK
        self.changeFrames(self.attack_frames)

    def setDigest(self):
        self.state = c.DIGEST
        self.changeFrames(self.digest_frames)

    def attacking(self):
        if self.frame_index == (self.frame_num - 3):
            # 对活着的僵尸才需要吞下去消化
            if self.attack_zombie.alive():
                if not self.should_diggest:
                    # 播放吞的音效 由于一帧在这个循环中执行了若干次，可能被设置播放若干次导致声音重叠，所以用if保护
                    # 在尚未检测到需要消化时播放音效
                    c.SOUND_BIGCHOMP.play()
                    self.should_diggest = True
                    self.attack_zombie.kill()
        if (self.frame_index + 1) == self.frame_num:
            if self.should_diggest:
                self.setDigest()
                self.should_diggest = False
            else:
                self.setIdle()

    def digest(self):
        if self.digest_timer == 0:
            self.digest_timer = self.current_time
        elif (self.current_time - self.digest_timer) > self.digest_interval:
            self.digest_timer = 0
            self.setIdle()


class PuffShroom(Plant):
    def __init__(self, x, y, bullet_group):
        Plant.__init__(self, x, y, c.PUFFSHROOM, c.PLANT_HEALTH, bullet_group)
        self.shoot_timer = 0

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.sleep_frames = []

        idle_name = name
        sleep_name = name + 'Sleep'

        frame_list = [self.idle_frames, self.sleep_frames]
        name_list = [idle_name, sleep_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.idle_frames

    def attacking(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.current_time - 700
        elif (self.current_time - self.shoot_timer) >= 1400:
            self.bullet_group.add(
                Bullet(
                    self.rect.right,
                    self.rect.y + 10,
                    self.rect.y + 10,
                    c.BULLET_MUSHROOM,
                    c.BULLET_DAMAGE_NORMAL,
                    effect=None,
                )
            )
            self.shoot_timer = self.current_time
            # 播放音效
            c.SOUND_PUFF.play()

    def canAttack(self, zombie):
        if (zombie.name == c.SNORKELZOMBIE) and (
            zombie.frames == zombie.swim_frames
        ):
            return False
        if (
            self.rect.x <= zombie.rect.right
            and (self.rect.x + c.GRID_X_SIZE * 4 >= zombie.rect.x)
            and (zombie.rect.left <= c.SCREEN_WIDTH + 10)
        ):
            return True
        return False

    def setAttack(self):
        self.state = c.ATTACK
        if self.shoot_timer != 0:
            self.shoot_timer = self.current_time - 700


class PotatoMine(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.POTATOMINE, c.PLANT_HEALTH, None)
        self.animate_interval = 300
        self.is_init = True
        self.init_timer = 0
        self.bomb_timer = 0
        self.explode_x_range = c.GRID_X_SIZE / 2
        self.start_boom = False
        self.boomed = False

    def loadImages(self, name, scale):
        self.init_frames = []
        self.idle_frames = []
        self.explode_frames = []

        init_name = name + 'Init'
        idle_name = name
        explode_name = name + 'Explode'

        frame_list = [self.init_frames, self.idle_frames, self.explode_frames]
        name_list = [init_name, idle_name, explode_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.init_frames

    def idling(self):
        if self.is_init:
            if self.init_timer == 0:
                self.init_timer = self.current_time
            elif (self.current_time - self.init_timer) > 15000:
                self.changeFrames(self.idle_frames)
                self.is_init = False

    def canAttack(self, zombie):    # 土豆雷不可能遇上潜水僵尸
        if zombie.name == c.POLE_VAULTING_ZOMBIE and (not zombie.jumped):
            return False
        # 这里碰撞应当比碰撞一般更容易，就设置成圆形或矩形模式，不宜采用mask
        elif (
            pg.sprite.collide_circle_ratio(0.7)(zombie, self)
            and (not self.is_init)
            and (not zombie.losthead)
        ):
            return True
        return False

    def attacking(self):
        if self.bomb_timer == 0:
            self.bomb_timer = self.current_time
            # 播放音效
            c.SOUND_POTATOMINE.play()
            self.changeFrames(self.explode_frames)
            self.start_boom = True
        elif (self.current_time - self.bomb_timer) > 500:
            self.health = 0


class PortraitPotatoMine(PotatoMine):
    """Distinct buried art, 15-second arming, emergence and one-shot blast."""

    ARM_MS = 15000
    RISE_MS = 900
    TRIGGER_MS = 350

    def __init__(self, x, y, effect_group):
        Plant.__init__(self, x, y, c.PORTRAITPOTATOMINE, c.PLANT_HEALTH, effect_group)
        self.is_init = True
        self.born = None
        self.triggered_at = None
        self.trigger_zombie = None
        self.blast_mask = None
        self.blast_rect = None
        self.start_boom = False
        self.boomed = False
        self.explode_x_range = c.GRID_X_SIZE / 2
        self.phase = 'buried'

    def loadImages(self, name, scale):
        self.frames = tool.GFX[name + 'Init']

    def canAttack(self, zombie):
        return (
            not self.is_init and self.triggered_at is None and not self.start_boom
            and self.health > 0 and self.validTrigger(zombie)
            and (
                pg.sprite.collide_mask(zombie, self) is not None
                or abs(zombie.rect.centerx - self.rect.centerx) <= self.explode_x_range
                # A zombie already chewing the buried mine may change pose
                # just as it arms, momentarily removing the pixel overlap.
                or (getattr(zombie, 'prey', None) is self
                    and zombie.rect.colliderect(self.rect))
            )
        )

    def validTrigger(self, zombie):
        return (
            zombie.alive() and zombie.health > 0 and zombie.state != c.DIE
            and not zombie.is_hypno and not zombie.losthead
            and not (zombie.name == c.POLE_VAULTING_ZOMBIE and not zombie.jumped)
        )

    def setAttack(self, zombie=None):
        if not self.is_init and self.triggered_at is None and self.health > 0:
            self.triggered_at = self.current_time
            self.trigger_zombie = zombie
            self.blast_mask = self.mask.copy()
            self.blast_rect = self.rect.copy()
            self.state = c.ATTACK

    def setDamage(self, damage, zombie):
        if self.health <= 0:
            return
        # Readiness can occur between two bites. Trigger before a lethal bite,
        # and protect the short warning animation from further bite damage.
        if self.triggered_at is not None:
            return
        if self.canAttack(zombie):
            self.setAttack(zombie)
            return
        super().setDamage(damage, zombie)

    def hitsBlast(self, zombie):
        if not zombie.alive() or zombie.health <= 0 or zombie.state == c.DIE:
            return False
        if self.blast_mask is None:
            return False
        if abs(zombie.rect.centerx - self.blast_rect.centerx) <= self.explode_x_range:
            return True
        offset = (zombie.rect.x - self.blast_rect.x, zombie.rect.y - self.blast_rect.y)
        if self.blast_mask.overlap(zombie.mask, offset) is not None:
            return True
        # Keep the initiating enemy in the blast despite a chewing-frame
        # change, but never follow an enemy that has left the local footprint.
        return zombie is self.trigger_zombie and zombie.rect.colliderect(self.blast_rect)

    def update(self, game_info):
        from .portrait_potato import PotatoBurst

        self.current_time = now = game_info[c.CURRENT_TIME]
        if self.health <= 0:
            return
        if self.born is None:
            self.born = now
        age = now - self.born
        self.is_init = age < self.ARM_MS
        if self.triggered_at is not None:
            elapsed = now - self.triggered_at
            if elapsed >= self.TRIGGER_MS:
                if not self.start_boom:
                    self.start_boom = True
                    self.phase = 'exploded'
                    from .plant_layout import root as visual_root
                    self.bullet_group.add(PotatoBurst(*visual_root(self), now))
                    c.SOUND_POTATOMINE.play()
                    self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
                    # Level.checkPlants applies damage before removing us.
                    self.health = 0
                return
            self.phase, suffix = 'trigger', 'Warning'
            index = min(19, elapsed * 20 // self.TRIGGER_MS)
        elif age < self.ARM_MS - self.RISE_MS:
            self.phase, suffix = 'buried', 'Init'
            index = (age // 90) % 20
        elif self.is_init:
            self.phase, suffix = 'rising', 'Rise'
            index = min(19, (age - self.ARM_MS + self.RISE_MS) * 20 // self.RISE_MS)
        else:
            self.phase, suffix = 'armed', ''
            index = ((age - self.ARM_MS) // 75) % 20
        self.frames = tool.GFX[self.name + suffix]
        self.frame_index = index
        self.frame_num = len(self.frames)
        self.image = self.frames[index].copy()
        self.mask = pg.mask.from_surface(self.image)
        if 0 <= now - self.hit_timer < 200:
            self.image.fill((35, 15, 0, 0), special_flags=pg.BLEND_RGBA_ADD)
        if now - self.highlight_time < 100:
            self.image.set_alpha(150)


class Squash(Plant):
    def __init__(self, x, y, map_plant_set):
        Plant.__init__(self, x, y, c.SQUASH, c.PLANT_HEALTH, None)
        self.orig_pos = (x, y)
        self.aim_timer = 0
        self.start_boom = False   # 和灰烬等植物统一变量名，在这里表示倭瓜是否跳起
        self.map_plant_set = map_plant_set

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.aim_frames = []
        self.attack_frames = []

        idle_name = name
        aim_name = name + 'Aim'
        attack_name = name + 'Attack'

        frame_list = [self.idle_frames, self.aim_frames, self.attack_frames]
        name_list = [idle_name, aim_name, attack_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.idle_frames

    def canAttack(self, zombie):
        # 普通状态
        if (
            self.state == c.IDLE
            and self.rect.x <= zombie.rect.right
            and (self.rect.right + c.GRID_X_SIZE >= zombie.rect.x)
        ):
            return True
        # 攻击状态
        elif self.state == c.ATTACK:
            if pg.sprite.collide_rect_ratio(0.5)(
                zombie, self
            ) or pg.sprite.collide_mask(zombie, self):
                return True
        return False

    def setAttack(self, zombie, zombie_group):
        self.attack_zombie = zombie
        self.zombie_group = zombie_group
        self.state = c.ATTACK
        # 攻击状态下生命值无敌
        self.health = c.INF

    def attacking(self):
        if self.start_boom:
            if (self.frame_index + 1) == self.frame_num:
                for zombie in self.zombie_group:
                    if self.canAttack(zombie):
                        zombie.setDamage(
                            1800, damage_type=c.ZOMBIE_RANGE_DAMAGE
                        )
                self.health = 0   # 避免僵尸在原位啃食
                self.map_plant_set.remove(c.SQUASH)
                self.kill()
                # 播放碾压音效
                c.SOUND_SQUASHING.play()
        elif self.aim_timer == 0:
            # 锁定目标时播放音效
            c.SOUND_SQUASH_HMM.play()
            self.aim_timer = self.current_time
            self.changeFrames(self.aim_frames)
        elif (self.current_time - self.aim_timer) > 1000:
            self.changeFrames(self.attack_frames)
            self.rect.centerx = self.attack_zombie.rect.centerx
            self.start_boom = True
            self.animate_interval = 300

    def getPosition(self):
        return self.orig_pos


class PortraitSquash(Plant):
    """Calm -> fed-up face -> crouch -> real arc jump -> one crushing impact."""

    WINDUP_MS = 650
    FLIGHT_MS = 650
    IMPACT_MS = 600
    DAMAGE = 1800
    RANGE = 135

    def __init__(self, x, y, level, row):
        super().__init__(x, y, c.PORTRAITSQUASH, c.PLANT_HEALTH, level.bullet_groups[row])
        self.level, self.row = level, row
        self.orig_pos = (x, y)
        self.attack_check = c.CHECK_ATTACK_NEVER
        self.phase = 'idle'
        self.started = None
        self.target = None
        self.landing_x = None
        self.start_boom = False
        self.impacted = False

    def loadImages(self, name, scale):
        self.frames = tool.GFX[name]

    def getPosition(self):
        # Animated coordinates must never change planting-grid ownership.
        return self.orig_pos

    def targets(self):
        return sorted(
            (z for z in self.level.zombie_groups[self.row]
             if targetable(z) and abs(z.rect.centerx - self.orig_pos[0]) <= self.RANGE),
            key=lambda z: abs(z.rect.centerx - self.orig_pos[0]),
        )

    def land(self, now):
        from .portrait_squash import SquashDust, FlattenedZombie
        if self.impacted:
            return
        self.impacted = True
        for victim in list(self.level.zombie_groups[self.row]):
            if not targetable(victim):
                continue
            # Same-row landing footprint, not the airborne image's mask.
            if abs(victim.rect.centerx - self.landing_x) <= 65:
                victim.setDamage(self.DAMAGE, damage_type=c.ZOMBIE_RANGE_DAMAGE)
                if victim.health <= 0:
                    self.bullet_group.add(FlattenedZombie(victim, now))
                    victim.kill()
        from .plant_layout import ROOT_OFFSET
        self.bullet_group.add(SquashDust((round(self.landing_x), self.orig_pos[1] + ROOT_OFFSET), now))
        c.SOUND_SQUASHING.play()

    def update(self, game_info):
        self.current_time = now = game_info[c.CURRENT_TIME]
        if self.health <= 0:
            return
        if self.started is None:
            targets = self.targets()
            if targets:
                self.target = targets[0]
                self.started = now
                self.state = c.ATTACK
                self.start_boom = True
                self.health = c.INF
                c.SOUND_SQUASH_HMM.play()
            else:
                self.image = self.frames[(now // 90) % len(self.frames)].copy()
                self.mask = pg.mask.from_surface(self.image)
                if now - self.highlight_time < 100:
                    self.image.set_alpha(150)
                return
        age = now - self.started
        angry = tool.GFX[self.name + 'Angry']
        centerx, bottom = self.orig_pos
        sx, sy = 1.0, 1.0
        if age < self.WINDUP_MS:
            if not targetable(self.target):
                alternatives = self.targets()
                if alternatives:
                    self.target = alternatives[0]
            self.phase = 'angry' if age < 350 else 'crouch'
            if age < 350:
                centerx += round(math.sin(age / 25) * 2)
            else:
                t = (age - 350) / 300
                sx, sy = 1 + .14 * t, 1 - .23 * t
        else:
            if self.landing_x is None:
                self.landing_x = max(25, min(c.SCREEN_WIDTH - 25, self.target.rect.centerx))
            flight = age - self.WINDUP_MS
            centerx = self.landing_x
            if flight < self.FLIGHT_MS:
                self.phase = 'jump'
                t = flight / self.FLIGHT_MS
                centerx = self.orig_pos[0] + (self.landing_x - self.orig_pos[0]) * t
                bottom -= round(4 * 160 * t * (1 - t))
                sx, sy = .94, 1.04
            else:
                self.phase = 'impact'
                self.land(now)
                impact_age = flight - self.FLIGHT_MS
                if impact_age >= self.IMPACT_MS:
                    self.health = 0
                    return
                t = impact_age / self.IMPACT_MS
                sx, sy = 1.18 - .08 * t, .56 + .34 * min(1, t * 3)
        self.image = pg.transform.smoothscale(
            angry, (round(angry.get_width() * sx), round(angry.get_height() * sy)))
        self.rect = self.image.get_rect(midbottom=(round(centerx), round(bottom)))
        self.mask = pg.mask.from_surface(self.image)
        if self.phase == 'impact':
            self.image.set_alpha(round(255 * max(0, 1 - (age - self.WINDUP_MS - self.FLIGHT_MS) / self.IMPACT_MS)))


class Spikeweed(Plant):
    def __init__(self, x, y):
        Plant.__init__(
            self, x, y, c.SPIKEWEED, c.PLANT_HEALTH, None, scale=0.9
        )
        self.animate_interval = 70
        self.attack_timer = 0

    def setIdle(self):
        self.animate_interval = 70
        self.state = c.IDLE

    def canAttack(self, zombie):
        # 地刺能不能扎的判据：
        # 僵尸中心与地刺中心的距离或僵尸包括了地刺中心和右端（平衡得到合理的攻击范围,"僵尸包括了地刺中心和右端"是为以后巨人做准备）
        # 暂时不能用碰撞判断，平衡性不好
        if (-40 <= zombie.rect.centerx - self.rect.centerx <= 40) or (
            zombie.rect.left <= self.rect.x <= zombie.rect.right
            and zombie.rect.left <= self.rect.right <= zombie.rect.right
        ):
            return True
        return False

    def setAttack(self, zombie_group):
        self.zombie_group = zombie_group
        self.animate_interval = 35
        self.state = c.ATTACK
        if self.hit_timer != 0:
            self.hit_timer = self.current_time - 500

    def attacking(self):
        if self.hit_timer == 0:
            self.hit_timer = self.current_time - 500
        elif (self.current_time - self.attack_timer) >= 700:
            self.attack_timer = self.current_time
            # 最后再来判断攻击是否要杀死自己
            killSelf = False
            for zombie in self.zombie_group:
                if self.canAttack(zombie):
                    # 有车的僵尸
                    if zombie.name in {c.ZOMBONI}:
                        zombie.health = zombie.losthead_health
                        killSelf = True
                    else:
                        zombie.setDamage(
                            20, damage_type=c.ZOMBIE_COMMON_DAMAGE
                        )
            if killSelf:
                self.health = 0
            # 播放攻击音效，同子弹打击
            c.SOUND_BULLET_EXPLODE.play()


class Jalapeno(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.JALAPENO, c.INF, None)
        self.orig_pos = (x, y)
        self.state = c.ATTACK
        self.start_boom = False
        self.boomed = False
        self.explode_y_range = 0
        self.explode_x_range = 500

    def loadImages(self, name, scale):
        self.explode_frames = []
        explode_name = name + 'Explode'
        self.loadFrames(self.explode_frames, explode_name)

        self.loadFrames(self.frames, name)

    def setExplode(self):
        self.changeFrames(self.explode_frames)
        self.animate_timer = self.current_time
        self.rect.x = c.MAP_OFFSET_X
        self.start_boom = True

    def animation(self):
        if self.start_boom:
            if (self.current_time - self.animate_timer) > 100:
                if self.frame_index == 1:
                    # 播放爆炸音效
                    c.SOUND_BOMB.play()
                self.frame_index += 1
                if self.frame_index >= self.frame_num:
                    self.health = 0
                    return
                self.animate_timer = self.current_time
        else:
            if (self.current_time - self.animate_timer) > 100:
                self.frame_index += 1
                if self.frame_index >= self.frame_num:
                    self.setExplode()
                    return
                self.animate_timer = self.current_time
        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)

        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif (self.current_time - self.hit_timer) < 200:
            self.image.set_alpha(192)
        else:
            self.image.set_alpha(255)

    def getPosition(self):
        return self.orig_pos


class ScaredyShroom(Plant):
    def __init__(self, x, y, bullet_group):
        Plant.__init__(
            self, x, y, c.SCAREDYSHROOM, c.PLANT_HEALTH, bullet_group
        )
        self.shoot_timer = 0
        self.cry_x_range = c.GRID_X_SIZE * 1.5

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.cry_frames = []
        self.sleep_frames = []

        idle_name = name
        cry_name = name + 'Cry'
        sleep_name = name + 'Sleep'

        frame_list = [self.idle_frames, self.cry_frames, self.sleep_frames]
        name_list = [idle_name, cry_name, sleep_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.idle_frames

    def needCry(self, zombie):
        if (
            zombie.state != c.DIE
            and abs(self.rect.x - zombie.rect.x) < self.cry_x_range
        ):
            return True
        return False

    def setCry(self):
        self.state = c.CRY
        self.changeFrames(self.cry_frames)

    def setAttack(self):
        self.state = c.ATTACK
        self.changeFrames(self.idle_frames)
        if self.shoot_timer != 0:
            self.shoot_timer = self.current_time - 700

    def setIdle(self):
        self.state = c.IDLE
        self.changeFrames(self.idle_frames)

    def attacking(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.current_time - 700
        elif (self.current_time - self.shoot_timer) >= 1400:
            self.bullet_group.add(
                Bullet(
                    self.rect.right - 15,
                    self.rect.y + 40,
                    self.rect.y + 40,
                    c.BULLET_MUSHROOM,
                    c.BULLET_DAMAGE_NORMAL,
                    effect=None,
                )
            )
            self.shoot_timer = self.current_time
            # 播放音效
            c.SOUND_PUFF.play()


class SunShroom(Plant):
    def __init__(self, x, y, sun_group):
        Plant.__init__(self, x, y, c.SUNSHROOM, c.PLANT_HEALTH, None)
        self.animate_interval = 140
        self.sun_timer = 0
        self.sun_group = sun_group
        self.is_big = False
        self.change_timer = 0

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.big_frames = []
        self.sleep_frames = []

        idle_name = name
        big_name = name + 'Big'
        sleep_name = name + 'Sleep'

        frame_list = [self.idle_frames, self.big_frames, self.sleep_frames]
        name_list = [idle_name, big_name, sleep_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.idle_frames

    def idling(self):
        if not self.is_big:
            if self.change_timer == 0:
                self.change_timer = self.current_time
            elif (self.current_time - self.change_timer) > 100000:
                self.changeFrames(self.big_frames)
                self.is_big = True
                # 播放长大音效
                c.SOUND_PLANT_GROW.play()
        if self.sun_timer == 0:
            self.sun_timer = self.current_time - (c.FLOWER_SUN_INTERVAL - 6000)
        elif (self.current_time - self.sun_timer) > c.FLOWER_SUN_INTERVAL:
            self.sun_group.add(
                Sun(
                    self.rect.centerx,
                    self.rect.bottom,
                    self.rect.right,
                    self.rect.bottom + self.rect.h // 2,
                    self.is_big,
                )
            )
            self.sun_timer = self.current_time


class IceShroom(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.ICESHROOM, c.PLANT_HEALTH, None)
        self.orig_pos = (x, y)
        self.start_boom = False
        self.boomed = False

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.snow_frames = []
        self.sleep_frames = []
        self.trap_frames = []

        idle_name = name
        snow_name = name + 'Snow'
        sleep_name = name + 'Sleep'
        trap_name = name + 'Trap'

        frame_list = [
            self.idle_frames,
            self.snow_frames,
            self.sleep_frames,
            self.trap_frames,
        ]
        name_list = [idle_name, snow_name, sleep_name, trap_name]
        scale_list = [1, 1.5, 1, 1]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, scale_list[i])

        self.frames = self.idle_frames

    def setFreeze(self):
        self.changeFrames(self.snow_frames)
        self.animate_timer = self.current_time
        self.rect.x = c.MAP_OFFSET_X
        self.rect.y = c.MAP_OFFSET_Y
        self.start_boom = True

    def animation(self):
        if self.start_boom:
            if (self.current_time - self.animate_timer) > 500:
                self.frame_index += 1
                if self.frame_index >= self.frame_num:
                    self.health = 0
                    return
                self.animate_timer = self.current_time
        else:
            if self.state != c.SLEEP:
                self.health = c.INF
            if (self.current_time - self.animate_timer) > 100:
                self.frame_index += 1
                if self.frame_index >= self.frame_num:
                    if self.state == c.SLEEP:
                        self.frame_index = 0
                    else:
                        self.setFreeze()
                        return
                self.animate_timer = self.current_time
        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)

        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif (self.current_time - self.hit_timer) < 200:
            self.image.set_alpha(192)
        else:
            self.image.set_alpha(255)

    def getPosition(self):
        return self.orig_pos


class HypnoShroom(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.HYPNOSHROOM, c.PLANT_HEALTH, None)
        self.animate_interval = 80
        self.zombie_to_hypno = None
        self.attack_check = c.CHECK_ATTACK_NEVER

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.sleep_frames = []

        idle_name = name
        sleep_name = name + 'Sleep'

        frame_list = [self.idle_frames, self.sleep_frames]
        name_list = [idle_name, sleep_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.idle_frames

    def idling(self):
        if self.health < c.PLANT_HEALTH and self.zombie_to_hypno:
            self.health = 0


class WallNutBowling(Plant):
    def __init__(self, x, y, map_y, level):
        Plant.__init__(self, x, y, c.WALLNUTBOWLING, 1, None)
        self.map_y = map_y
        self.level = level
        self.init_rect = self.rect.copy()
        self.rotate_degree = 0
        self.animate_interval = 200
        self.move_timer = 0
        self.move_interval = 70
        self.vel_x = random.randint(12, 15)
        self.vel_y = 0
        self.disable_hit_y = -1
        self.attack_check = c.CHECK_ATTACK_NEVER

    def loadImages(self, name, scale):
        self.loadFrames(self.frames, name, 1)

    def idling(self):
        if self.move_timer == 0:
            self.move_timer = self.current_time
        elif (self.current_time - self.move_timer) >= self.move_interval:
            self.rotate_degree = (self.rotate_degree - 30) % 360
            self.init_rect.x += self.vel_x
            self.init_rect.y += self.vel_y
            self.handleMapYPosition()
            if self.shouldChangeDirection():
                self.changeDirection(-1)
            if self.init_rect.x > c.SCREEN_WIDTH + 25:
                self.health = 0
            self.move_timer += self.move_interval

    def canHit(self, map_y):
        if self.disable_hit_y == map_y:
            return False
        return True

    def handleMapYPosition(self):
        map_y1 = self.level.map.getMapIndex(
            self.init_rect.x, self.init_rect.centery
        )[1]
        map_y2 = self.level.map.getMapIndex(
            self.init_rect.x, self.init_rect.bottom
        )[1]
        if self.map_y != map_y1 and map_y1 == map_y2:
            # wallnut bowls to another row, should modify which plant group it belongs to
            self.level.plant_groups[self.map_y].remove(self)
            self.level.plant_groups[map_y1].add(self)
            self.map_y = map_y1

    def shouldChangeDirection(self):
        if self.init_rect.centery <= c.MAP_OFFSET_Y:
            return True
        elif self.init_rect.bottom + 20 >= c.SCREEN_HEIGHT:
            return True
        return False

    def changeDirection(self, map_y):
        if self.vel_y == 0:
            if self.map_y == 0:
                self.vel_y = self.vel_x
            elif self.map_y == (c.GRID_Y_LEN - 1):  # 坚果保龄球显然没有泳池的6行情形
                self.vel_y = -self.vel_x
            else:
                if random.randint(0, 1):
                    self.vel_y = self.vel_x
                else:
                    self.vel_y = -self.vel_x
        else:
            self.vel_y = -self.vel_y

        self.disable_hit_y = map_y

    def animation(self):
        image = self.frames[self.frame_index]
        self.image = pg.transform.rotate(image, self.rotate_degree)
        self.mask = pg.mask.from_surface(self.image)
        # must keep the center postion of image when rotate
        self.rect = self.image.get_rect(center=self.init_rect.center)


class RedWallNutBowling(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.REDWALLNUTBOWLING, 1, None)
        self.orig_y = y
        self.explode_timer = 0
        self.explode_y_range = 1
        self.explode_x_range = c.GRID_X_SIZE * 1.5
        self.init_rect = self.rect.copy()
        self.rotate_degree = 0
        self.animate_interval = 200
        self.move_timer = 0
        self.move_interval = 70
        self.vel_x = random.randint(12, 15)
        self.start_boom = False
        self.boomed = False

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.loadFrames(self.idle_frames, name, 1)

        frame = tool.GFX[c.BOOM_IMAGE]
        rect = frame.get_rect()
        image = tool.get_image(frame, 0, 0, rect.w, rect.h)
        self.explode_frames = (image,)

        self.frames = self.idle_frames

    def idling(self):
        if self.move_timer == 0:
            self.move_timer = self.current_time
        elif (self.current_time - self.move_timer) >= self.move_interval:
            self.rotate_degree = (self.rotate_degree - 30) % 360
            self.init_rect.x += self.vel_x
            if self.init_rect.x > c.SCREEN_WIDTH + 25:
                self.health = 0
            self.move_timer += self.move_interval

    def attacking(self):
        if self.explode_timer == 0:
            self.start_boom = True
            self.explode_timer = self.current_time
            self.changeFrames(self.explode_frames)
            # 播放爆炸音效
            c.SOUND_BOMB.play()
        elif (self.current_time - self.explode_timer) > 500:
            self.health = 0

    def animation(self):
        if (self.current_time - self.animate_timer) > self.animate_interval:
            self.frame_index += 1
            if self.frame_index >= self.frame_num:
                self.frame_index = 0
            self.animate_timer = self.current_time

        image = self.frames[self.frame_index]
        if self.state == c.IDLE:
            self.image = pg.transform.rotate(image, self.rotate_degree)
        else:
            self.image = image
        self.mask = pg.mask.from_surface(self.image)
        # must keep the center postion of image when rotate
        self.rect = self.image.get_rect(center=self.init_rect.center)

    def getPosition(self):
        return (self.rect.centerx, self.orig_y)


class LilyPad(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.LILYPAD, c.PLANT_HEALTH, None)
        self.attack_check = c.CHECK_ATTACK_NEVER


class TorchWood(Plant):
    def __init__(self, x, y, bullet_group):
        Plant.__init__(self, x, y, c.TORCHWOOD, c.PLANT_HEALTH, bullet_group)
        self.attack_check = c.CHECK_ATTACK_NEVER

    def idling(self):
        for i in self.bullet_group:
            if (
                i.name == c.BULLET_PEA
                and i.passed_torchwood_x != self.rect.centerx
                and abs(i.rect.centerx - self.rect.centerx) <= 20
            ):
                self.bullet_group.add(
                    Bullet(
                        i.rect.x,
                        i.rect.y,
                        i.dest_y,
                        c.BULLET_FIREBALL,
                        c.BULLET_DAMAGE_FIREBALL_BODY,
                        effect=c.BULLET_EFFECT_UNICE,
                        passed_torchwood_x=self.rect.centerx,
                    )
                )
                i.kill()
            elif (
                i.name == c.BULLET_PEA_ICE
                and i.passed_torchwood_x != self.rect.centerx
                and abs(i.rect.centerx - self.rect.centerx)
            ):
                self.bullet_group.add(
                    Bullet(
                        i.rect.x,
                        i.rect.y,
                        i.dest_y,
                        c.BULLET_PEA,
                        c.BULLET_DAMAGE_NORMAL,
                        effect=None,
                        passed_torchwood_x=self.rect.centerx,
                    )
                )
                i.kill()


class StarFruit(Plant):
    def __init__(self, x, y, bullet_group, level):
        Plant.__init__(self, x, y, c.STARFRUIT, c.PLANT_HEALTH, bullet_group)
        self.shoot_timer = 0
        self.level = level
        self.map_x, self.map_y = self.level.map.getMapIndex(x, y)

    def canAttack(self, zombie):
        if (zombie.name == c.SNORKELZOMBIE) and (
            zombie.frames == zombie.swim_frames
        ):
            return False
        if zombie.state != c.DIE:
            zombie_map_y = self.level.map.getMapIndex(
                zombie.rect.centerx, zombie.rect.bottom
            )[1]
            if (self.rect.x >= zombie.rect.x) and (
                self.map_y == zombie_map_y
            ):  # 对于同行且在杨桃后的僵尸
                return True
            # 斜向上，理想直线方程为：
            # f(zombie.rect.x) = -0.75*(zombie.rect.x - (self.rect.right - 5)) + self.rect.y - 10
            # 注意实际上为射线
            elif (
                -100
                <= (
                    zombie.rect.y
                    - (
                        -0.75 * (zombie.rect.x - (self.rect.right - 5))
                        + self.rect.y
                        - 10
                    )
                )
                <= 70
                and (zombie.rect.left <= c.SCREEN_WIDTH)
                and (zombie.rect.x >= self.rect.x)
            ):
                return True
            # 斜向下，理想直线方程为：f(zombie.rect.x) = zombie.rect.x + self.rect.y - self.rect.right - 15
            # 注意实际上为射线
            elif (
                abs(
                    zombie.rect.y
                    - (zombie.rect.x + self.rect.y - self.rect.right - 15)
                )
                <= 70
                and (zombie.rect.left <= c.SCREEN_WIDTH)
                and (zombie.rect.x >= self.rect.x)
            ):
                return True
            elif zombie.rect.left <= self.rect.x <= zombie.rect.right:
                return True
        return False

    def attacking(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.current_time - 700
        elif (self.current_time - self.shoot_timer) >= 1400:
            # pypvz特有设定：向后打的杨桃子弹无视铁门与报纸防具
            self.bullet_group.add(
                StarBullet(
                    self.rect.left - 10,
                    self.rect.y + 15,
                    c.BULLET_DAMAGE_NORMAL,
                    c.STAR_BACKWARD,
                    self.level,
                    damage_type=c.ZOMBIE_COMMON_DAMAGE,
                )
            )
            # 其他方向的杨桃子弹伤害效果与豌豆等同
            self.bullet_group.add(
                StarBullet(
                    self.rect.centerx - 20,
                    self.rect.bottom - self.rect.h - 15,
                    c.BULLET_DAMAGE_NORMAL,
                    c.STAR_UPWARD,
                    self.level,
                )
            )
            self.bullet_group.add(
                StarBullet(
                    self.rect.centerx - 20,
                    self.rect.bottom - 5,
                    c.BULLET_DAMAGE_NORMAL,
                    c.STAR_DOWNWARD,
                    self.level,
                )
            )
            self.bullet_group.add(
                StarBullet(
                    self.rect.right - 5,
                    self.rect.bottom - 20,
                    c.BULLET_DAMAGE_NORMAL,
                    c.STAR_FORWARD_DOWN,
                    self.level,
                )
            )
            self.bullet_group.add(
                StarBullet(
                    self.rect.right - 5,
                    self.rect.y - 10,
                    c.BULLET_DAMAGE_NORMAL,
                    c.STAR_FORWARD_UP,
                    self.level,
                )
            )
            self.shoot_timer = self.current_time
            # 播放发射音效
            c.SOUND_SHOOT.play()

    def setAttack(self):
        self.state = c.ATTACK
        if self.shoot_timer != 0:
            self.shoot_timer = self.current_time - 700


class CoffeeBean(Plant):
    def __init__(self, x, y, plant_group, map_content, map, map_x):
        Plant.__init__(self, x, y, c.COFFEEBEAN, c.PLANT_HEALTH, None)
        self.plant_group = plant_group
        self.map_content = map_content
        self.map = map
        self.map_x = map_x
        self.attack_check = c.CHECK_ATTACK_NEVER

    def animation(self):
        if (self.current_time - self.animate_timer) > self.animate_interval:
            self.frame_index += 1

            if self.frame_index >= self.frame_num:
                self.map_content[c.MAP_SLEEP] = False
                for plant in self.plant_group:
                    if plant.name in c.CAN_SLEEP_PLANTS:
                        if plant.state == c.SLEEP:
                            plant_map_x, _ = self.map.getMapIndex(
                                plant.rect.centerx, plant.rect.bottom
                            )
                            if plant_map_x == self.map_x:
                                plant.state = c.IDLE
                                plant.setIdle()
                                plant.changeFrames(plant.idle_frames)
                # 播放唤醒音效
                c.SOUND_MUSHROOM_WAKEUP.play()
                self.map_content[c.MAP_PLANT].remove(self.name)
                self.kill()
                self.frame_index = self.frame_num - 1

            self.animate_timer = self.current_time

        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)
        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif (self.current_time - self.hit_timer) < 200:
            self.image.set_alpha(192)
        else:
            self.image.set_alpha(255)


class SeaShroom(Plant):
    def __init__(self, x, y, bullet_group):
        Plant.__init__(self, x, y, c.SEASHROOM, c.PLANT_HEALTH, bullet_group)
        self.shoot_timer = 0

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.sleep_frames = []

        idle_name = name
        sleep_name = name + 'Sleep'

        frame_list = [self.idle_frames, self.sleep_frames]
        name_list = [idle_name, sleep_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.idle_frames

    def attacking(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.current_time - 700
        elif (self.current_time - self.shoot_timer) >= 1400:
            self.bullet_group.add(
                Bullet(
                    self.rect.right,
                    self.rect.y + 50,
                    self.rect.y + 50,
                    c.BULLET_SEASHROOM,
                    c.BULLET_DAMAGE_NORMAL,
                    effect=None,
                )
            )
            self.shoot_timer = self.current_time
            # 播放发射音效
            c.SOUND_PUFF.play()

    def canAttack(self, zombie):
        if (zombie.name == c.SNORKELZOMBIE) and (
            zombie.frames == zombie.swim_frames
        ):
            return False
        if (
            self.rect.x <= zombie.rect.right
            and (self.rect.x + c.GRID_X_SIZE * 4 >= zombie.rect.x)
            and (zombie.rect.left <= c.SCREEN_WIDTH + 10)
        ):
            return True
        return False

    def setAttack(self):
        self.state = c.ATTACK
        if self.shoot_timer != 0:
            self.shoot_timer = self.current_time - 700


class TallNut(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.TALLNUT, c.TALLNUT_HEALTH, None)
        self.load_images()
        self.cracked1 = False
        self.cracked2 = False
        self.attack_check = c.CHECK_ATTACK_NEVER

    def load_images(self):
        self.cracked1_frames = []
        self.cracked2_frames = []

        cracked1_frames_name = self.name + '_cracked1'
        cracked2_frames_name = self.name + '_cracked2'

        self.loadFrames(self.cracked1_frames, cracked1_frames_name)
        self.loadFrames(self.cracked2_frames, cracked2_frames_name)

    def idling(self):
        if not self.cracked1 and self.health <= c.TALLNUT_CRACKED1_HEALTH:
            self.changeFrames(self.cracked1_frames)
            self.cracked1 = True
        elif not self.cracked2 and self.health <= c.TALLNUT_CRACKED2_HEALTH:
            self.changeFrames(self.cracked2_frames)
            self.cracked2 = True


class PortraitTallNut(Plant):
    """Portrait barrier with breathing, impact recoil and proportional cracks."""

    def __init__(self, x, y):
        super().__init__(x, y, c.PORTRAITTALLNUT, c.PORTRAITTALLNUT_HEALTH, None)
        self.attack_check = c.CHECK_ATTACK_NEVER
        self.damage_frames = [self.frames,
                              tool.GFX[c.PORTRAITTALLNUT + '_cracked1'],
                              tool.GFX[c.PORTRAITTALLNUT + '_cracked2']]
        self.damage_stage = 0
        self.last_impact = None

    def update(self, game_info):
        self.current_time = game_info[c.CURRENT_TIME]
        if self.health <= c.PORTRAITTALLNUT_HEALTH // 3:
            self.damage_stage = 2
        elif self.health <= c.PORTRAITTALLNUT_HEALTH * 2 // 3:
            self.damage_stage = 1
        else:
            self.damage_stage = 0
        self.frames = self.damage_frames[self.damage_stage]
        self.frame_index = int(self.current_time / 90) % len(self.frames)
        self.frame_num = len(self.frames)
        image = self.frames[self.frame_index].copy()
        age = 1000 if self.last_impact is None else self.current_time - self.last_impact
        if 0 <= age < 350:
            shifted = pg.Surface(image.get_size(), pg.SRCALPHA)
            offset = round(math.sin(age / 18) * 4 * (1 - age / 350))
            shifted.blit(image, (offset, 0))
            # Brief shell chips scatter to the right after the bite.
            for index in range(4):
                x = 79 + round(age / 350 * (10 + index * 3))
                y = 85 + index * 10 + round(math.sin(age / 110) * 8)
                pg.draw.polygon(shifted, (234, 176, 83, round(255 * (1 - age / 350))),
                                [(x, y), (x + 4, y - 2), (x + 3, y + 4)])
            image = shifted
        bar = getattr(self, 'healing_bar', None)
        healing = bar is not None and bar.alive() and self.current_time - bar.born < bar.DURATION
        if self.health < self.max_health or healing:
            from .health_bar import draw_health_bar
            health = bar.displayed_health(self.current_time) if healing else self.health
            alpha = 255
            if healing and self.health >= self.max_health:
                alpha = round(255 * min(1, (bar.DURATION - self.current_time + bar.born) / 350))
            draw_health_bar(image, health, self.max_health, (23, 3), alpha)
        if self.current_time - self.highlight_time < 100:
            image.set_alpha(150)
        self.image = image
        self.mask = pg.mask.from_surface(self.frames[self.frame_index])

    def setDamage(self, damage, zombie):
        old_health = self.health
        super().setDamage(damage, zombie)
        if self.health < old_health:
            self.last_impact = self.current_time


class TangleKlep(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.TANGLEKLEP, c.PLANT_HEALTH, None)
        self.load_images()
        self.splashing = False

    def load_images(self):
        self.idle_frames = []
        self.splash_frames = []

        idle_name = self.name
        splash_name = self.name + 'Splash'

        frame_list = [self.idle_frames, self.splash_frames]
        name_list = [idle_name, splash_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.idle_frames

    def canAttack(self, zombie):
        if zombie.state != c.DIE and (not zombie.losthead):
            # 这里碰撞应当比碰撞一般更容易，就设置成圆形或矩形模式，不宜采用mask
            if pg.sprite.collide_rect_ratio(1)(zombie, self):
                return True
        return False

    def setAttack(self, zombie, zombie_group):
        self.attack_zombie = zombie
        self.zombie_group = zombie_group
        self.state = c.ATTACK

    def attacking(self):
        if not self.splashing:
            self.splashing = True
            self.changeFrames(self.splash_frames)
            self.attack_zombie.kill()
            # 播放拖拽音效
            c.SOUND_TANGLE_KELP_DRAG.play()
        # 这里必须用elif排除尚未进入splash阶段，以免误触
        elif (self.frame_index + 1) >= self.frame_num:
            self.health = 0


# 毁灭菇的处理办法：
# 爆炸后留下的坑看作另一种形态的毁灭菇
# 当存在这种形态的毁灭菇时不可以种植物
# 坑形态的毁灭菇存在时不可种植物
# 坑形态的毁灭菇同地刺一样不可以被啃食
# 爆炸时杀死同一格的所有植物
class DoomShroom(Plant):
    def __init__(self, x, y, map_plant_set, explode_y_range):
        Plant.__init__(self, x, y, c.DOOMSHROOM, c.PLANT_HEALTH, None)
        self.map_plant_set = map_plant_set
        self.bomb_timer = 0
        self.explode_y_range = explode_y_range
        self.explode_x_range = 250
        self.start_boom = False
        self.boomed = False
        self.original_x = x
        self.original_y = y

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.sleep_frames = []
        self.boom_frames = []

        idle_name = name
        sleep_name = name + 'Sleep'
        boom_name = name + 'Boom'

        frame_list = [self.idle_frames, self.sleep_frames, self.boom_frames]
        name_list = [idle_name, sleep_name, boom_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.idle_frames

    def setBoom(self):
        self.changeFrames(self.boom_frames)
        self.start_boom = True

    def animation(self):
        # 发生了爆炸
        if self.start_boom:
            if self.frame_index == 1:
                self.rect.x -= 80
                self.rect.y += 30
                # 播放爆炸音效
                c.SOUND_DOOMSHROOM.play()
            if (
                self.current_time - self.animate_timer
            ) > self.animate_interval:
                self.frame_index += 1
            if self.frame_index >= self.frame_num:
                self.health = 0
                self.frame_index = self.frame_num - 1
                self.map_plant_set.add(c.HOLE)
        # 睡觉状态
        elif self.state == c.SLEEP:
            if (
                self.current_time - self.animate_timer
            ) > self.animate_interval:
                self.frame_index += 1
                if self.frame_index >= self.frame_num:
                    self.frame_index = 0
                self.animate_timer = self.current_time
        # 正常状态
        else:
            self.health = c.INF
            if (self.current_time - self.animate_timer) > 100:
                self.frame_index += 1
                if self.frame_index >= self.frame_num:
                    self.setBoom()
                    return
                self.animate_timer = self.current_time
        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)

        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif (self.current_time - self.hit_timer) < 200:
            self.image.set_alpha(192)
        else:
            self.image.set_alpha(255)


# 用于描述毁灭菇的坑
class Hole(Plant):
    def __init__(self, x, y, plot_type):
        # 指定区域类型这一句必须放在前面，否则加载图片判断将会失败
        self.plot_type = plot_type
        Plant.__init__(self, x, y, c.HOLE, c.INF, None)
        self.timer = 0
        self.shallow = False
        self.attack_check = c.CHECK_ATTACK_NEVER

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.idle2_frames = []
        self.water_frames = []
        self.water2_frames = []
        self.roof_frames = []
        self.roof2_frames = []

        idle_name = name
        idle2_name = name + 'Shallow'
        water_name = name + 'Water'
        water2_name = name + 'WaterShallow'
        roof_name = name + 'Roof'
        roof2_name = name + 'RoofShallow'

        frame_list = [
            self.idle_frames,
            self.idle2_frames,
            self.water_frames,
            self.water2_frames,
            self.roof_frames,
            self.roof2_frames,
        ]
        name_list = [
            idle_name,
            idle2_name,
            water_name,
            water2_name,
            roof_name,
            roof2_name,
        ]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        if self.plot_type == c.MAP_TILE:
            self.frames = self.roof_frames
        elif self.plot_type == c.MAP_WATER:
            self.frames = self.water_frames
        else:
            self.frames = self.idle_frames

    def idling(self):
        if self.timer == 0:
            self.timer = self.current_time
        elif (not self.shallow) and (self.current_time - self.timer >= 90000):
            if self.plot_type == c.MAP_TILE:
                self.frames = self.roof2_frames
            elif self.plot_type == c.MAP_WATER:
                self.frames = self.water2_frames
            else:
                self.frames = self.idle2_frames
            self.shallow = True
        elif self.current_time - self.timer >= 180000:
            self.health = 0


class Grave(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.GRAVE, c.INF, None)
        self.frame_index = random.randint(0, self.frame_num - 1)
        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)
        self.attack_check = c.CHECK_ATTACK_NEVER

    def animation(self):
        pass


class GraveBuster(Plant):
    def __init__(self, x, y, plant_group, map, map_x):
        Plant.__init__(self, x, y, c.GRAVEBUSTER, c.PLANT_HEALTH, None)
        self.map = map
        self.map_x = map_x
        self.plant_group = plant_group
        self.animate_interval = 100
        self.attack_check = c.CHECK_ATTACK_NEVER
        # 播放吞噬音效
        c.SOUND_GRAVEBUSTER_CHOMP.play()

    def animation(self):
        if (self.current_time - self.animate_timer) > self.animate_interval:
            self.frame_index += 1
            if self.frame_index >= self.frame_num:
                self.frame_index = self.frame_num - 1
                for item in self.plant_group:
                    if item.name == c.GRAVE:
                        item_map_x, _ = self.map.getMapIndex(
                            item.rect.centerx, item.rect.bottom
                        )
                        if item_map_x == self.map_x:
                            item.health = 0
                            self.health = 0
            self.animate_timer = self.current_time

        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)

        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif (self.current_time - self.hit_timer) < 200:
            self.image.set_alpha(192)
        else:
            self.image.set_alpha(255)


class FumeShroom(Plant):
    def __init__(self, x, y, bullet_group, zombie_group):
        Plant.__init__(self, x, y, c.FUMESHROOM, c.PLANT_HEALTH, bullet_group)
        self.shoot_timer = 0
        self.show_attack_frames = True
        self.zombie_group = zombie_group

    def loadImages(self, name, scale):
        self.idle_frames = []
        self.sleep_frames = []
        self.attack_frames = []

        idle_name = name
        sleep_name = name + 'Sleep'
        attack_name = name + 'Attack'

        frame_list = [self.idle_frames, self.sleep_frames, self.attack_frames]
        name_list = [idle_name, sleep_name, attack_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.idle_frames

    def canAttack(self, zombie):
        if (zombie.name == c.SNORKELZOMBIE) and (
            zombie.frames == zombie.swim_frames
        ):
            return False
        if (
            self.rect.x <= zombie.rect.right
            and (self.rect.x + c.GRID_X_SIZE * 5 >= zombie.rect.x)
            and (zombie.rect.left <= c.SCREEN_WIDTH + 10)
        ):
            return True
        return False

    def setAttack(self):
        self.state = c.ATTACK
        if self.shoot_timer != 0:
            self.shoot_timer = self.current_time - 700

    def attacking(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.current_time - 700
        elif self.current_time - self.shoot_timer >= 1100:
            if self.show_attack_frames:
                self.show_attack_frames = False
                self.changeFrames(self.attack_frames)

        if self.current_time - self.shoot_timer >= 1400:
            self.bullet_group.add(Fume(self.rect.right - 35, self.rect.y))
            # 烟雾只是个动画，实际伤害由本身完成
            for target_zombie in self.zombie_group:
                if self.canAttack(target_zombie):
                    target_zombie.setDamage(
                        c.BULLET_DAMAGE_NORMAL,
                        damage_type=c.ZOMBIE_RANGE_DAMAGE,
                    )
            self.shoot_timer = self.current_time
            self.show_attack_frames = True
            # 播放发射音效
            c.SOUND_FUME.play()

    def animation(self):
        if (self.current_time - self.animate_timer) > self.animate_interval:
            self.frame_index += 1
            if self.frame_index >= self.frame_num:
                if self.frames == self.attack_frames:
                    self.changeFrames(self.idle_frames)
                else:
                    self.frame_index = 0
            self.animate_timer = self.current_time

        self.image = self.frames[self.frame_index]
        self.mask = pg.mask.from_surface(self.image)

        if self.current_time - self.highlight_time < 100:
            self.image.set_alpha(150)
        elif (self.current_time - self.hit_timer) < 200:
            self.image.set_alpha(192)
        else:
            self.image.set_alpha(255)


class IceFrozenPlot(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.ICEFROZENPLOT, c.INF, None)
        self.timer = 0
        self.attack_check = c.CHECK_ATTACK_NEVER

    def idling(self):
        if self.timer == 0:
            self.timer = self.current_time
        elif self.current_time - self.timer >= 30000:
            self.health = 0


class Garlic(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.GARLIC, c.GARLIC_HEALTH, None)
        self.load_images()
        self.cracked1 = False
        self.cracked2 = False

    def load_images(self):
        self.cracked1_frames = []
        self.cracked2_frames = []

        cracked1_frames_name = self.name + '_cracked1'
        cracked2_frames_name = self.name + '_cracked2'

        self.loadFrames(self.cracked1_frames, cracked1_frames_name)
        self.loadFrames(self.cracked2_frames, cracked2_frames_name)

    def idling(self):
        if (not self.cracked1) and self.health <= c.GARLIC_CRACKED1_HEALTH:
            self.changeFrames(self.cracked1_frames)
            self.cracked1 = True
        elif (not self.cracked2) and self.health <= c.GARLIC_CRACKED2_HEALTH:
            self.changeFrames(self.cracked2_frames)
            self.cracked2 = True


class PumpkinHead(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.PUMPKINHEAD, c.WALLNUT_HEALTH, None)
        self.load_images()
        self.cracked1 = False
        self.cracked2 = False
        self.animate_interval = 160
        self.attack_check = c.CHECK_ATTACK_NEVER

    def load_images(self):
        self.cracked1_frames = []
        self.cracked2_frames = []

        cracked1_frames_name = self.name + '_cracked1'
        cracked2_frames_name = self.name + '_cracked2'

        self.loadFrames(self.cracked1_frames, cracked1_frames_name)
        self.loadFrames(self.cracked2_frames, cracked2_frames_name)

    def idling(self):
        if not self.cracked1 and self.health <= c.WALLNUT_CRACKED1_HEALTH:
            self.changeFrames(self.cracked1_frames)
            self.cracked1 = True
        elif not self.cracked2 and self.health <= c.WALLNUT_CRACKED2_HEALTH:
            self.changeFrames(self.cracked2_frames)
            self.cracked2 = True


class GiantWallNut(Plant):
    def __init__(self, x, y):
        Plant.__init__(self, x, y, c.GIANTWALLNUT, 1, None)
        self.init_rect = self.rect.copy()
        self.rotate_degree = 0
        self.animate_interval = 200
        self.move_timer = 0
        self.move_interval = 70
        self.vel_x = random.randint(15, 18)
        self.attack_check = c.CHECK_ATTACK_NEVER

    def idling(self):
        if self.move_timer == 0:
            self.move_timer = self.current_time
        elif (self.current_time - self.move_timer) >= self.move_interval:
            self.rotate_degree = (self.rotate_degree - 30) % 360
            self.init_rect.x += self.vel_x
            if self.init_rect.x > c.SCREEN_WIDTH:
                self.health = 0
            self.move_timer += self.move_interval

    def animation(self):
        image = self.frames[self.frame_index]
        self.image = pg.transform.rotate(image, self.rotate_degree)
        self.mask = pg.mask.from_surface(self.image)
        # must keep the center postion of image when rotate
        self.rect = self.image.get_rect(center=self.init_rect.center)
