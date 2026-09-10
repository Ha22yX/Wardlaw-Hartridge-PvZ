"""Reuse this project's existing paper frame and buttons, without a new UI skin."""
import pygame as pg
from .. import constants as c

_panels = {}


def paper_panel(size):
    from .. import tool
    size = tuple(size)
    if size not in _panels:
        source = tool.GFX[c.GAME_VICTORY_IMAGE].subsurface((117, 241, 548, 265)).copy()
        # Remove the baked-in text while retaining this project's existing frame.
        source.fill(source.get_at((30, 30)), (12, 12, 524, 241))
        result = pg.Surface(size, pg.SRCALPHA)
        edge = min(12, size[0] // 3, size[1] // 3)
        src_x, src_y = (0, edge, source.get_width() - edge, source.get_width()), (0, edge, source.get_height() - edge, source.get_height())
        dst_x, dst_y = (0, edge, size[0] - edge, size[0]), (0, edge, size[1] - edge, size[1])
        for row in range(3):
            for col in range(3):
                piece = source.subsurface((src_x[col], src_y[row],
                                           src_x[col + 1] - src_x[col], src_y[row + 1] - src_y[row]))
                target = (dst_x[col + 1] - dst_x[col], dst_y[row + 1] - dst_y[row])
                result.blit(pg.transform.scale(piece, target), (dst_x[col], dst_y[row]))
        _panels[size] = result
    return _panels[size]


def draw_button(surface, rect, text, font):
    from .. import tool
    image = tool.GFX[c.UNIVERSAL_BUTTON].subsurface((0, 0, 111, 26)).copy()
    image.set_colorkey(c.BLACK)
    surface.blit(pg.transform.scale(image, rect.size), rect)
    label = font.render(text, True, c.NAVYBLUE)
    surface.blit(label, label.get_rect(center=rect.center))
