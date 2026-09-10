"""Big-head sprite animation, botanical gas clouds and a synthesized puff."""

from array import array
import math
import random

import pygame as pg

from .. import constants as c


def install_assets(graphics):
    # Convert the generated black backdrop before scaling or rotating.
    source = graphics['sun_gas_portrait'].copy()
    # Generated backdrops may contain almost-black speckles as well as #000.
    background = pg.mask.from_threshold(source, c.BLACK, (9, 9, 9, 255))
    background.to_surface(source, setcolor=c.BLACK, unsetcolor=None)
    source.set_colorkey(c.BLACK)
    source = source.convert_alpha()
    base = pg.transform.smoothscale(source, (96, 144))

    def pose(width, height, angle=0, offset=0):
        canvas = pg.Surface((112, 144), pg.SRCALPHA)
        body = pg.transform.smoothscale(base, (width, height))
        body = pg.transform.rotate(body, angle)
        canvas.blit(body, body.get_rect(midbottom=(56 + offset, 144)))
        # Mirror the whole animated pose, including recoil, to face right.
        return pg.transform.flip(canvas, True, False)

    idle, charge, release = [], [], []
    for index in range(12):
        breath = math.sin(index * math.tau / 12)
        idle.append(pose(96 + round(breath), 140 + round(breath * 2)))
    for index in range(8):
        # The massive head squashes as the belly appears to inflate.
        charge.append(pose(96 + index * 2, 140 - index * 3,
                           0, (index % 2 * 2 - 1) * 2))
        recoil = math.sin(index / 7 * math.pi)
        release.append(pose(103 - index, 126 + index * 2,
                            round(recoil * 6), -round(recoil * 3)))
    graphics[c.GASSUNFLOWER] = idle
    graphics[c.GASSUNFLOWER + 'Charge'] = charge
    graphics[c.GASSUNFLOWER + 'Release'] = release

    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((204, 218, 139))
    pg.draw.rect(card, (235, 229, 176), (5, 105, 90, 31))
    portrait = pg.transform.smoothscale(pg.transform.flip(source, True, False), (70, 105))
    card.blit(portrait, (15, 1))
    font = pg.font.Font(c.FONT_PATH, 14)
    title = font.render(c.PLANT_DISPLAY_NAMES[c.GASSUNFLOWER], True, (44, 67, 24))
    card.blit(title, title.get_rect(center=(50, 98)))
    pg.draw.rect(card, (70, 94, 32), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_GASSUNFLOWER] = card


class SunGasCloud(pg.sprite.Sprite):
    def __init__(self, origin, now, direction=1):
        super().__init__()
        self.name = c.FUME  # Decorative only; no projectile collision.
        self.born = now
        self.direction = direction
        self.image = pg.Surface((190, 120), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=origin)
        self.update({c.CURRENT_TIME: now})

    def update(self, game_info):
        age = game_info[c.CURRENT_TIME] - self.born
        if age >= 1800:
            self.kill()
            return
        progress = max(0, age / 1800)
        self.image.fill((0, 0, 0, 0))
        alpha = round(180 * (1 - progress))
        for index in range(7):
            x = 85 + self.direction * (progress * 45 + index * 5)
            y = 77 - progress * 36 + math.sin(index * 1.9) * 15
            radius = round(10 + progress * 13 + index % 3 * 3)
            color = ((129, 179, 36), (187, 223, 63), (93, 152, 51))[index % 3]
            pg.draw.circle(self.image, (*color, alpha), (round(x), round(y)), radius)
        for index in range(8):
            angle = index * math.tau / 8 + progress * 2
            x = 95 + math.cos(angle) * (10 + progress * 55)
            y = 63 + math.sin(angle) * (8 + progress * 30)
            pg.draw.line(self.image, (255, 230, 82, alpha), (x - 3, y), (x + 3, y), 2)
            pg.draw.line(self.image, (255, 248, 165, alpha), (x, y - 3), (x, y + 3), 2)


_puff = None


def play_puff(volume):
    global _puff
    settings = pg.mixer.get_init()
    if settings is None:
        return
    rate, sample_format, channels = settings
    if sample_format != -16:
        return
    if _puff is None:
        rng = random.Random(77)
        samples = array('h')
        duration = .32
        phase = 0
        for index in range(int(rate * duration)):
            t = index / rate
            phase += math.tau * (95 - 55 * t / duration) / rate
            flutter = .6 + .4 * math.sin(t * 110)
            envelope = min(1, t / .012) * (1 - t / duration) ** 2
            wave = .55 * math.sin(phase) + .2 * math.sin(phase * 3) + .18 * rng.uniform(-1, 1)
            sample = round(13000 * wave * flutter * envelope)
            samples.extend([sample] * channels)
        _puff = pg.mixer.Sound(buffer=samples.tobytes())
    _puff.set_volume(max(0, min(1, volume)) * .5)
    _puff.play()
