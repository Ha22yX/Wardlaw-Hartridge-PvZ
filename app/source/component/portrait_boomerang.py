"""Root-aligned portrait poses and a swept, two-pass piercing projectile."""
import math
from pathlib import Path
import pygame as pg
from .. import constants as c

SIZE = (190, 170)
ROOT = (78, 166)
LEG_MS = 900


def install_assets(graphics):
    folder = Path(__file__).resolve().parents[2] / 'resources/generated_sources'
    sheet = pg.image.load(str(folder / 'portrait_boomerang.png')).convert_alpha()
    bg = pg.mask.from_threshold(sheet, (0, 0, 0), (12, 12, 12, 255))
    bg.connected_component((0, 0)).to_surface(sheet, setcolor=(0, 0, 0, 0), unsetcolor=None)
    pieces = pg.mask.from_surface(sheet).connected_components(10000)
    if len(pieces) != 8:
        raise ValueError('Boomerang atlas requires eight isolated complete poses')
    rects = [p.get_bounding_rects()[0] for p in pieces]
    rects.sort(key=lambda r: (r.centery > sheet.get_height() / 2, r.centerx))
    scale = 150 / max(r.h for r in rects)
    poses = []
    for rect in rects:
        cut = sheet.subsurface(rect)
        # Align the leaf root, not the center of outstretched throwing arms.
        base = cut.subsurface((0, int(rect.h * .8), rect.w, rect.h - int(rect.h * .8)))
        root_x = base.get_bounding_rect().centerx
        pose = pg.transform.smoothscale(cut, (round(rect.w * scale), round(rect.h * scale)))
        frame = pg.Surface(SIZE, pg.SRCALPHA)
        frame.blit(pose, (ROOT[0] - round(root_x * scale), ROOT[1] - pose.get_height()))
        poses.append(frame)
    graphics[c.PORTRAITBOOMERANG + 'Poses'] = poses
    sequences = {'Idle': [0] * 24, 'Charge': [0] * 4 + [1] * 20,
                 'Throw': [2] * 10 + [3] * 14, 'Wait': [4] * 24,
                 'Catch': [5] * 8 + [6] * 8 + [7] * 8}
    for phase, indices in sequences.items():
        frames = []
        for i, index in enumerate(indices):
            wave = math.sin(i / len(indices) * math.tau)
            source = poses[index]
            size = (SIZE[0], SIZE[1] + round(wave * (1 if phase == 'Idle' else 2)))
            art = pg.transform.smoothscale(source, size)
            frame = pg.Surface(SIZE, pg.SRCALPHA)
            frame.blit(art, (0, SIZE[1] - size[1]))
            frames.append(frame)
        graphics[c.PORTRAITBOOMERANG + phase] = frames
    graphics[c.PORTRAITBOOMERANG] = graphics[c.PORTRAITBOOMERANG + 'Idle']
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((223, 218, 180))
    icon = pg.transform.rotozoom(poses[0], 0, .56)
    card.blit(icon, icon.get_rect(midbottom=(56, 100)))
    title = pg.font.Font(c.FONT_PATH, 14).render(c.PLANT_DISPLAY_NAMES[c.PORTRAITBOOMERANG], True, (49, 73, 32))
    card.blit(title, title.get_rect(center=(50, 107)))
    pg.draw.rect(card, (96, 76, 46), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_PORTRAITBOOMERANG] = card
    projectile = pg.image.load(str(folder / 'portrait_boomerang_projectile.png')).convert_alpha()
    projectile = projectile.subsurface(projectile.get_bounding_rect())
    projectile = pg.transform.smoothscale(projectile, (32, 32))
    graphics[c.BOOMERANG] = [pg.transform.rotozoom(projectile, i * 15, 1) for i in range(24)]


class ReturningBoomerang(pg.sprite.Sprite):
    def __init__(self, owner, now, graphics):
        super().__init__()
        self.name = c.BOOMERANG
        self.owner, self.level, self.row = owner, owner.level, owner.row
        self.born = self.last_time = now
        self.origin = owner.rect.centerx
        self.end = self.origin + c.PORTRAITBOOMERANG_RANGE
        self.y = owner.rect.bottom - 40
        self.frames = graphics[c.BOOMERANG]
        self.hit_sets = (set(), set())
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(self.origin, self.y))

    def hit_segment(self, x1, x2, leg, now):
        from .face_projectile import targetable, FaceImpact
        lo, hi = sorted((x1, x2))
        for enemy in self.level.zombie_groups[self.row]:
            if (enemy in self.hit_sets[leg] or not targetable(enemy)
                    or getattr(enemy, 'is_hypno', False)
                    or not self.origin <= enemy.rect.centerx <= self.end):
                continue
            if enemy.rect.right < lo or enemy.rect.left > hi:
                continue
            self.hit_sets[leg].add(enemy)
            enemy.setDamage(c.PORTRAITBOOMERANG_DAMAGE, damage_type=c.ZOMBIE_DEAFULT_DAMAGE)
            self.level.head_group.add(FaceImpact((enemy.rect.centerx, self.y), now))
            self.level.impact_audio.play('pea', enemy.rect.centerx,
                self.level.game_info.get(c.SOUND_VOLUME, 1), now)

    def update(self, info):
        now = info[c.CURRENT_TIME]
        old = max(0, min(2 * LEG_MS, self.last_time - self.born))
        age = max(old, min(2 * LEG_MS, now - self.born))
        # Split a long frame at the turn; collisions cannot skip either leg.
        for leg in (0, 1):
            start, end = max(old, leg * LEG_MS), min(age, (leg + 1) * LEG_MS)
            if end <= start:
                continue
            def x_at(t):
                progress = t / LEG_MS if leg == 0 else 2 - t / LEG_MS
                return self.origin + c.PORTRAITBOOMERANG_RANGE * progress
            self.hit_segment(x_at(start), x_at(end), leg, now)
        self.last_time = now
        if age >= 2 * LEG_MS:
            if self.owner.alive() and self.owner.health > 0:
                self.owner.caught_at = now
            self.kill()
            return
        progress = age / LEG_MS if age <= LEG_MS else 2 - age / LEG_MS
        self.image = self.frames[int(age / 28) % len(self.frames)]
        self.rect = self.image.get_rect(center=(round(self.origin + c.PORTRAITBOOMERANG_RANGE * progress),
            round(self.y + math.sin(progress * math.pi) * (-7 if age < LEG_MS else 7))))
