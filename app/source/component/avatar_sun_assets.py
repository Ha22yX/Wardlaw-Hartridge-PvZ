"""One shared portrait replaces sun drops, producer output and currency icons."""

import math

import pygame as pg

from .. import constants as c


def install_assets(graphics):
    portrait = graphics['avatar_sun'].copy()
    background = pg.mask.from_threshold(portrait, c.BLACK, (9, 9, 9, 255))
    background.to_surface(portrait, setcolor=c.BLACK, unsetcolor=None)
    portrait.set_colorkey(c.BLACK)
    portrait = portrait.convert_alpha()
    head = pg.transform.smoothscale(portrait, (66, 66))
    frames = []
    for index in range(16):
        phase = index * math.tau / 16
        canvas = pg.Surface((78, 78), pg.SRCALPHA)
        pg.draw.circle(canvas, (255, 190, 36, 45), (39, 39), 34)
        for spark in range(5):
            angle = phase + spark * math.tau / 5
            point = pg.Vector2(39, 39) + pg.Vector2(math.cos(angle), math.sin(angle)) * 33
            pg.draw.circle(canvas, (255, 232, 109, 220), point, 2)
        face = pg.transform.rotozoom(head, math.sin(phase) * 5, 1 + math.sin(phase) * .025)
        canvas.blit(face, face.get_rect(center=(39, 39)))
        frames.append(canvas)
    # Sun, SunShroom and GasSun all use this same named sprite bank.
    graphics[c.SUN] = frames

    # The currency emblem is embedded in the chooser background for both the
    # selection panel and the in-game menu; replace it once at asset setup.
    chooser = graphics[c.MENUBAR_BACKGROUND].copy()
    pg.draw.circle(chooser, (89, 53, 23), (40, 34), 24)
    pg.draw.circle(chooser, (237, 193, 98), (40, 34), 24, 2)
    chooser.blit(pg.transform.smoothscale(portrait, (45, 45)), (18, 11))
    graphics[c.MENUBAR_BACKGROUND] = chooser

    # Cover only the small currency badge, preserving the plant illustration,
    # text and price area. This also includes all custom plant cards.
    badge = pg.transform.smoothscale(portrait, (23, 26))
    for key in list(graphics):
        if not key.startswith('card_'):
            continue
        card = graphics[key].copy()
        if card.get_size() != (100, 140):
            continue
        pg.draw.rect(card, (249, 250, 213), (66, 106, 29, 29))
        card.blit(badge, (69, 107))
        graphics[key] = card
