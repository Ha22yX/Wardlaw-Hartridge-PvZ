"""Portrait bok-choy boxer assets, contact sparks and short punch sounds."""

from array import array
import math
import random

import pygame as pg

from .. import constants as c

SIZE = (196, 152)
ROOT = (98, 150)
# Gutters were inspected manually: bottom-left extended fist needs a wider cell.
REGIONS = [(a, 0, b - a, 480) for a, b in ((0, 380), (380, 760), (760, 1155), (1155, 1536))]
REGIONS += [(a, 480, b - a, 544) for a, b in ((0, 406), (406, 785), (785, 1180), (1180, 1536))]

# Source-photo silhouette only: facial pixels are copied, never regenerated.
PHOTO_OUTLINE = [(136, 119), (163, 97), (214, 88), (255, 69), (309, 59),
                 (350, 64), (388, 91), (425, 112), (454, 143), (476, 154),
                 (490, 185), (483, 220), (454, 256), (444, 291), (436, 321),
                 (431, 347), (432, 371), (418, 390), (402, 397), (401, 424),
                 (393, 448), (397, 468), (383, 492), (366, 508), (341, 538),
                 (295, 565), (252, 548), (229, 510), (211, 477), (192, 434),
                 (174, 396), (135, 394), (115, 371), (110, 332), (111, 284),
                 (119, 250), (123, 216), (118, 185), (122, 145)]
PHOTO_RECT = pg.Rect(110, 59, 381, 507)
NECKS = [(200, 254), (568, 254), (959, 254), (1323, 254),
         (174, 760), (577, 784), (936, 762), (1332, 773)]
EAR_COVERS = [(90, 65, 70, 150), (458, 65, 72, 150), (860, 65, 75, 150), (1214, 65, 75, 150),
              (65, 554, 78, 158), (478, 580, 75, 153), (814, 554, 75, 158), (1224, 554, 75, 158)]


