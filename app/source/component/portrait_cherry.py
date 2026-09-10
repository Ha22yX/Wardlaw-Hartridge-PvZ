"""Reference-based double portrait cherry and deterministic game-time effects."""

import math
import random

import pygame as pg

from .. import constants as c


def install_assets(graphics):
    source = graphics['portrait_cherrybomb'].copy()
    background = pg.mask.from_threshold(source, c.BLACK, (9, 9, 9, 255))
    background.to_surface(source, setcolor=c.BLACK, unsetcolor=None)
    source.set_colorkey(c.BLACK)
    source = pg.transform.smoothscale(source.convert_alpha(), (120, 120))
    # Keep the shared stem intact; independently sway the two portrait fruits.
    stem = source.subsurface((0, 0, 120, 42)).copy()
    halves = [source.subsurface((x, 42, 60, 78)).copy() for x in (0, 60)]
    for warning in (False, True):
        frames = []
        for i in range(16):
            phase = i * math.tau / 16
            pose = pg.Surface((140, 144), pg.SRCALPHA)
            pose.blit(stem, (10, 12))
            for side, half in enumerate(halves):
                wave = math.sin(phase + side * math.pi)
                fruit = pg.transform.rotate(half, wave * (4 if warning else 2))
                pose.blit(fruit, fruit.get_rect(midtop=(40 + 60 * side, 54 + round(wave * 2))))
            if warning:
                factor = 1 + .20 * (i / 15) + .025 * math.sin(i * 2)
                enlarged = pg.transform.smoothscale(pose, (round(140 * factor), round(144 * factor)))
                pose.fill((0, 0, 0, 0))
                pose.blit(enlarged, enlarged.get_rect(midbottom=(70, 144)))
                if i % 4 < 2:
                    tint = pg.Surface(pose.get_size(), pg.SRCALPHA)
                    tint.fill((65, 12, 0, 0))
                    pose.blit(tint, (0, 0), special_flags=pg.BLEND_RGBA_ADD)
            frames.append(pose)
        graphics[c.PORTRAITCHERRYBOMB + ('Warning' if warning else '')] = frames
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((230, 189, 124))
    card.blit(pg.transform.smoothscale(source, (94, 94)), (3, 0))
    title = pg.font.Font(c.FONT_PATH, 13).render(c.PLANT_DISPLAY_NAMES[c.PORTRAITCHERRYBOMB], True, (71, 26, 22))
    card.blit(title, title.get_rect(center=(50, 99)))
    pg.draw.rect(card, (101, 44, 27), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_PORTRAITCHERRYBOMB] = card


class PortraitCherryBlast(pg.sprite.Sprite):
    """Visual-only fire, photo confetti, shock rings and fading smoke."""

    DURATION = 1800

    def __init__(self, x, y, born, portrait):
        super().__init__()
        self.name = c.FUME  # excluded from ordinary projectile collisions
        self.born = born
        self.image = pg.Surface((460, 400), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        rng = random.Random(71)
        self.particles = []
        for index in range(20):
            angle = math.tau * index / 20 + rng.uniform(-.1, .1)
            speed = rng.uniform(75, 180)
            tile = portrait.subsurface((20 + index % 5 * 20, 57 + index // 5 * 17, 18, 16)).copy()
            self.particles.append((angle, speed, tile, rng.uniform(-300, 300)))
        self.update({c.CURRENT_TIME: born})

    def update(self, game_info):
        age = max(0, game_info[c.CURRENT_TIME] - self.born)
        if age >= self.DURATION:
            self.kill()
            return
        t = age / 1000
        self.image.fill((0, 0, 0, 0))
        cx, cy = 230, 200
        # Two smoke origins follow the positions of the two cherry faces.
        for i in range(12):
            angle = i * math.tau / 12
            radius = 22 + t * 62
            center = (round(cx + math.cos(angle) * radius), round(cy + math.sin(angle) * radius * .55 - t * 34))
            pg.draw.circle(self.image, (86, 77, 71, round(110 * (1 - age / self.DURATION))), center, round(15 + t * 20))
        if age < 650:
            for ring in range(2):
                radius = round(18 + t * (220 - ring * 45))
                pg.draw.circle(self.image, (255, 219, 85, round(230 * (1 - age / 650))), (cx, cy), radius, 5 - ring * 2)
            for side in (-1, 1):
                for i in range(9):
                    angle = math.tau * i / 9
                    reach = 12 + 80 * math.sin(min(1, t / .65) * math.pi)
                    center = (round(cx + side * 27 + math.cos(angle) * reach), round(cy + math.sin(angle) * reach))
                    r = max(1, round(26 * (1 - age / 650)))
                    pg.draw.circle(self.image, (255, 101 + i * 10, 24, 230), center, r)
                    pg.draw.circle(self.image, (255, 246, 178, 240), center, max(1, r // 2))
        for angle, speed, tile, spin in self.particles:
            px = cx + math.cos(angle) * speed * t
            py = cy + math.sin(angle) * speed * t * .7 + 45 * t * t
            piece = pg.transform.rotate(tile, spin * t)
            piece.set_alpha(round(255 * (1 - age / self.DURATION)))
            self.image.blit(piece, piece.get_rect(center=(round(px), round(py))))
            if age < 900:
                pg.draw.line(self.image, (255, 208, 67, round(220 * (1 - age / 900))),
                             (round(px), round(py)),
                             (round(px - math.cos(angle) * 12), round(py - math.sin(angle) * 12)), 2)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
