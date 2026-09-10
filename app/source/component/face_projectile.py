"""Photo-based homing comet and short-lived impact effects."""

import math

import pygame as pg

from .. import constants as c
from .. import tool


COLORS = ((60, 235, 255), (171, 92, 255), (255, 104, 224), (255, 223, 90))


def targetable(zombie):
    if zombie.state == c.DIE or zombie.health <= 0 or not zombie.alive():
        return False
    if not (0 < zombie.rect.centerx < c.SCREEN_WIDTH):
        return False
    return not (
        zombie.name == c.SNORKELZOMBIE
        and zombie.frames == zombie.swim_frames
    )


class FaceImpact(pg.sprite.Sprite):
    """Only visual: never enters ordinary bullet collision handling."""

    def __init__(self, center, now):
        super().__init__()
        self.name = c.FUME
        self.born = now
        self.image = pg.Surface((128, 128), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        self.update({c.CURRENT_TIME: now})

    def update(self, game_info):
        age = game_info[c.CURRENT_TIME] - self.born
        if age >= 360:
            self.kill()
            return
        self.image.fill((0, 0, 0, 0))
        fraction = max(0, age / 360)
        radius = int(8 + fraction * 48)
        alpha = int(230 * (1 - fraction))
        for index, color in enumerate(COLORS[:3]):
            pg.draw.circle(self.image, (*color, alpha), (64, 64),
                           max(2, radius - index * 6), 2)
        for index in range(12):
            angle = index * math.tau / 12 + fraction
            point = pg.Vector2(math.cos(angle), math.sin(angle))
            start = pg.Vector2(64, 64) + point * radius
            end = start + point * (8 * (1 - fraction))
            pg.draw.line(self.image, (*COLORS[index % 4], alpha), start, end, 3)


class GrinSeed(pg.sprite.Sprite):
    """Homes across lanes and disappears after one ordinary, armor-respecting hit."""

    _face = None

    def __init__(self, x, y, level, preferred_row, now):
        super().__init__()
        self.name = c.GRIN_SEED
        self.state = c.FLY
        self.damage = c.GRINDEVOURER_DAMAGE
        self.level = level
        self.preferred_row = preferred_row
        self.hit_zombies = set()
        self.spent = False
        self.pos = pg.Vector2(x, y)
        self.previous_pos = self.pos.copy()
        self.velocity = pg.Vector2(1, (preferred_row - (level.map_y_len - 1) / 2) * .3).normalize()
        self.born = self.last_time = now
        self.target = None
        self.image = pg.Surface((176, 144), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        # Decorative trails must not inflict damage: only the head has a hitbox.
        hitbox = pg.Surface(self.image.get_size(), pg.SRCALPHA)
        pg.draw.circle(hitbox, (255, 255, 255), (88, 72), 21)
        self.mask = pg.mask.from_surface(hitbox)
        if GrinSeed._face is None:
            face = pg.transform.smoothscale(tool.GFX['grin_face_comet'], (70, 70))
            face.set_colorkey(c.BLACK)
            GrinSeed._face = face.convert_alpha()
        self._render(now)

    def _seek(self):
        candidates = [(row, z) for row, group in enumerate(self.level.zombie_groups)
                      for z in group if z not in self.hit_zombies and targetable(z)]
        if candidates:
            self.target = min(candidates, key=lambda pair: (
                pair[0] != self.preferred_row,
                self.pos.distance_squared_to(pair[1].rect.center),
            ))[1]
        else:
            self.target = None

    def update(self, game_info):
        now = game_info[c.CURRENT_TIME]
        dt = max(0, min((now - self.last_time) / 1000, .05))
        self.last_time = now
        if self.spent or now - self.born >= c.GRIN_SEED_LIFETIME:
            self.kill()
            return
        if self.target is None or not targetable(self.target) or self.target in self.hit_zombies:
            self._seek()
        self.previous_pos = self.pos.copy()
        distance = None
        if self.target is not None:
            delta = pg.Vector2(self.target.rect.center) - self.pos
            distance = delta.length()
            if distance > .1:
                desired = delta.normalize()
                # Turn smoothly, including to enemies behind the plant.
                self.velocity = self.velocity.lerp(desired, min(1, dt * 16))
                if self.velocity.length_squared() > .001:
                    self.velocity.normalize_ip()
                else:
                    self.velocity = desired
        step = c.GRIN_SEED_SPEED * dt
        if distance is not None and distance < step:
            self.pos.update(self.target.rect.center)
        else:
            self.pos += self.velocity * step
        self.rect.center = self.pos
        if not pg.Rect(-140, -140, c.SCREEN_WIDTH + 280, c.SCREEN_HEIGHT + 280).collidepoint(self.pos):
            self.kill()
        self._render(now)

    def _render(self, now):
        self.image.fill((0, 0, 0, 0))
        center = pg.Vector2(88, 72)
        phase = (now - self.born) / 120
        side = pg.Vector2(-self.velocity.y, self.velocity.x)
        for index, color in enumerate(COLORS[:3]):
            points = []
            for step in range(12):
                distance = step * 5
                wobble = math.sin(phase - step * .5 + index * 2) * (3 + step * .6)
                points.append(center - self.velocity * distance + side * wobble)
            pg.draw.lines(self.image, (*color, 130), False, points, 5)
            pg.draw.lines(self.image, (*color, 235), False, points, 2)
        for index in range(6):
            angle = phase * .6 + index * math.tau / 6
            point = center + pg.Vector2(math.cos(angle) * 37, math.sin(angle) * 32)
            pg.draw.circle(self.image, (*COLORS[index % 4], 240), point, 2)
        # Gentle bob and pulse keep the photographed profile readable.
        scale = 1 + math.sin(phase) * .05
        face = pg.transform.rotozoom(self._face, math.sin(phase * .5) * 7, scale)
        self.image.blit(face, face.get_rect(center=center))

    def hits(self, zombie):
        if self.spent or zombie in self.hit_zombies or not targetable(zombie):
            return False
        core = zombie.rect.inflate(-min(26, zombie.rect.w // 3), -20)
        return bool(core.clipline(self.previous_pos, self.pos)) or bool(pg.sprite.collide_mask(self, zombie))

    def on_hit(self, zombie, effect_group):
        if self.spent:
            return
        self.spent = True
        zombie.setDamage(self.damage, effect=None, damage_type=c.ZOMBIE_DEAFULT_DAMAGE)
        self.level.impact_audio.play(
            'homing', zombie.rect.centerx, self.level.game_info[c.SOUND_VOLUME],
        )
        self.hit_zombies.add(zombie)
        effect_group.add(FaceImpact(self.pos, self.last_time))
        self.kill()
