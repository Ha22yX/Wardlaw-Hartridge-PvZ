"""One visual coordinate system; grid ownership and combat geometry stay intact."""
import pygame as pg
from .. import constants as c

CUSTOM_NAMES = frozenset((c.GRINDEVOURER, c.GASSUNFLOWER, c.PORTRAITTALLNUT,
    c.PORTRAITCHERRYBOMB, c.HEADPHONEBOXER, c.PORTRAITPOTATOMINE,
    c.PORTRAITSQUASH, c.PORTRAITHEALER, c.PORTRAITCHOMPER, c.PORTRAITTHREEPEATER))
# Grid roots already sit 60% down each tile. Keep the leaves inside the lawn,
# not against its lower edge. Enlargement remains anchored at the same root.
ROOT_OFFSET = 8
MAX_IDLE_HEIGHT = 80
CHARACTER_SCALE = 1.15
_profiles = {}


def install_layout(graphics):
    _profiles.clear()
    for name in CUSTOM_NAMES:
        frames = graphics[name]
        bounds = frames[0].get_bounding_rect()
        for frame in frames[1:]:
            bounds.union_ip(frame.get_bounding_rect())
        # Use one fixed scale per character, not a different scale per pose.
        # Broad multi-head plants retain a little more room horizontally.
        width = 98 if name in (c.PORTRAITTHREEPEATER, c.PORTRAITCHERRYBOMB) else 84
        scale = min(.78, MAX_IDLE_HEIGHT / max(1, bounds.h), width / max(1, bounds.w)) * CHARACTER_SCALE
        _profiles[name] = (scale, frames[0].get_height() - bounds.bottom)


def scale_for(name):
    return _profiles.get(name, (1, 0))[0]


def visual_rect(name, image, rect):
    if name not in _profiles:
        return rect.copy()
    scale, padding = _profiles[name]
    size = (max(1, round(image.get_width() * scale)), max(1, round(image.get_height() * scale)))
    result = pg.Rect((0, 0), size)
    result.midbottom = (rect.centerx, rect.bottom + ROOT_OFFSET + round(padding * scale))
    return result


def point(plant, world_point):
    """Map a mouth, rear, or other source-sprite landmark to the visible sprite."""
    if plant.name not in _profiles:
        return world_point
    rect = visual_rect(plant.name, plant.image, plant.rect)
    return (round(rect.x + (world_point[0] - plant.rect.x) * rect.w / plant.image.get_width()),
            round(rect.y + (world_point[1] - plant.rect.y) * rect.h / plant.image.get_height()))


def root(plant):
    x, y = plant.getPosition()
    return (x, y + ROOT_OFFSET) if plant.name in _profiles else (x, y)


def sprite(plant):
    return image_and_rect(plant.name, plant.image, plant.rect)


def image_and_rect(name, image, rect):
    dest = visual_rect(name, image, rect)
    if name not in _profiles:
        return image, dest
    return pg.transform.smoothscale(image, dest.size), dest


def draw(plant, surface):
    image, rect = sprite(plant)
    surface.blit(image, rect)


def draw_projectile(projectile, surface):
    if projectile.name == c.GRIN_SEED:
        image = pg.transform.rotozoom(projectile.image, 0, .72)
        surface.blit(image, image.get_rect(center=projectile.rect.center))
    else:
        surface.blit(projectile.image, projectile.rect)


def draw_heal_effect(effect, surface):
    target = getattr(effect, 'target', None)
    if target is None or target.name not in _profiles:
        surface.blit(effect.image, effect.rect)
        return
    scale = scale_for(target.name)
    image = pg.transform.smoothscale(effect.image,
        (max(1, round(effect.image.get_width() * scale)), max(1, round(effect.image.get_height() * scale))))
    rect = image.get_rect(midtop=point(target, effect.rect.midtop))
    surface.blit(image, rect)