def original_head(photo):
    mask = pg.Surface(photo.get_size(), pg.SRCALPHA)
    pg.draw.polygon(mask, (255, 255, 255, 255), PHOTO_OUTLINE)
    head = photo.convert_alpha().copy()
    head.blit(mask, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    return head.subsurface(PHOTO_RECT).copy()


def leaf_body(cell, region, ear_cover):
    """Retain generated green leaves/stalks, discard generated human features."""
    body = cell.copy()
    pixels = pg.PixelArray(body)
    shifts = body.get_shifts()
    ear = pg.Rect(ear_cover).move(-region[0], -region[1])
    for y in range(body.get_height()):
        for x in range(body.get_width()):
            pixel = pixels[x, y]
            r, g, b = ((pixel >> s) & 255 for s in shifts[:3])
            if g <= b + 8 or g < r - 8 or ear.collidepoint(x, y):
                pixels[x, y] = 0
    pixels.close()
    return body


def install_assets(graphics):
    sheet = graphics['headphone_boxer_sheet'].copy()
    if sheet.get_size() != (1536, 1024):
        raise ValueError('Headphone boxer source size changed; recheck its crop regions')
    background = pg.mask.from_threshold(sheet, c.BLACK, (9, 9, 9, 255))
    background.to_surface(sheet, setcolor=c.BLACK, unsetcolor=None)
    sheet.set_colorkey(c.BLACK)
    sheet = sheet.convert_alpha()
    pieces, bodies, centers, source_bounds = [], [], [], []
    for index, region in enumerate(REGIONS):
        cell = sheet.subsurface(region)
        bounds = cell.get_bounding_rect(min_alpha=32)
        if not (bounds.left > 2 and bounds.top > 2 and
                bounds.right < cell.get_width() - 2 and bounds.bottom < cell.get_height() - 2):
            raise ValueError('Boxer pose touches crop boundary')
        base_y = bounds.bottom - round(bounds.height * .12)
        base = cell.subsurface((0, base_y, cell.get_width(), bounds.bottom - base_y))
        centers.append(base.get_bounding_rect(min_alpha=32).centerx - bounds.x)
        pieces.append(cell.subsurface(bounds).copy())
        bodies.append(leaf_body(cell, region, EAR_COVERS[index]).subsurface(bounds).copy())
        source_bounds.append(bounds)
    scale = 140 / max(p.get_height() for p in pieces)
    head = original_head(graphics['boxer_original_photo'])
    graphics[c.HEADPHONEBOXER + 'OriginalHead'] = head
    head_scale = 87 / head.get_height()
    head = pg.transform.smoothscale(head, (round(head.get_width() * head_scale), 87))
    # Anchor to the original-photo neck, retaining one identical head texture
    # across every pose; arms/body move underneath it.
    head_anchor = (round((278 - PHOTO_RECT.x) * head_scale), round((552 - PHOTO_RECT.y) * head_scale))
    poses = []
    for index, (piece, center) in enumerate(zip(bodies, centers)):
        sprite = pg.transform.smoothscale(piece, (round(piece.get_width() * scale), round(piece.get_height() * scale)))
        canvas = pg.Surface(SIZE, pg.SRCALPHA)
        origin = (ROOT[0] - round(center * scale), ROOT[1] - sprite.get_height())
        canvas.blit(sprite, origin)
        region, bounds = REGIONS[index], source_bounds[index]
        neck = (origin[0] + round((NECKS[index][0] - region[0] - bounds.x) * scale),
                origin[1] + round((NECKS[index][1] - region[1] - bounds.y) * scale))
        canvas.blit(head, (neck[0] - head_anchor[0], neck[1] - head_anchor[1]))
        poses.append(canvas)
    graphics[c.HEADPHONEBOXER + 'Poses'] = poses
    # Keep the neutral silhouette as the actual hurtbox; extended fists are not
    # extra body area that zombies can bite from farther away.
    idle = []
    for i in range(16):
        idle.append(poses[0 if i < 8 else 1].copy())
    graphics[c.HEADPHONEBOXER] = idle
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((213, 223, 158))
    portrait = pg.transform.rotozoom(poses[0], 0, 92 / SIZE[1])
    card.blit(portrait, portrait.get_rect(midbottom=(50, 95)))
    title = pg.font.Font(c.FONT_PATH, 13).render(c.PLANT_DISPLAY_NAMES[c.HEADPHONEBOXER], True, (36, 67, 29))
    card.blit(title, title.get_rect(center=(50, 101)))
    pg.draw.rect(card, (57, 89, 41), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_HEADPHONEBOXER] = card


class PunchImpact(pg.sprite.Sprite):
    def __init__(self, point, born, direction, heavy=False):
        super().__init__()
        self.name = c.FUME
        self.born, self.direction, self.heavy = born, direction, heavy
        self.image = pg.Surface((128, 128), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=point)
        self.update({c.CURRENT_TIME: born})

    def update(self, info):
        age = info[c.CURRENT_TIME] - self.born
        if age >= 280:
            self.kill()
            return
        t = max(0, age / 280)
        self.image.fill((0, 0, 0, 0))
        alpha = round(245 * (1 - t))
        radius = (15 if self.heavy else 10) + t * 30
        vertices = []
        for i in range(20):
            angle = math.tau * i / 20
            r = radius if i % 2 == 0 else radius * .42
            vertices.append((64 + math.cos(angle) * r, 64 + math.sin(angle) * r))
        pg.draw.polygon(self.image, (255, 215, 75, alpha), vertices)
        pg.draw.circle(self.image, (255, 255, 228, alpha), (64, 64), max(1, round(10 * (1 - t))))
        for i in range(5):
            yy = 45 + i * 9
            end = 57 - self.direction * 18
            pg.draw.line(self.image, (190, 244, 92, alpha), (end, yy),
                         (end - self.direction * (15 + 25 * t), yy), 2)


_sounds = {}


def play_punch(volume, heavy=False):
    settings = pg.mixer.get_init()
    if settings is None or settings[1] != -16:
        return
    rate, _, channels = settings
    key = (rate, channels, heavy)
    if key not in _sounds:
        rng = random.Random(41)
        samples = array('h')
        duration = .14 if heavy else .085
        for i in range(round(rate * duration)):
            t = i / rate
            decay = (1 - t / duration) ** 3
            wave = math.sin(math.tau * (105 if heavy else 170) * t) * .6 + rng.uniform(-1, 1) * .4
            value = round(16000 * wave * decay * min(1, t / .003))
            samples.extend([value] * channels)
        _sounds[key] = pg.mixer.Sound(buffer=samples.tobytes())
    _sounds[key].set_volume(max(0, min(1, volume)) * .45)
    _sounds[key].play()
