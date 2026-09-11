"""Headless parity and browser-adapter integration checks, no player-save access."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT.parent / "pypvz"
APP = ROOT / "app"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(APP))


def parity():
    counts = {}
    for folder in ("resources", "source"):
        paths = [p for p in (ORIGINAL / folder).rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
        for path in paths:
            target = APP / path.relative_to(ORIGINAL)
            if path.name == "tool.py" and folder == "source":
                # Exactly two platform seams: a clock hook and CSS-managed display.
                expected = path.read_text().replace(
                    "self.current_time = pg.time.get_ticks() * self.game_info[c.GAME_RATE]",
                    "self.current_time = self.game_clock() * self.game_info[c.GAME_RATE]")
                expected = expected.replace("    # 状态转移\n    def flip_state", "    def game_clock(self):\n        return pg.time.get_ticks()\n\n    # 状态转移\n    def flip_state")
                expected = expected.replace("pg.display.set_mode(c.SCREEN_SIZE, pg.SCALED)   # 设置初始屏幕", "pg.display.set_mode(c.SCREEN_SIZE)   # CSS fits the unchanged 800x600 framebuffer.")
                assert target.read_text() == expected, "Unexpected gameplay changes in tool.py"
            else:
                assert target.read_bytes() == path.read_bytes(), path
        counts[folder] = len(paths)
    print("PASS byte-for-byte resources/rules:", counts)


def integration():
    import pygame as pg
    pg.init()
    from source import constants as c
    from web_platform import BrowserPlatform, sanitize_save
    with tempfile.TemporaryDirectory(prefix="pypvz-web-test-") as temp:
        c.USERDATA_PATH = str(Path(temp) / "save.json")
        c.USERLOG_PATH = str(Path(temp) / "log.txt")
        bridge = BrowserPlatform()
        events = []
        bridge.notify = lambda kind, data: events.append((kind, data))
        bridge.prepare_save(c)
        from source.runtime_check import load_game_modules
        c, tool, level, mainmenu, screen = load_game_modules()
        bridge.install(tool, c)
        class TestControl(tool.Control):
            def game_clock(self):
                return bridge.game_ms
        game = TestControl()
        bridge.bind(game, c)
        game.setup_states({c.MAIN_MENU: mainmenu.Menu(), c.LEVEL: level.Level(),
                           c.GAME_VICTORY: screen.GameVictoryScreen(),
                           c.GAME_LOSE: screen.GameLoseScreen(),
                           c.AWARD_SCREEN: screen.AwardScreen(), c.HELP_SCREEN: screen.HelpScreen()}, c.MAIN_MENU)
        bridge.ready()
        def tick(ms=20):
            bridge.game_ms += ms
            game.event_loop()
            game.update()
            bridge.publish(force=True)
        def start(stage, mode=c.MODE_ADVENTURE):
            game.game_info.update({c.GAME_MODE: mode, c.LEVEL_NUM: stage, c.LITTLEGAME_NUM: stage})
            game.state = game.state_dict[c.LEVEL] = level.Level()
            game.state_name = c.LEVEL
            game.state.startup(bridge.game_ms, game.game_info)
            tick()
            return game.state
        menu = game.state
        tick()
        assert [row[0] for row in menu.cheat_rows] == ['9', '0', '-', '=']
        assert menu.cheat_rect.top >= menu.littleGame_rect.bottom
        assert menu.cheat_rect.bottom < menu.option_button_rect.top
        captures = os.environ.get('PVZ_TEST_CAPTURE_DIR')
        if captures:
            Path(captures).mkdir(parents=True, exist_ok=True)
            pg.image.save(game.screen, str(Path(captures) / 'menu.png'))
        menu.checkHilight(*menu.cheat_rect.center)
        assert menu.cheat_image is menu.cheat_frames[1]
        menu.current_time += 100
        menu.checkHilight(0, 0)
        assert menu.cheat_image is menu.cheat_frames[0]
        bridge.action({'action': 'pointer', 'point': menu.cheat_rect.center})
        tick()
        assert menu.cheat_menu_open and not menu.done
        if captures:
            pg.image.save(game.screen, str(Path(captures) / 'cheats.png'))
        for rect in (menu.adventure_rect, menu.littleGame_rect, menu.option_button_rect):
            bridge.action({'action': 'pointer', 'point': rect.center})
            tick()
            assert menu.cheat_menu_open and not menu.done
            assert not menu.adventure_clicked and not menu.option_button_clicked
        bridge.action({'action': 'pointer', 'point': menu.cheat_close_rect.center})
        tick()
        assert not menu.cheat_menu_open and not menu.done
        bridge.action({'action': 'pointer', 'point': menu.cheat_rect.center})
        tick()
        pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE))
        tick()
        assert not menu.cheat_menu_open
        print('PASS cheat-menu single-click open/close, hover, modal isolation, Escape, four key descriptions')
        for stage, cards in enumerate((2, 4, 6, 10, 10), 1):
            scene = start(stage)
            assert len(bridge.last_state['cards']) == cards
            assert bridge.last_state['guide']
            if stage == 1:
                while scene.first_lawn_guide.active:
                    guide = scene.first_lawn_guide
                    point = guide.next_rect.center if guide.step in (0, 6) else guide.target_rect(scene).center
                    bridge.action({'action': 'pointer', 'point': point})
                    tick(1000)
                assert sum(len(g) for g in scene.plant_groups) == 2
            else:
                bridge.action({'action': 'guide'})
                tick()
                assert not scene.first_lawn_guide.active
            bridge.action({'action': 'speed'})
            tick()
            assert scene.speed_multiplier == 2
            bridge.action({'action': 'speed'})
            tick()
            assert scene.speed_multiplier == 1
        # All original mini-games, including their conveyor-card representation.
        from source.component import menubar
        from source.component.custom_campaign import CardTooltip, DESCRIPTIONS
        # Focused hover is absent under SDL dummy by default. Exercise real
        # moving cards explicitly so tooltip crashes cannot escape this test.
        probe = menubar.MoveCard(100, 6, c.CARD_GASSUNFLOWER, c.GASSUNFLOWER)
        tooltip = CardTooltip()
        tooltip.update([probe], probe.rect.center, 1000)
        tooltip.update([probe], probe.rect.center, 1499)
        assert not tooltip.visible
        tooltip.update([probe], probe.rect.center, 1500)
        assert tooltip.visible
        tooltip.draw(game.screen)
        assert not hasattr(probe, 'info'), 'Keep conveyor identity for browser adapter'
        tooltip.update([], probe.rect.center, 1501)
        assert not tooltip.visible and tooltip.card is None
        for stage in range(1, 6):
            scene = start(stage, c.MODE_LITTLEGAME)
            for _ in range(10):
                tick(1000)
            if isinstance(scene.menubar, menubar.MoveBar):
                scene.menubar.createCard()
                bridge.publish(force=True)
                assert bridge.last_state['cards']
                for card in scene.menubar.card_list:
                    with patch.object(pg.mouse, 'get_focused', return_value=True), \
                         patch.object(pg.mouse, 'get_pos', return_value=card.rect.center), \
                         patch.object(pg.time, 'get_ticks', return_value=1000):
                        scene.updateCardTooltip(game.screen, scene.current_time)
                    with patch.object(pg.mouse, 'get_focused', return_value=True), \
                         patch.object(pg.mouse, 'get_pos', return_value=card.rect.center), \
                         patch.object(pg.time, 'get_ticks', return_value=1500):
                        scene.updateCardTooltip(game.screen, scene.current_time)
                    assert scene.card_tooltip.visible == (card.plant_name in DESCRIPTIONS)
                assert all(card['cost'] == 0 and card['available'] for card in bridge.last_state['cards'])
        # Return from a conveyor game, then enter every saved adventure stage
        # through the actual menu click/transition, reusing the same Level.
        for stage in range(1, 6):
            bridge.action({'action': 'home'})
            game.game_info[c.LEVEL_NUM] = stage
            tick()
            bridge.click(game.state.adventure_rect.center)
            tick()
            tick(3300)
            tick()
            assert game.state_name == c.LEVEL
            assert game.game_info[c.GAME_MODE] == c.MODE_ADVENTURE
            scene = game.state
            assert isinstance(scene.menubar, menubar.MenuBar)
            assert scene.map_data['custom_stage'] == stage
            bridge.action({'action': 'skip'})
            tick()
            card = scene.menubar.card_list[0]
            tooltip = scene.card_tooltip
            tooltip.update(scene.menubar.card_list, card.rect.center, 1000)
            tooltip.update(scene.menubar.card_list, card.rect.center, 1500)
            assert tooltip.visible
            tooltip.draw(game.screen)
        print('PASS moving/static card hover and actual menu entry into all five adventure stages')
        data = sanitize_save({c.GAME_RATE: 1.5, c.SOUND_VOLUME: .75}, c)
        assert data[c.GAME_RATE] == 1.5 and data[c.SOUND_VOLUME] == .75
        bridge.action({'action': 'import', 'save': data})
        assert game.state_name == c.MAIN_MENU
        bridge.action({'action': 'export'})
        assert events[-1][0] == 'export'
        assert events[-1][1][c.SOUND_VOLUME] == .75
        assert all(Path(path).exists() for path in (c.USERDATA_PATH,))
        print("PASS all five campaign scenes, original tutorial planting, single-click speed toggle, all five mini-games, save import/export")
    pg.quit()


if __name__ == '__main__':
    parity()
    integration()
