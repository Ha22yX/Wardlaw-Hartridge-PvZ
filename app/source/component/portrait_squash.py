"""Two expression poses and cosmetic crushing effects."""
import math
import pygame as pg
from .. import constants as c

SIZE = (126, 156)
ROOT = (63, 154)


def install_assets(graphics):
    sheet = graphics['portrait_squash_sheet_v2'].copy()
    sheet.set_colorkey(None)
    sheet = sheet.convert_alpha()
    bg = pg.mask.from_threshold(sheet, c.BLACK, (8, 8, 8, 255))
    bg.connected_component((0, 0)).to_surface(sheet, setcolor=(0, 0, 0, 0), unsetcolor=None)
    masks = pg.mask.from_surface(sheet).connected_components(10000)
    if len(masks) != 2:
        raise ValueError('Portrait squash needs exactly two separate expression silhouettes')
    masks.sort(key=lambda m: m.get_bounding_rects()[0].x)
    poses = []
    for mask in masks:
        rect = mask.get_bounding_rects()[0]
        pose = sheet.subsurface(rect).copy()
        factor = min(108 / rect.width, 140 / rect.height)
        pose = pg.transform.smoothscale(pose, (round(rect.width * factor), round(rect.height * factor)))
        canvas = pg.Surface(SIZE, pg.SRCALPHA)
        canvas.blit(pose, pose.get_rect(midbottom=ROOT))
        poses.append(canvas)
    graphics[c.PORTRAITSQUASH + 'Calm'] = poses[0]
    graphics[c.PORTRAITSQUASH + 'Angry'] = poses[1]
    idle = []
    for i in range(20):
        frame = pg.Surface(SIZE, pg.SRCALPHA)
        body = pg.transform.rotozoom(poses[0], math.sin(i * math.tau / 20) * 1.2, 1)
        frame.blit(body, body.get_rect(midbottom=(63, 156)))
        idle.append(frame)
    graphics[c.PORTRAITSQUASH] = idle
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((202, 218, 149))
    icon = pg.transform.rotozoom(poses[0], 0, 95 / SIZE[1])
    card.blit(icon, icon.get_rect(midbottom=(50, 96)))
    title = pg.font.Font(c.FONT_PATH, 13).render(c.PLANT_DISPLAY_NAMES[c.PORTRAITSQUASH], True, (44, 67, 22))
    card.blit(title, title.get_rect(center=(50, 102)))
    pg.draw.rect(card, (63, 96, 37), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_PORTRAITSQUASH] = card


class SquashDust(pg.sprite.Sprite):
    def __init__(self, point, born):
        super().__init__()
        self.name, self.born = c.FUME, born
        self.image = pg.Surface((240, 120), pg.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(point[0], point[1] + 15))
        self.update({c.CURRENT_TIME: born})

    def update(self, info):
        age = info[c.CURRENT_TIME] - self.born
        if age >= 850:
            self.kill()
            return
        t = max(0, age / 850)
        self.image.fill((0, 0, 0, 0))
        alpha = round(200 * (1 - t))
        w = round(40 + t * 180)
        pg.draw.ellipse(self.image, (237, 215, 132, alpha), (120 - w // 2, 83 - w // 12, w, 12 + w // 6), 3)
        for i in range(10):
            angle = i * math.tau / 10
            x = 120 + round(math.cos(angle) * (15 + t * 88))
            y = 88 - round(abs(math.sin(angle)) * (5 + t * 48))
            pg.draw.circle(self.image, (177, 152, 94, alpha), (x, y), round(4 + t * 10))


class FlattenedZombie(pg.sprite.Sprite):
    """Squashed snapshot, not a second damage source or living enemy."""
    def __init__(self, victim, born):
        super().__init__()
        self.name, self.born = c.FUME, born
        self.source = victim.image.copy()
        self.point = victim.rect.midbottom
        self.image = self.source
        self.rect = self.image.get_rect(midbottom=self.point)
        self.update({c.CURRENT_TIME: born})

    def update(self, info):
        age = info[c.CURRENT_TIME] - self.born
        if age >= 1100:
            self.kill()
            return
        t = min(1, max(0, age / 120))
        self.image = pg.transform.smoothscale(
            self.source, (round(self.source.get_width() * (1 + .28 * t)),
                          max(12, round(self.source.get_height() * (1 - .87 * t)))))
        if age > 600:
            self.image.set_alpha(round(255 * (1100 - age) / 500))
        self.rect = self.image.get_rect(midbottom=self.point)
