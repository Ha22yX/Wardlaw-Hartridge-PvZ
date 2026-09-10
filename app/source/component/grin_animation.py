"""Right-facing eight-pose sheet, measured bounds and a stable root anchor."""

import math

import pygame as pg

from .. import constants as c

SIZE = (160, 156)
ROOT = (80, 153)
WINDUP_MS = 420
FIRE_MS = 180
RECOVER_MS = 260

# Reviewed empty gutters in the 1536 x 1024 source, not assumed equal cells.
REGIONS = [(x0, y0, x1 - x0, y1 - y0)
           for y0, y1 in ((0, 510), (510, 1024))
           for x0, x1 in ((0, 380), (380, 765), (765, 1155), (1155, 1536))]


def _sway(pose, offset):
    canvas = pg.Surface(SIZE, pg.SRCALPHA)
    for y in range(SIZE[1]):
        # Lower leaves stay anchored; only the upper body recoils/breathes.
        weight = max(0, 1 - y / 116) ** 2
        canvas.blit(pose, (round(offset * weight), y), (0, y, SIZE[0], 1))
    return canvas


def install_assets(graphics):
    sheet = graphics['grin_sheet_right_v3'].copy()
    if sheet.get_size() != (1536, 1024):
        raise ValueError('Re-measure Grin source regions if the source resolution changes')
    background = pg.mask.from_threshold(sheet, c.BLACK, (10, 10, 10, 255))
    background.to_surface(sheet, setcolor=c.BLACK, unsetcolor=None)
    sheet.set_colorkey(c.BLACK)
    sheet = sheet.convert_alpha()
    pieces, anchors = [], []
    for region in REGIONS:
        cell = sheet.subsurface(region)
        bounds = cell.get_bounding_rect(min_alpha=32)
        if not (bounds.left > 2 and bounds.top > 2 and
                bounds.right < cell.get_width() - 2 and bounds.bottom < cell.get_height() - 2):
            raise ValueError('Grin pose touches crop boundary: inspect the sheet before slicing')
        # Center on the lower leaf rosette, not on the leaning head/phone.
        base_y = bounds.bottom - round(bounds.h * .16)
        base = cell.subsurface((0, base_y, cell.get_width(), bounds.bottom - base_y))
        base_bounds = base.get_bounding_rect(min_alpha=32)
        anchors.append((base_bounds.centerx - bounds.x, bounds.h))
        pieces.append(cell.subsurface(bounds).copy())
    scale = 142 / max(piece.get_height() for piece in pieces)
    poses = []
    for piece, anchor in zip(pieces, anchors):
        width, height = round(piece.get_width() * scale), round(piece.get_height() * scale)
        sprite = pg.transform.smoothscale(piece, (width, height))
        pose = pg.Surface(SIZE, pg.SRCALPHA)
        pose.blit(sprite, (ROOT[0] - round(anchor[0] * scale), ROOT[1] - height))
        poses.append(pose)
    # Actual right mouth edge in open-mouth source pose (#5).
    open_region = REGIONS[5]
    open_bounds = sheet.subsurface(open_region).get_bounding_rect(min_alpha=32)
    mouth = (747 - open_region[0] - open_bounds.x,
             714 - open_region[1] - open_bounds.y)
    graphics[c.GRINDEVOURER + 'Muzzle'] = (
        round((mouth[0] - anchors[5][0]) * scale),
        round((mouth[1] - anchors[5][1]) * scale),
    )
    graphics[c.GRINDEVOURER + 'SourcePoses'] = poses
    graphics[c.GRINDEVOURER] = [
        _sway(poses[i // 6], math.sin(i * math.tau / 24)) for i in range(24)]
    graphics[c.GRINDEVOURER + 'Attack'] = [
        _sway(poses[4 if i < 8 else 5], -math.sin(i / 11 * math.pi)) for i in range(12)]
    graphics[c.GRINDEVOURER + 'Fire'] = [
        _sway(poses[5 if i < 2 else 6], -3 * math.sin(i / 9 * math.pi)) for i in range(10)]
    graphics[c.GRINDEVOURER + 'Recover'] = [
        _sway(poses[6 if i < 3 else 7], -max(0, 1 - i / 11)) for i in range(12)]
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((220, 202, 139))
    portrait = pg.transform.rotozoom(pieces[0], 0, 90 / pieces[0].get_height())
    card.blit(portrait, portrait.get_rect(midbottom=(50, 94)))
    title = pg.font.Font(c.FONT_PATH, 13).render(c.PLANT_DISPLAY_NAMES[c.GRINDEVOURER], True, (35, 65, 26))
    card.blit(title, title.get_rect(center=(50, 101)))
    pg.draw.rect(card, (63, 89, 29), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_GRINDEVOURER] = card
