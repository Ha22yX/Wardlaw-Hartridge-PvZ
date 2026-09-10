"""Animate the generated four walking and four eating poses, without gore."""

import math

import pygame as pg

from .. import constants as c


def install_assets(graphics):
    sheet = graphics['portrait_zombie_sheet'].copy()
    background = pg.mask.from_threshold(sheet, c.BLACK, (12, 12, 12, 255))
    background.to_surface(sheet, setcolor=c.BLACK, unsetcolor=None)
    sheet.set_colorkey(c.BLACK)
    sheet = sheet.convert_alpha()
    cell_w, cell_h = sheet.get_width() // 4, sheet.get_height() // 2
    poses = []
    for row in range(2):
        for col in range(4):
            cell = sheet.subsurface((col * cell_w, row * cell_h, cell_w, cell_h)).copy()
            cell = cell.subsurface(cell.get_bounding_rect(min_alpha=32)).copy()
            # Fixed height and a fixed planting baseline avoid feet jumping
            # when independent AI poses have slightly different margins.
            height = 144
            width = round(cell.get_width() * height / cell.get_height())
            sprite = pg.transform.smoothscale(cell, (width, height))
            canvas = pg.Surface((112, 160), pg.SRCALPHA)
            canvas.blit(sprite, sprite.get_rect(midbottom=(56, 158)))
            poses.append(canvas)

    install_animation_sets(graphics, c.PORTRAIT_ZOMBIE, poses)


def install_animation_sets(graphics, name, poses):
    """Shared complete animation sets, preserving each variant's canvas size."""
    width, height = poses[0].get_size()
    death_width = height + 24
    for suffix, offset in (('', 0), ('Attack', 4)):
        frames = []
        for i in range(12):
            canvas = pg.Surface((width, height), pg.SRCALPHA)
            phase = i * math.tau / 12
            sprite = poses[offset + i // 3]
            canvas.blit(sprite, (round(math.sin(phase)) if offset else 0,
                                 -round(abs(math.sin(phase)) * (1 if offset else 2))))
            frames.append(canvas)
        graphics[name + suffix] = frames
        tired = []
        for i, frame in enumerate(frames):
            canvas = frame.copy()
            for star in range(3):
                angle = i * math.tau / 12 + star * math.tau / 3
                x, y = round(width // 2 - 2 + math.cos(angle) * 23), round(13 + math.sin(angle) * 5)
                pg.draw.line(canvas, (255, 224, 81), (x - 3, y), (x + 3, y), 2)
                pg.draw.line(canvas, (255, 224, 81), (x, y - 3), (x, y + 3), 2)
            tired.append(canvas)
        graphics[name + ('LostHeadAttack' if offset else 'LostHead')] = tired

    idle = []
    for i in range(16):
        pose = poses[1]
        sprite = pg.transform.rotozoom(pose, math.sin(i * math.tau / 16) * 1.2, 1)
        canvas = pg.Surface((width, height), pg.SRCALPHA)
        canvas.blit(sprite, sprite.get_rect(midbottom=(width // 2, height)))
        idle.append(canvas)
    graphics[name + 'Idle'] = idle

    death, boom = [], []
    for i in range(20):
        t = i / 19
        canvas = pg.Surface((death_width, height), pg.SRCALPHA)
        tilt = min(1, t / .65)
        body = pg.transform.rotate(poses[2], 88 * tilt * tilt)
        body = body.subsurface(body.get_bounding_rect()).copy()
        body.set_alpha(round(255 * min(1, (1 - t) * 4)))
        canvas.blit(body, body.get_rect(midbottom=(death_width // 2, height - 1)))
        death.append(canvas)

        ash = pg.Surface((death_width, height), pg.SRCALPHA)
        mask = pg.mask.from_surface(body)
        silhouette = pg.Surface(body.get_size(), pg.SRCALPHA)
        mask.to_surface(silhouette, setcolor=(36, 32, 37, round(255 * (1 - t))), unsetcolor=(0, 0, 0, 0))
        ash.blit(silhouette, silhouette.get_rect(midbottom=(death_width // 2, height - 1)))
        for spark in range(10):
            angle = spark * 2.399
            x = round(death_width // 2 + math.sin(angle) * (12 + t * 46))
            y = round(height - 20 - spark * 10 - t * 45)
            pg.draw.circle(ash, (255, 150 + spark * 8, 49, round(220 * (1 - t))), (x, y), 2)
        boom.append(ash)
    graphics[name + 'Die'] = death
    graphics[name + 'BoomDie'] = boom
