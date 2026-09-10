"""Separate idle/open portraits, plus a non-blocking plant-eating animation."""

import math

import pygame as pg

from .. import constants as c


def install_assets(graphics):
    portraits = {}
    for state in ('idle', 'open', 'chew'):
        source = graphics['shovel_face_' + state].copy()
        background = pg.mask.from_threshold(source, c.BLACK, (9, 9, 9, 255))
        background.to_surface(source, setcolor=c.BLACK, unsetcolor=None)
        source.set_colorkey(c.BLACK)
        portraits[state] = source.convert_alpha()
    graphics[c.SHOVEL] = pg.transform.smoothscale(portraits['idle'], (71, 67))
    graphics['shovel_open_cursor'] = pg.transform.smoothscale(portraits['open'], (96, 96))
    graphics['shovel_bite_open'] = pg.transform.smoothscale(portraits['open'], (118, 118))
    frames = []
    # Chewing alternates actual independently generated cheek/mouth expressions.
    sequence = ('chew', 'chew', 'idle', 'open', 'chew', 'idle', 'chew', 'chew')
    for index, state in enumerate(sequence):
        image = pg.Surface((128, 128), pg.SRCALPHA)
        width = 118 + round(math.sin(index * math.pi / 2) * 6)
        height = 118 - (5 if index % 2 else 0)
        face = pg.transform.smoothscale(portraits[state], (width, height))
        image.blit(face, face.get_rect(center=(64, 64)))
        frames.append(image)
    graphics['shovel_chew_frames'] = frames
    graphics['shovel_chew_toolbar'] = [pg.transform.smoothscale(frame, (78, 73)) for frame in frames]


class ShovelChew(pg.sprite.Sprite):
    DURATION = 1700

    def __init__(self, graphics, victim, now):
        super().__init__()
        self.graphics = graphics
        self.born = now
        from .plant_layout import sprite
        visible, visible_rect = sprite(victim)
        self.victim = visible.copy().convert_alpha()
        # Use a roomy canvas for the victim shrinking into the mouth.
        self.image = pg.Surface((260, 240), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=(visible_rect.centerx + 24, visible_rect.centery))
        self.victim_center = pg.Vector2(visible_rect.center) - pg.Vector2(self.rect.topleft)
        self.update({c.CURRENT_TIME: now})

    def update(self, game_info):
        age = max(0, game_info[c.CURRENT_TIME] - self.born)
        if age >= self.DURATION:
            self.kill()
            return
        self.image.fill((0, 0, 0, 0))
        head_center = pg.Vector2(149, 103)
        mouth = head_center + pg.Vector2(-23, 26)
        if age < 320:
            head = self.graphics['shovel_bite_open']
            self.image.blit(head, head.get_rect(center=head_center))
            fraction = age / 320
            food = pg.transform.rotozoom(self.victim, fraction * -30,
                                          max(.04, 1 - fraction * .96))
            food.set_alpha(round(255 * (1 - fraction * .65)))
            point = self.victim_center.lerp(mouth, fraction)
            self.image.blit(food, food.get_rect(center=point))
        else:
            index = int((age - 320) / 110) % len(self.graphics['shovel_chew_frames'])
            head = self.graphics['shovel_chew_frames'][index].copy()
            # A small final swallow and fade after two chewing cycles.
            if age > 1450:
                head.set_alpha(round(255 * (self.DURATION - age) / 250))
            bounce = math.sin((age - 320) / 55) * 3
            self.image.blit(head, head.get_rect(center=(head_center.x, head_center.y + bounce)))
            for crumb in range(5):
                angle = crumb * 1.6 + age / 170
                center = mouth + pg.Vector2(-10 - crumb * 5, math.sin(angle) * 10 + 5)
                pg.draw.ellipse(self.image, (152, 201, 75, max(0, 210 - age // 9)),
                                (center.x, center.y, 5, 3))
