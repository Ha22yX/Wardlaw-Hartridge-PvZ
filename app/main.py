# /// script
# dependencies = ["pygame-ce"]
# ///
"""Browser entry point. All game rules and assets remain in source/resources."""
import asyncio
import json
import os
import sys
import time
import traceback
import pygame as pg


async def main():
    from web_platform import BrowserPlatform
    bridge = BrowserPlatform()
    try:
        bridge.status("正在准备原版游戏素材…")
        os.environ['SDL_MOUSE_FOCUS_CLICKTHROUGH'] = '1'
        pg.mixer.pre_init(44100, -16, 2, 1024)
        pg.init()
        await asyncio.sleep(0)
        from source import constants as c
        c.USERDATA_PATH = "/tmp/pypvz-browser/userdata.json"
        c.USERLOG_PATH = "/tmp/pypvz-browser/run.log"
        bridge.prepare_save(c)
        # Import exactly the original game and all of its asset installers.
        from source.runtime_check import load_game_modules
        c, tool, level, mainmenu, screen = load_game_modules()
        bridge.install(tool, c)

        class BrowserControl(tool.Control):
            def game_clock(self):
                return bridge.game_ms

            def flip_state(self):
                if self.state.next == c.EXIT:
                    self.state.saveUserData()
                    bridge.ended = True
                    return
                super().flip_state()

        game = BrowserControl()
        bridge.bind(game, c)
        states = {
            c.MAIN_MENU: mainmenu.Menu(),
            c.GAME_VICTORY: screen.GameVictoryScreen(),
            c.GAME_LOSE: screen.GameLoseScreen(),
            c.LEVEL: level.Level(),
            c.AWARD_SCREEN: screen.AwardScreen(),
            c.HELP_SCREEN: screen.HelpScreen(),
        }
        game.setup_states(states, c.MAIN_MENU)
        bridge.save(game.game_info)
        bridge.ready()
        last = time.perf_counter()
        accumulator = 0
        while True:
            current = time.perf_counter()
            elapsed = max(0, min(0.1, current - last))
            last = current
            bridge.receive()
            if bridge.visible and not bridge.ended:
                accumulator += elapsed
                # The desktop game is 50 logical frames/sec. Keep that rate,
                # independent of 60/90/120-Hz displays; preserve its 2x substeps.
                step = 1 / game.fps
                while accumulator >= step:
                    accumulator -= step
                    bridge.game_ms += step * 1000
                    game.event_loop()
                    game.update()
                    if bridge.ended:
                        break
                pg.display.update()
            else:
                accumulator = 0
            bridge.publish(force=bridge.ended)
            await asyncio.sleep(0)
    except Exception:
        detail = traceback.format_exc()
        print(detail)
        bridge.failure(detail)


asyncio.run(main())
