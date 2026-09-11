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
        assert not card.canClick(9999, scene.current_time)
        assert pg.image.tobytes(card.image, 'RGBA') != ready_image, 'Planting must darken the card in the same frame'
        scene.update(game.screen, 61500, None, [False, False])
        assert not card.canClick(9999, scene.current_time)
        assert pg.image.tobytes(card.image, 'RGBA') != ready_image
        assert card.refresh_timer <= scene.current_time

        # Real selection/planting clicks less than 250 ms apart, at 2x speed.
        scene.speed_multiplier = 2
        other = scene.menubar.card_list[1]
        other_ready = pg.image.tobytes(other.image, 'RGBA')
        scene.update(game.screen, 61520, other.rect.center, [True, False])
        assert scene.drag_plant
        scene.update(game.screen, 61540, scene.map.getMapGridPos(3, 2), [True, False])
        assert not scene.drag_plant
        assert not other.canClick(9999, scene.current_time)
        assert pg.image.tobytes(other.image, 'RGBA') != other_ready
        scene.handle_key(pg.event.Event(pg.KEYDOWN, key=pg.K_0, mod=0))
        assert other.canClick(9999, scene.current_time)
        assert pg.image.tobytes(other.image, 'RGBA') == other_ready

        # Every card uses the same visual/interaction boundary, even when a
        # stale refresh timestamp or a frozen tutorial clock is present.
        for seed in scene.menubar.card_list:
            seed.clicked = False
            seed.setFrozenTime(1000)
            cooling = pg.image.tobytes(seed.image, 'RGBA')
            assert not seed.canClick(9999, 1000)
            seed.refresh_timer = 999999
            seed.update(9999, 1000)
            assert seed.refresh_timer == 1000
            assert pg.image.tobytes(seed.image, 'RGBA') == cooling
            expiry = 1000 + seed.frozen_time
            seed.update(9999, expiry)
            assert seed.canClick(9999, expiry)
            assert pg.image.tobytes(seed.image, 'RGBA') != cooling
            assert seed.orig_image.get_alpha() == 255

        deadline = scene.campaign.next_wave
        scene.campaign.update(scene, deadline - 1)
        assert scene.campaign.wave == 0
        scene.campaign.update(scene, deadline)
        assert scene.campaign.wave == 1
        assert sum(map(len, scene.zombie_groups)) == 1
    # Drain a burst exactly like SDL's keyboard event loop, including presses
    # beyond the first-stage boundary. Boundary presses must not restart it.
    scene = level.Level()
    game.game_info.update({c.GAME_MODE: c.MODE_ADVENTURE, c.LEVEL_NUM: 5})
    scene.startup(1000, game.game_info)
    game.state = scene
    pg.event.clear()
    for _ in range(104):
        pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_MINUS, mod=0))
    game.event_loop()
    scene.update(game.screen, 1000, None, [False, False])
    assert scene.game_info[c.LEVEL_NUM] == 1
    assert len(scene.menubar.card_list) == 2
    guide, campaign, cards = scene.first_lawn_guide, scene.campaign, scene.menubar
    assert guide.active and campaign.wave == 0
    for _ in range(100):
        pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_MINUS, mod=0))
    game.event_loop()
    assert scene.first_lawn_guide is guide and scene.campaign is campaign
    assert scene.menubar is cards and scene.game_info[c.LEVEL_NUM] == 1
    scene.handle_key(pg.event.Event(pg.KEYDOWN, key=pg.K_EQUALS, mod=0))
    assert scene.game_info[c.LEVEL_NUM] == 2
    assert len(scene.menubar.card_list) == 4
    print('PASS +/- clock, cooldowns, 20-second endless start, 204 rapid minus events to stage 1, stable boundary and return to stage 2')
pg.quit()
