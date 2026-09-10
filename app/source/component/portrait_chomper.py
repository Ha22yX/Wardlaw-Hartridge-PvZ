"""Photo-faced chomper poses and a cosmetic, non-damaging gulp snapshot."""
import math
from pathlib import Path
import pygame as pg
from .. import constants as c

SIZE = (160, 170)
ROOT = (80, 166)


def install_assets(graphics):
    path = Path(__file__).resolve().parents[2] / 'resources/generated_sources/portrait_chomper_sheet.png'
    sheet = pg.image.load(str(path)).convert_alpha()
    background = pg.mask.from_threshold(sheet, (0, 0, 0), (12, 12, 12, 255))
    background.connected_component((0, 0)).to_surface(
        sheet, setcolor=(0, 0, 0, 0), unsetcolor=None)
    pieces = pg.mask.from_surface(sheet).connected_components(10000)
    if len(pieces) != 8:
        raise ValueError('Portrait chomper requires eight isolated complete poses')
    rects = [piece.get_bounding_rects()[0] for piece in pieces]
    rects.sort(key=lambda r: (r.centery > sheet.get_height() // 2, r.centerx))
    # Crop actual silhouettes, never split an AI atlas into assumed equal cells.
    scale = min(133 / max(r.width for r in rects), 152 / max(r.height for r in rects))
    poses = []
    for rect in rects:
        pose = pg.transform.smoothscale(sheet.subsurface(rect),
                                       (round(rect.w * scale), round(rect.h * scale)))
        canvas = pg.Surface(SIZE, pg.SRCALPHA)
        canvas.blit(pose, pose.get_rect(midbottom=ROOT))
        poses.append(canvas)
    graphics[c.PORTRAITCHOMPER + 'Poses'] = poses
    # Distinct jaw/cheek poses, with root-anchored breathing between keyframes.
    sequences = {'Idle': [0] * 24,
                 'Attack': [1] * 5 + [2] * 12 + [3] * 7,
                 'Chew': [4] * 6 + [6] * 4 + [5] * 6 + [6] * 4 + [4] * 4,
                 'Swallow': [7] * 16 + [0] * 8}
    for phase, indices in sequences.items():
        frames = []
        for i, index in enumerate(indices):
            t = i / len(indices)
            wave = math.sin(t * math.tau)
            pose = poses[index]
            # No cross-fades between different faces (which create double eyes).
            angle = wave * (.65 if phase == 'Idle' else 1.1)
            zoom = 1 + .01 * wave
            transformed = pg.transform.rotozoom(pose, angle, zoom)
            frame = pg.Surface(SIZE, pg.SRCALPHA)
            dx = round(7 * math.sin(t * math.pi)) if phase == 'Attack' else 0
            frame.blit(transformed, transformed.get_rect(midbottom=(ROOT[0] + dx, ROOT[1])))
            frames.append(frame)
        graphics[c.PORTRAITCHOMPER + phase] = frames
    graphics[c.PORTRAITCHOMPER] = graphics[c.PORTRAITCHOMPER + 'Idle']
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((223, 218, 180))
    icon = pg.transform.rotozoom(poses[0], 0, .57)
    card.blit(icon, icon.get_rect(midbottom=(50, 99)))
    title = pg.font.Font(c.FONT_PATH, 14).render(c.PLANT_DISPLAY_NAMES[c.PORTRAITCHOMPER], True, (77, 40, 91))
    card.blit(title, title.get_rect(center=(50, 107)))
    pg.draw.rect(card, (96, 76, 46), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_PORTRAITCHOMPER] = card


class GulpedZombie(pg.sprite.Sprite):
    """The enemy is already consumed; this copy cannot bite or take damage."""
    DURATION = 240

    def __init__(self, victim, plant, born):
        super().__init__()
        self.name = c.FUME
        self.source = victim.image.copy()
        self.start = victim.rect.center
        self.plant = plant
        self.born = born
        self.image = self.source
        self.rect = self.image.get_rect(center=self.start)
        self.update({c.CURRENT_TIME: born})

    def update(self, info):
        age = max(0, info[c.CURRENT_TIME] - self.born)
        if age >= self.DURATION or not self.plant.alive() or self.plant.health <= 0:
            self.kill()
            return
        t = age / self.DURATION
        from .plant_layout import point as visual_point
        end = visual_point(self.plant, (self.plant.rect.centerx + 25, self.plant.rect.top + 79))
        factor = max(.03, 1 - t)
        self.image = pg.transform.smoothscale(self.source,
            (max(1, round(self.source.get_width() * factor)),
             max(1, round(self.source.get_height() * factor))))
        self.image.set_alpha(round(255 * (1 - t * t)))
        point = (self.start[0] + (end[0] - self.start[0]) * t,
                 self.start[1] + (end[1] - self.start[1]) * t)
        self.rect = self.image.get_rect(center=point)
