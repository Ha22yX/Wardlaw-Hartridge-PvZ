"""Regress wall-clock jumps, card refreshes, and endless opening countdown."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import pygame as pg
pg.init()
from source import constants as c

with tempfile.TemporaryDirectory(prefix='campaign-clock-test-') as tmp:
    c.USERDATA_PATH = str(Path(tmp) / 'save.json')
    c.USERLOG_PATH = str(Path(tmp) / 'log.txt')
    from web_platform import BrowserPlatform
    bridge = BrowserPlatform()
    bridge.prepare_save(c)
    from source.runtime_check import load_game_modules
    c, tool, level, *_ = load_game_modules()
    from source.component.custom_campaign import PREPARATION_MS, REST_MS
    game = tool.Control()
    assert PREPARATION_MS == (18000, 24000, 30000, 32000, 20000)
    assert REST_MS[-1] == 8000

    # Test both directions, main keyboard and numpad, with SDL far ahead.
    for start, key, target in ((4, pg.K_EQUALS, 5), (5, pg.K_MINUS, 4),
                               (4, pg.K_PLUS, 5), (4, pg.K_KP_PLUS, 5),
                               (5, pg.K_KP_MINUS, 4)):
        scene = level.Level()
        game.game_info.update({c.GAME_MODE: c.MODE_ADVENTURE, c.LEVEL_NUM: start})
        scene.startup(1000, game.game_info)
        # Local game time can lag the control clock after a guide/pause.
        scene.current_time = 500
        with patch.object(pg.time, 'get_ticks', return_value=180000):
            scene.handle_key(pg.event.Event(pg.KEYDOWN, key=key, mod=0))
        assert scene.game_info[c.LEVEL_NUM] == target
        assert scene.current_time == 1000
        assert scene.campaign.next_wave == 1000 + PREPARATION_MS[target - 1]

        # An arbitrarily long introduction must not spend preparation time.
        scene.update(game.screen, 61000, None, [False, False])
        assert scene.current_time == 1000
        scene.first_lawn_guide.finish(scene)
        scene.update(game.screen, 61000, None, [False, False])
        scene.menubar.sun_value = 9999
        scene.update(game.screen, 61250, None, [False, False])
        card = scene.menubar.card_list[0]
        ready_image = pg.image.tobytes(card.image, 'RGBA')
        scene.click_result = (card.info[0], card)
        scene.setupMouseImage(*scene.click_result)
        scene.addPlant(scene.map.getMapGridPos(2, 2))
        assert not scene.drag_plant and sum(map(len, scene.plant_groups)) == 1
        scene.update(game.screen, 61500, None, [False, False])
        assert not card.canClick(9999, scene.current_time)
        assert pg.image.tobytes(card.image, 'RGBA') != ready_image
        assert card.refresh_timer <= scene.current_time

        deadline = scene.campaign.next_wave
        scene.campaign.update(scene, deadline - 1)
        assert scene.campaign.wave == 0
        scene.campaign.update(scene, deadline)
        assert scene.campaign.wave == 1
        assert sum(map(len, scene.zombie_groups)) == 1
    print('PASS +/- jump clock, first planted card cooldown rendering, guide freeze, exact 20-second endless start')
pg.quit()
