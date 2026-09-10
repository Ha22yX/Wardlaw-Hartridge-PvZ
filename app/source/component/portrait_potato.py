"""Root-aligned mine poses and a cosmetic dirt/fire burst."""

import math
import random
import pygame as pg
from .. import constants as c

SIZE = (128, 140)
ROOT = (64, 138)


def cutout(source):
    # Remove only connected near-black backdrop, not dark hair/glasses.
    source = source.copy()
    source.set_colorkey(None)
    source = source.convert_alpha()
    background = pg.mask.from_threshold(source, (0, 0, 0), (18, 18, 18, 255))
    for region in background.connected_components():
        bounds = region.get_bounding_rects()
        if bounds and any(b.left == 0 or b.top == 0 or b.right == source.get_width()
                          or b.bottom == source.get_height() for b in bounds):
            region.to_surface(source, setcolor=(0, 0, 0, 0), unsetcolor=None)
    return source.subsurface(source.get_bounding_rect(min_alpha=16)).copy()


def place(sprite, angle=0, scale=1, bob=0):
    image = pg.Surface(SIZE, pg.SRCALPHA)
    body = pg.transform.rotozoom(sprite, angle, scale)
    image.blit(body, body.get_rect(midbottom=(ROOT[0], ROOT[1] + bob)))
    return image


def install_assets(graphics):
    standing = cutout(graphics['portrait_potato_mine'])
    buried = cutout(graphics['portrait_potato_buried'])
    standing = pg.transform.rotozoom(standing, 0, 112 / standing.get_height())
    buried = pg.transform.rotozoom(buried, 0, standing.get_width() / buried.get_width())
    graphics[c.PORTRAITPOTATOMINE + 'Base'] = standing
    idle, underground, rising, warning = [], [], [], []
    for i in range(20):
        phase = i * math.tau / 20
        pose = place(standing, math.sin(phase) * 1.3, bob=round(math.sin(phase) * 1))
        # Pulse the bulb, keeping the photographed face unchanged.
        glow = pg.Surface(SIZE, pg.SRCALPHA)
        pg.draw.circle(glow, (255, 64, 25, round(35 + 30 * (1 + math.sin(phase)))),
                       (75, 34), 8)
        pose.blit(glow, (0, 0))
        idle.append(pose)
        underground.append(place(buried, math.sin(phase) * .7))
        progress = i / 19
        canvas = pg.Surface(SIZE, pg.SRCALPHA)
        emerge = place(standing, bob=round((1 - progress) * 62))
        emerge.set_alpha(round(255 * progress))
        canvas.blit(emerge, (0, 0))
        dirt = place(buried)
        dirt.set_alpha(round(255 * (1 - progress)))
        canvas.blit(dirt, (0, 0))
        for chip in range(6):
            px = 30 + chip * 13
            py = 127 - round(math.sin(progress * math.pi) * (8 + chip % 3 * 5))
            pg.draw.circle(canvas, (144, 85, 37, round(255 * (1 - progress))), (px, py), 2)
        rising.append(canvas)
        charged = place(standing, math.sin(i * 2) * 2, 1 + .13 * progress)
        charged.fill((round(progress * 65), round(progress * 20), 0, 0),
                     special_flags=pg.BLEND_RGBA_ADD)
        warning.append(charged)
    for suffix, frames in (('', idle), ('Init', underground), ('Rise', rising), ('Warning', warning)):
        graphics[c.PORTRAITPOTATOMINE + suffix] = frames
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((225, 203, 158))
    portrait = pg.transform.rotozoom(standing, 0, 90 / standing.get_height())
    card.blit(portrait, portrait.get_rect(midbottom=(50, 94)))
    title = pg.font.Font(c.FONT_PATH, 13).render(c.PLANT_DISPLAY_NAMES[c.PORTRAITPOTATOMINE], True, (72, 43, 22))
    card.blit(title, title.get_rect(center=(50, 101)))
    pg.draw.rect(card, (99, 65, 33), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_PORTRAITPOTATOMINE] = card


class PotatoBurst(pg.sprite.Sprite):
    """Visual only: game damage is resolved once by the level."""
    def __init__(self, x, y, born):
        super().__init__()
        self.name = c.FUME
        self.born = born
        self.image = pg.Surface((320, 260), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y - 35))
        rng = random.Random(47)
        self.chips = [(rng.uniform(-110, 110), rng.uniform(-210, -70), rng.randint(3, 8))
                      for _ in range(24)]
        self.update({c.CURRENT_TIME: born})

    def update(self, game_info):
        age = game_info[c.CURRENT_TIME] - self.born
        if age >= 1400:
            self.kill()
            return
        t = max(0, age / 1000)
        self.image.fill((0, 0, 0, 0))
        fade = max(0, 1 - age / 1400)
        center = (160, 150)
        if age < 550:
            radius = round(12 + 95 * age / 550)
            pg.draw.circle(self.image, (255, 177, 39, round(235 * (1 - age / 550))),
                           center, radius, 7)
            for i in range(9):
                a = i * math.tau / 9
                point = (160 + round(math.cos(a) * radius * .55),
                         150 + round(math.sin(a) * radius * .45))
                pg.draw.circle(self.image, (255, 95 + i * 8, 20, round(230 * fade)),
                               point, max(1, round((25 - age / 30) * fade)))
            pg.draw.circle(self.image, (255, 249, 190, round(240 * (1 - age / 550))),
                           center, max(1, round(32 * (1 - age / 550))))
        for vx, vy, size in self.chips:
            px, py = round(160 + vx * t), round(150 + vy * t + 140 * t * t)
            pg.draw.polygon(self.image, (139, 80, 34, round(255 * fade)),
                            [(px - size, py), (px, py - size), (px + size, py + size)])
        for i in range(7):
            px = 160 + round(math.sin(i * 2.4) * (25 + t * 60))
            py = 157 - round(t * (20 + i * 5))
            pg.draw.circle(self.image, (139, 117, 86, round(90 * fade)),
                           (px, py), round(8 + t * 18))
