"""Complete generated bruiser sprites, isolated by connected silhouettes."""

import pygame as pg
from .. import constants as c
from .portrait_zombie_assets import install_animation_sets

SIZE = (152, 184)
# Inspected torso seeds, avoiding fixed grid cuts across oversized hands.
SEEDS = [(235, 225), (598, 250), (970, 235), (1310, 245),
         (236, 700), (600, 700), (985, 700), (1363, 700)]


def install_assets(graphics):
    sheet = graphics['elite_zombie_full_sheet'].copy()
    if sheet.get_size() != (1536, 1024):
        raise ValueError('Elite zombie source changed: recheck silhouette seeds')
    sheet.set_colorkey(None)
    sheet = sheet.convert_alpha()
    # Only remove backdrop connected to the image edge. Dark facial details,
    # sweatshirt folds and shoe laces are not transparent holes.
    background = pg.mask.from_threshold(sheet, c.BLACK, (8, 8, 8, 255))
    background = background.connected_component((0, 0))
    background.to_surface(sheet, setcolor=(0, 0, 0, 0), unsetcolor=None)
    all_pixels = pg.mask.from_surface(sheet, 32)
    pieces, source_bounds = [], []
    for index, seed in enumerate(SEEDS):
        mask = all_pixels.connected_component(seed)
        bounds_list = mask.get_bounding_rects()
        if not bounds_list:
            raise ValueError('Elite body seed missed its sprite')
        bounds = bounds_list[0]
        if not (250 < bounds.width < 430 and 400 < bounds.height < 500):
            raise ValueError(f'Elite sprite joined another sprite: {bounds}')
        mask_surface = pg.Surface(sheet.get_size(), pg.SRCALPHA)
        mask.to_surface(mask_surface, setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        piece = sheet.subsurface(bounds).copy()
        piece.blit(mask_surface.subsurface(bounds), (0, 0), special_flags=pg.BLEND_RGBA_MULT)
        if index == 3:
            piece = pg.transform.flip(piece, True, False)
        pieces.append(piece)
        source_bounds.append(bounds)
    if len({tuple(b) for b in source_bounds}) != 8:
        raise ValueError('Duplicate elite zombie silhouette')
    graphics[c.ELITE_PORTRAIT_ZOMBIE + 'SourceBounds'] = source_bounds
    scale = 162 / max(p.get_height() for p in pieces)
    poses = []
    for piece in pieces:
        sprite = pg.transform.smoothscale(piece, (round(piece.get_width() * scale),
                                                  round(piece.get_height() * scale)))
        canvas = pg.Surface(SIZE, pg.SRCALPHA)
        canvas.blit(sprite, sprite.get_rect(midbottom=(SIZE[0] // 2, SIZE[1] - 2)))
        poses.append(canvas)
    graphics[c.ELITE_PORTRAIT_ZOMBIE + 'Poses'] = poses
    install_animation_sets(graphics, c.ELITE_PORTRAIT_ZOMBIE, poses)
