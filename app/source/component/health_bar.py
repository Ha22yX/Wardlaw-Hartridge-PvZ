"""The portrait nut's health bar, shared by temporary healing feedback."""
import pygame as pg


def draw_health_bar(image, health, maximum, pos=None, alpha=255):
    bar = pg.Surface((64, 6), pg.SRCALPHA)
    pg.draw.rect(bar, (49, 29, 14), (0, 0, 64, 6), border_radius=2)
    fraction = max(0, min(1, health / maximum))
    color = (109, 213, 75) if fraction > 1 / 3 else (242, 109, 69)
    pg.draw.rect(bar, color, (1, 1, round(62 * fraction), 4))
    bar.set_alpha(alpha)
    image.blit(bar, pos if pos is not None else ((image.get_width() - 64) // 2, 3))
