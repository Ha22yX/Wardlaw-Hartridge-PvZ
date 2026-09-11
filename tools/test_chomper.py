"""Check regenerated chomper animation and its unchanged ten-second digestion."""
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import pygame as pg

pg.init()
from source import constants as c

with tempfile.TemporaryDirectory(prefix='chomper-test-') as temp:
    c.USERDATA_PATH = str(Path(temp) / 'save.json')
    c.USERLOG_PATH = str(Path(temp) / 'log.txt')
    from source.runtime_check import load_game_modules
    c, tool, *_ = load_game_modules()
    from source.component.plant import PortraitChomper
    from source.component.portrait_chomper import SIZE

    poses = tool.GFX[c.PORTRAITCHOMPER + 'Poses']
    assert len(poses) == 8
    assert len({pg.image.tobytes(p, 'RGBA') for p in poses}) == 8
    for phase in ('Idle', 'Attack', 'Chew', 'Swallow'):
        frames = tool.GFX[c.PORTRAITCHOMPER + phase]
        assert len(frames) == 24
        assert len({pg.image.tobytes(f, 'RGBA') for f in frames}) > 1
        for frame in frames:
            assert frame.get_size() == SIZE
            bounds = frame.get_bounding_rect()
            assert bounds.left > 0 and bounds.right < SIZE[0]
            assert bounds.top > 0 and bounds.bottom < SIZE[1]
    scene = SimpleNamespace(current_time=0,
                            map=SimpleNamespace(getMapIndex=lambda x, y: (2, 0)),
                            zombie_groups=[pg.sprite.Group()], head_group=pg.sprite.Group())
    plant = PortraitChomper(300, 400, scene)
    plants = pg.sprite.Group(plant)

    def victim():
        z = pg.sprite.Sprite(scene.zombie_groups[0])
        z.image = pg.Surface((30, 60), pg.SRCALPHA)
        z.image.fill((80, 130, 70))
        z.rect = z.image.get_rect(center=(plant.rect.centerx + 75, plant.rect.centery))
        z.name, z.state, z.health = c.NORMAL_ZOMBIE, c.WALK, 200
        return z

    first, second = victim(), victim()
    plant.update({c.CURRENT_TIME: 0})
    assert plant.phase == 'Attack'
    plant.update({c.CURRENT_TIME: 549})
    assert first.alive() and second.alive()
    plant.update({c.CURRENT_TIME: 550})
    assert plant.eaten_count == 1 and not first.alive() and second.alive()
    assert plant.digest_until == 10550
    plant.update({c.CURRENT_TIME: 1000})
    assert plant.phase == 'Chew'
    plant.update({c.CURRENT_TIME: 10000})
    assert plant.phase == 'Swallow' and second.alive()
    plant.update({c.CURRENT_TIME: 10549})
    assert plant.state == c.DIGEST and second.alive()
    plant.update({c.CURRENT_TIME: 10550})
    assert plant.phase == 'Attack' and plant.eaten_count == 1
    plant.update({c.CURRENT_TIME: 11100})
    assert plant.eaten_count == 2 and not second.alive()
    print('PASS 8 distinct poses, 96 rooted frames, bite, chew, swallow, exact 10-second digestion')
pg.quit()
