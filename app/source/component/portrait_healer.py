"""Curly-haired healing flower assets and purely cosmetic recovery effects."""
import math
from pathlib import Path
import pygame as pg
from .. import constants as c
from .health_bar import draw_health_bar

SIZE = (144, 160)
ROOT = (72, 156)
PHASES = ('Idle', 'Charge', 'Release', 'Recover')


def install_assets(graphics):
    path = Path(__file__).resolve().parents[2] / 'resources/generated_sources/portrait_healer_expressions_v2.png'
    sheet = pg.image.load(str(path)).convert_alpha()
    bg = pg.mask.from_threshold(sheet, (0, 0, 0), (12, 12, 12, 255))
    bg.connected_component((0, 0)).to_surface(sheet, setcolor=(0, 0, 0, 0), unsetcolor=None)
    pieces = pg.mask.from_surface(sheet).connected_components(10000)
    if len(pieces) != 4:
        raise ValueError('Healing plant atlas requires four isolated full character poses')
    rects = [part.get_bounding_rects()[0] for part in pieces]
    rects.sort(key=lambda r: (r.centery > sheet.get_height() // 2, r.centerx))
    scale = min(130 / max(r.w for r in rects), 144 / max(r.h for r in rects))
    poses = []
    for rect in rects:
        sprite = pg.transform.smoothscale(sheet.subsurface(rect),
                                        (round(rect.w * scale), round(rect.h * scale)))
        canvas = pg.Surface(SIZE, pg.SRCALPHA)
        canvas.blit(sprite, sprite.get_rect(midbottom=ROOT))
        poses.append(canvas)
    graphics[c.PORTRAITHEALER + 'Poses'] = poses
    for index, phase in enumerate(PHASES):
        frames = []
        for i in range(24):
            t = i / 23
            wave = math.sin(t * math.tau)
            pose = poses[index]
            # Each phase starts with its actual expression, especially the heal
            # release. Cross-fading photographs produces ghost mouths/eyes.
            if index == 3 and t > .75:
                pose = poses[0]
            zoom = 1 + (.012 * wave if index == 0 else .016 * math.sin(t * math.pi))
            frame = pg.Surface(SIZE, pg.SRCALPHA)
            sprite = pg.transform.rotozoom(pose, wave * (.65 if index == 0 else 1.1), zoom)
            frame.blit(sprite, sprite.get_rect(midbottom=ROOT))
            if index in (1, 2):
                glow = pg.Surface(SIZE, pg.SRCALPHA)
                pg.draw.circle(glow, (113, 255, 166, round(40 + 50 * math.sin(t * math.pi))),
                               (72, 108), 12 + round(t * 6), 2)
                frame.blit(glow, (0, 0))
            frames.append(frame)
        graphics[c.PORTRAITHEALER + phase] = frames
    graphics[c.PORTRAITHEALER] = graphics[c.PORTRAITHEALER + 'Idle']
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((209, 236, 194))
    icon = pg.transform.rotozoom(poses[0], 0, .59)
    card.blit(icon, icon.get_rect(midbottom=(50, 98)))
    title = pg.font.Font(c.FONT_PATH, 14).render(c.PLANT_DISPLAY_NAMES[c.PORTRAITHEALER], True, (33, 78, 54))
    card.blit(title, title.get_rect(center=(50, 107)))
    pg.draw.rect(card, (69, 118, 64), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_PORTRAITHEALER] = card


class HealingBar(pg.sprite.Sprite):
    DURATION = 1500
    FILL_MS = 550

    def __init__(self, target, before, now):
        super().__init__()
        self.target, self.before, self.born = target, before, now
        self.after = target.health
        self.image = pg.Surface((64, 6), pg.SRCALPHA)
        self.rect = self.image.get_rect()
        self.update({c.CURRENT_TIME: now})

    def displayed_health(self, now):
        t = max(0, min(1, (now - self.born) / self.FILL_MS))
        t = t * t * (3 - 2 * t)
        return min(self.target.health, self.before + (self.after - self.before) * t)

    def update(self, info):
        now = info[c.CURRENT_TIME]
        age = max(0, now - self.born)
        if age >= self.DURATION or not self.target.alive() or self.target.health <= 0:
            self.kill()
            return
        self.rect.midtop = (self.target.rect.centerx, self.target.rect.top + 3)
        self.image.fill((0, 0, 0, 0))
        # The nut animates its existing embedded bar, never a second overlay.
        if self.target.name != c.PORTRAITTALLNUT:
            draw_health_bar(self.image, self.displayed_health(now),
                            self.target.max_health, (0, 0))
        self.image.set_alpha(round(255 * min(1, (self.DURATION - age) / 350)))


class HealingWave(pg.sprite.Sprite):
    DURATION = 1300
    ground_effect = True

    def __init__(self, scene, cell, recipients, now):
        super().__init__()
        self.born = now
        self.tiles = []
        col, row = cell
        h = scene.map.grid_height_size
        for y in range(max(0, row - 1), min(scene.map.height, row + 2)):
            for x in range(max(0, col - 1), min(scene.map.width, col + 2)):
                px, py = scene.map.getMapGridPos(x, y)
                self.tiles.append(pg.Rect(px - 40, py - h * 3 // 5, 80, h))
        from .plant_layout import ROOT_OFFSET
        cx, cy = scene.map.getMapGridPos(col, row)
        self.center = (cx, cy + ROOT_OFFSET)
        self.recipients = recipients  # Snapshots: removed plants aren't retained as objects.
        self.bounds = self.tiles[0].unionall(self.tiles)
        self.glow = pg.Surface((96, 40), pg.SRCALPHA)
        for inset in range(18):
            pg.draw.ellipse(self.glow, (100, 244, 153, 2 + inset * 2),
                            (inset * 2, inset, 96 - inset * 4, 40 - inset * 2))
        self.image = pg.Surface(c.SCREEN_SIZE, pg.SRCALPHA)
        self.rect = self.image.get_rect()
        self.update({c.CURRENT_TIME: now})

    def update(self, info):
        age = max(0, info[c.CURRENT_TIME] - self.born)
        if age >= self.DURATION:
            self.kill()
            return
        t = age / self.DURATION
        self.image.fill((0, 0, 0, 0))
        fade = math.sin(math.pi * t) ** .7
        self.image.set_clip(self.bounds)
        cx, cy = self.center[0], self.center[1] - 5
        # A soft ground ripple, not nine UI boxes laid over the characters.
        for delay in (0, .22):
            progress = (t - delay) / (1 - delay)
            if not 0 <= progress <= 1:
                continue
            radius = 12 + 108 * (1 - (1 - progress) ** 2)
            for width, opacity in ((7, 15), (3, 36), (1, 100)):
                pg.draw.ellipse(self.image, (172, 255, 184, round(opacity * fade * (1 - progress))),
                                (cx - radius, cy - radius * .65,
                                 radius * 2, radius * 1.3), width)
        for index, ((x, y), amount) in enumerate(self.recipients):
            glow = self.glow.copy()
            glow.set_alpha(round(220 * fade))
            self.image.blit(glow, glow.get_rect(center=(x, y - 5)))
            # Curved streams arrive at the roots of only plants actually healed.
            for i in range(3):
                u = max(0, min(1, t * 1.8 - i * .12))
                if not 0 < u < 1:
                    continue
                px = cx + (x - cx) * u
                py = cy + (y - 5 - cy) * u - math.sin(u * math.pi) * 24
                pg.draw.circle(self.image, (202, 255, 160, round(200 * fade)), (px, py), 2)
            for i in range(6):
                phase = t * 3 + i * 2.4 + index
                px = x + math.sin(phase) * (23 + i % 3 * 6)
                py = y - 5 - ((t * 38 + i * 9) % 46)
                opacity = round(210 * fade)
                color = (230, 246, 142, opacity) if i % 2 else (134, 255, 176, opacity)
                pg.draw.ellipse(self.image, color, (px - 2, py - 3, 4, 6))
                if i % 3 == 0:
                    pg.draw.line(self.image, (237, 255, 210, opacity), (px - 3, py), (px + 3, py))
        self.image.set_clip(None)
