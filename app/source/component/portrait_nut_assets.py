"""Build looping portrait-wall poses and two shell damage stages."""

import math

import pygame as pg

from .. import constants as c


def install_assets(graphics):
    source = graphics['portrait_tallnut'].copy()
    background = pg.mask.from_threshold(source, c.BLACK, (9, 9, 9, 255))
    background.to_surface(source, setcolor=c.BLACK, unsetcolor=None)
    source.set_colorkey(c.BLACK)
    source = source.convert_alpha()
    base = pg.transform.smoothscale(source, (94, 141))
    # Crack paths stay within the walnut shell, below the photographed face.
    cracks = [
        [(37, 65), (43, 78), (37, 88), (46, 100), (41, 111), (48, 130)],
        [(43, 78), (55, 84), (59, 94)],
        [(46, 100), (57, 108), (53, 122)],
        [(63, 61), (59, 73), (67, 83), (63, 96), (70, 106), (65, 124)],
        [(29, 81), (24, 92), (32, 104), (28, 121)],
    ]
    for tier in range(3):
        shell = base.copy()
        for path in cracks[:0 if tier == 0 else 2 if tier == 1 else 5]:
            pg.draw.lines(shell, (249, 206, 126), False,
                          [(x + 1, y) for x, y in path], 3)
            pg.draw.lines(shell, (53, 30, 17), False, path, 2 if tier == 1 else 3)
        frames = []
        for index in range(16):
            phase = index * math.tau / 16
            canvas = pg.Surface((110, 148), pg.SRCALPHA)
            body = pg.transform.smoothscale(shell, (94 + round(math.sin(phase)),
                                                    139 + round(math.cos(phase) * 2)))
            body = pg.transform.rotate(body, math.sin(phase) * (1.8 + tier * .5))
            canvas.blit(body, body.get_rect(midbottom=(55, 147)))
            frames.append(canvas)
        key = c.PORTRAITTALLNUT if tier == 0 else c.PORTRAITTALLNUT + f'_cracked{tier}'
        graphics[key] = frames
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((223, 193, 125))
    portrait = pg.transform.smoothscale(source, (64, 96))
    card.blit(portrait, (18, 2))
    title = pg.font.Font(c.FONT_PATH, 13).render(c.PLANT_DISPLAY_NAMES[c.PORTRAITTALLNUT], True, (58, 39, 18))
    card.blit(title, title.get_rect(center=(50, 98)))
    pg.draw.rect(card, (91, 62, 26), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_PORTRAITTALLNUT] = card
