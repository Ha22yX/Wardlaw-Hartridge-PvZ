"""Check proportional healing, timing, range, full-health clamp and stacking."""
import os
from pathlib import Path
import sys
import tempfile

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import pygame as pg
pg.init()
from source import constants as c

with tempfile.TemporaryDirectory(prefix='pvz-healer-test-') as tmp:
    c.USERDATA_PATH = str(Path(tmp) / 'save.json')
    c.USERLOG_PATH = str(Path(tmp) / 'log.txt')
    from web_platform import BrowserPlatform
    BrowserPlatform().prepare_save(c)
    from source.runtime_check import load_game_modules
    c, tool, level, *_ = load_game_modules()
    from source.component import plant
    game = tool.Control()
    game.game_info.update({c.GAME_MODE: c.MODE_ADVENTURE, c.LEVEL_NUM: 4})
    scene = level.Level()
    scene.startup(0, game.game_info)

    def add(cls, col, row, *args):
        item = cls(*scene.map.getMapGridPos(col, row), *args)
        scene.plant_groups[row].add(item)
        return item

    healer = add(plant.PortraitHealer, 4, 2, scene)
    nut = add(plant.PortraitTallNut, 5, 2)
    diagonal = add(plant.PeaShooter, 3, 1, scene.bullet_groups[1])
    outside = add(plant.PortraitTallNut, 6, 2)
    healer.health = diagonal.health = outside.health = 100
    nut.health = 1000
    healer.update({c.CURRENT_TIME: 1999})
    assert nut.health == 1000
    healer.update({c.CURRENT_TIME: 2000})
    assert nut.health == 1900, '4500 maximum HP must restore 900, with no 150 cap'
    assert healer.health == diagonal.health == 160
    assert outside.health == 100
    assert nut.healing_bar.alive()
    other = add(plant.PortraitHealer, 4, 2, scene)
    other.pulse(2000)
    assert nut.health == 1900, 'overlapping healers cannot stack'
    healer.update({c.CURRENT_TIME: 16999})
    assert nut.health == 1900
    nut.health = 4400
    diagonal.health = 0
    healer.update({c.CURRENT_TIME: 17000})
    assert nut.health == nut.max_health == 4500
    assert healer.health == 220
    assert diagonal.health == 0, 'no revival'
    assert healer.next_heal == 32000
    print('PASS 20% max-HP healing, no flat cap, 3x3/self/diagonal range, 2s/15s timing, no stacking, no overheal/revival')
pg.quit()
