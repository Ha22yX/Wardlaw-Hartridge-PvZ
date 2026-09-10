"""Three distinct photo heads, fixed-root animation, and lane-bound peas."""
import math
from pathlib import Path
import pygame as pg
from .. import constants as c
from .face_projectile import targetable

SIZE = (176, 194)
ROOT = (88, 190)
PHASES = ('Idle', 'Charge', 'Shoot', 'Recover')
COLORS = ((146, 243, 73), (90, 224, 216), (255, 211, 92))


def install_assets(graphics):
    path = Path(__file__).resolve().parents[2] / 'resources/generated_sources/portrait_threepeater_sheet.png'
    sheet = pg.image.load(str(path)).convert_alpha()
    bg = pg.mask.from_threshold(sheet, (0, 0, 0), (12, 12, 12, 255))
    bg.connected_component((0, 0)).to_surface(sheet, setcolor=(0, 0, 0, 0), unsetcolor=None)
    pieces = pg.mask.from_surface(sheet).connected_components(10000)
    if len(pieces) != 4:
        raise ValueError('Three-headed plant requires four isolated full-plant poses')
    rects = [p.get_bounding_rects()[0] for p in pieces]
    rects.sort(key=lambda r: (r.centery > sheet.get_height() // 2, r.centerx))
    scale = min(154 / max(r.w for r in rects), 176 / max(r.h for r in rects))
    poses = []
    for index, rect in enumerate(rects):
        sprite = pg.transform.smoothscale(sheet.subsurface(rect), (round(rect.w * scale), round(rect.h * scale)))
        canvas = pg.Surface(SIZE, pg.SRCALPHA)
        dest = sprite.get_rect(midbottom=ROOT)
        canvas.blit(sprite, dest)
        poses.append(canvas)
        if index == 2:
            # Mouth landmarks on the SHOOT silhouette, ordered upper/middle/lower.
            graphics[c.PORTRAITTHREEPEATER + 'Mouths'] = [
                (round(dest.x + u * dest.w), round(dest.y + v * dest.h))
                for u, v in ((.69, .275), (.93, .52), (.945, .83))]
    graphics[c.PORTRAITTHREEPEATER + 'Poses'] = poses
    for index, phase in enumerate(PHASES):
        frames = []
        for i in range(24):
            t = i / 23
            wave = math.sin(t * math.tau)
            # Distinct expressions are switched directly: no double-faced fades.
            pose = poses[0] if phase == 'Recover' and t > .8 else poses[index]
            body = pg.transform.rotozoom(pose, wave * .65, 1 + .008 * wave)
            frame = pg.Surface(SIZE, pg.SRCALPHA)
            offset = round(-3 * math.sin(t * math.pi)) if phase == 'Recover' else 0
            frame.blit(body, body.get_rect(midbottom=(ROOT[0] + offset, ROOT[1])))
            frames.append(frame)
        graphics[c.PORTRAITTHREEPEATER + phase] = frames
    graphics[c.PORTRAITTHREEPEATER] = graphics[c.PORTRAITTHREEPEATER + 'Idle']
    card = pg.Surface((100, 140), pg.SRCALPHA)
    card.fill((212, 227, 169))
    icon = pg.transform.rotozoom(poses[0], 0, .51)
    card.blit(icon, icon.get_rect(midbottom=(50, 100)))
    label = pg.font.Font(c.FONT_PATH, 13).render(c.PLANT_DISPLAY_NAMES[c.PORTRAITTHREEPEATER], True, (43, 76, 29))
    card.blit(label, label.get_rect(center=(50, 108)))
    pg.draw.rect(card, (64, 106, 37), card.get_rect(), 4, border_radius=6)
    graphics[c.CARD_PORTRAITTHREEPEATER] = card


class MuzzlePuff(pg.sprite.Sprite):
    def __init__(self, point, color, born):
        super().__init__()
        self.name = c.FUME
        self.point, self.color, self.born = point, color, born
        self.image = pg.Surface((48, 40), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=point)
        self.update({c.CURRENT_TIME: born})

    def update(self, info):
        t = max(0, (info[c.CURRENT_TIME] - self.born) / 220)
        if t >= 1:
            self.kill()
            return
        self.image.fill((0, 0, 0, 0))
        opacity = round(200 * (1 - t))
        pg.draw.ellipse(self.image, (*self.color, opacity), (20 + t * 8, 12 - t * 5, 5 + t * 8, 16 + t * 10), 2)
        for i in range(5):
            angle = (i - 2) * .38
            x = 24 + math.cos(angle) * (5 + t * 17)
            y = 20 + math.sin(angle) * (4 + t * 17)
            pg.draw.circle(self.image, (240, 255, 200, opacity), (x, y), 1 + i % 2)


class PortraitPea(pg.sprite.Sprite):
    """Curves from its own mouth into ONE lane; no homing or multi-hit."""
    SPEED = 300
    LIFETIME = 6000
    MERGE_MS = 350

    def __init__(self, start, dest_y, lane, head, born, scene):
        super().__init__()
        self.name = c.PORTRAIT_PEA
        self.state = c.FLY
        self.damage = c.PORTRAITTHREEPEATER_DAMAGE
        self.lane, self.head, self.scene = lane, head, scene
        self.start, self.dest_y, self.born = start, dest_y, born
        self.previous_age = self.age = 0
        self.color = COLORS[head]
        self.image = pg.Surface((40, 28), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=start)
        self.position = start
        self.explode_at = None
        self.expired = False
        self.update({c.CURRENT_TIME: born})

    def point_at(self, age):
        u = min(1, max(0, age / self.MERGE_MS))
        ease = u * u * (3 - 2 * u)
        return (self.start[0] + self.SPEED * age / 1000,
                self.start[1] + (self.dest_y - self.start[1]) * ease)

    def update(self, info):
        now = info[c.CURRENT_TIME]
        self.image.fill((0, 0, 0, 0))
        if self.state == c.EXPLODE:
            t = max(0, (now - self.explode_at) / 240)
            if t >= 1:
                self.kill()
                return
            opacity = round(240 * (1 - t))
            pg.draw.circle(self.image, (*self.color, opacity), (25, 14), round(4 + 8 * t), 2)
            for i in range(7):
                angle = i * math.tau / 7
                point = (25 + math.cos(angle) * 12 * t, 14 + math.sin(angle) * 12 * t)
                pg.draw.circle(self.image, (*self.color, opacity), point, 2)
            return
        self.previous_age, self.age = self.age, min(self.LIFETIME, max(0, now - self.born))
        self.position = self.point_at(self.age)
        self.rect = self.image.get_rect(topleft=(round(self.position[0]) - 25, round(self.position[1]) - 14))
        self.expired = now - self.born >= self.LIFETIME or self.position[0] > c.SCREEN_WIDTH + 30
        for i in range(4, 0, -1):
            pg.draw.circle(self.image, (*self.color, 35 + (4 - i) * 23), (25 - i * 5, 14), 2 + (4 - i))
        pg.draw.circle(self.image, (40, 96, 37), (25, 14), 7)
        pg.draw.circle(self.image, self.color, (25, 14), 6)
        pg.draw.circle(self.image, (244, 255, 211), (23, 12), 2)

    def check_hit(self, enemies):
        if self.state != c.FLY:
            return
        targets = sorted((z for z in enemies if targetable(z) and not getattr(z, 'is_hypno', False)),
                         key=lambda z: z.rect.centerx)
        # Sample the true curved path, not just the end point, to prevent tunneling
        # at low frame rates. Cosmetic tails never increase the collision radius.
        steps = max(1, math.ceil((self.age - self.previous_age) / 12))
        for i in range(steps + 1):
            age = self.previous_age + (self.age - self.previous_age) * i / steps
            x, y = self.point_at(age)
            for zombie in targets:
                if not zombie.rect.inflate(12, 12).collidepoint(x, y):
                    continue
                hit = False
                for dx, dy in ((0, 0), (-5, 0), (5, 0), (0, -5), (0, 5)):
                    px, py = round(x - zombie.rect.x + dx), round(y - zombie.rect.y + dy)
                    if 0 <= px < zombie.mask.get_size()[0] and 0 <= py < zombie.mask.get_size()[1]:
                        hit = hit or zombie.mask.get_at((px, py))
                if not hit:
                    continue
                zombie.setDamage(self.damage, effect=None, damage_type=c.ZOMBIE_DEAFULT_DAMAGE)
                self.state = c.EXPLODE
                self.position = (x, y)
                self.rect.topleft = (round(x) - 25, round(y) - 14)
                self.explode_at = self.scene.current_time
                self.scene.impact_audio.play('pea', x, self.scene.game_info[c.SOUND_VOLUME])
                self.update({c.CURRENT_TIME: self.explode_at})
                return
        if self.expired:
            self.kill()
