"""Web-only I/O adapter: touch, local saves, lifecycle and accessible controls.

Never changes plant/enemy stats, collision code, level maps or reward rules.
"""
import json
import math
import os
import sys
import pygame as pg

SAVE_KEY = "pypvz.portrait.save.v1"


def sanitize_save(data, c):
    if not isinstance(data, dict):
        raise ValueError("存档必须是 JSON 对象")
    result = c.INIT_USERDATA.copy()
    for key, default in result.items():
        value = data.get(key, default)
        if isinstance(default, bool):
            result[key] = value if isinstance(value, bool) else default
        elif isinstance(default, (int, float)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                continue
            result[key] = int(value) if isinstance(default, int) and key not in (c.GAME_RATE, c.SOUND_VOLUME) else value
        elif isinstance(value, type(default)):
            result[key] = value
    result[c.LEVEL_NUM] = max(1, min(5, result[c.LEVEL_NUM]))
    result[c.LITTLEGAME_NUM] = max(1, min(5, result[c.LITTLEGAME_NUM]))
    result[c.SOUND_VOLUME] = max(0, min(1, result[c.SOUND_VOLUME]))
    result[c.GAME_RATE] = max(.5, min(2, result[c.GAME_RATE]))
    result[c.CUSTOM_ENDLESS_BEST] = max(0, result[c.CUSTOM_ENDLESS_BEST])
    result[c.CUSTOM_CAMPAIGN_VERSION] = 1
    return result


class BrowserPlatform:
    def __init__(self):
        self.window = None
        if sys.platform == "emscripten":
            from platform import window
            self.window = window
        self.game = None
        self.c = None
        self.game_ms = 0
        self.visible = True
        self.ended = False
        self.last_publish = -1000
        self.last_state = None
        self.last_save = None

    def notify(self, kind, payload):
        if self.window is not None:
            # The WASM bridge may reinterpret UTF-8 as Latin-1: transfer ASCII
            # JSON escapes and let the browser decode Chinese exactly once.
            self.window.pvzReceive(kind, json.dumps(payload, ensure_ascii=True))

    def status(self, text):
        self.notify("status", text)

    def failure(self, detail):
        self.notify("failure", detail)

    def prepare_save(self, c):
        self.c = c
        os.makedirs(os.path.dirname(c.USERDATA_PATH), exist_ok=True)
        raw = self.window.pvzLoadSave() if self.window is not None else None
        try:
            data = sanitize_save(json.loads(str(raw)), c) if raw else c.INIT_USERDATA.copy()
        except (ValueError, TypeError):
            # Retain the broken browser record for user export/recovery.
            self.notify("warning", "浏览器存档无法读取，已保留备份并使用初始进度。")
            data = c.INIT_USERDATA.copy()
        with open(c.USERDATA_PATH, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False)

    def install(self, tool, c):
        bridge = self
        native_save = tool.State.saveUserData

        def save_web(state):
            native_save(state)
            bridge.save(state.game_info)
        tool.State.saveUserData = save_web

    def bind(self, game, c):
        self.game, self.c = game, c

    def save(self, data):
        payload = {key: data.get(key, default) for key, default in self.c.INIT_USERDATA.items()}
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if encoded != self.last_save:
            self.notify("save", payload)
            self.last_save = encoded

    def ready(self):
        self.notify("ready", True)
        self.publish(force=True)

    def click(self, point, button=1):
        x, y = (max(0, min(limit, int(value))) for value, limit in zip(point, (799, 599)))
        pg.mouse.set_pos((x, y))
        pg.event.post(pg.event.Event(pg.MOUSEBUTTONDOWN, button=button, pos=(x, y)))
        pg.event.post(pg.event.Event(pg.MOUSEBUTTONUP, button=button, pos=(x, y)))

    def receive(self):
        if self.window is None:
            return
        self.visible = bool(self.window.pvzVisible())
        raw = str(self.window.pvzDrain())
        for item in json.loads(raw):
            try:
                self.action(item)
            except (ValueError, KeyError, TypeError, AttributeError) as error:
                self.notify("warning", str(error))

    def action(self, item):
        if not self.game:
            return
        c, state = self.c, self.game.state
        action = item.get("action")
        if action == "pointer":
            self.click(item["point"], item.get("button", 1))
        elif action == "cancel":
            self.click((400, 300), 3)
        elif action == "card":
            index = int(item["index"])
            cards = getattr(getattr(state, "menubar", None), "card_list", [])
            if not 0 <= index < len(cards):
                return
            self.click(cards[index].rect.center)
        elif action == "key":
            mapping = {"9": pg.K_9, "0": pg.K_0, "-": pg.K_MINUS,
                       "+": pg.K_PLUS, "=": pg.K_EQUALS}
            if item["key"] in mapping:
                pg.event.post(pg.event.Event(pg.KEYDOWN, key=mapping[item["key"]], mod=0))
        elif action in ("menu", "speed", "shovel", "resume", "guide", "skip", "reward"):
            if action == "guide":
                guide = getattr(state, "first_lawn_guide", None)
                if guide and guide.active:
                    self.click(guide.next_rect.center if guide.step in (0, 6)
                               else guide.target_rect(state).center)
            elif action == "skip":
                guide = getattr(state, "first_lawn_guide", None)
                if guide and guide.active:
                    guide.finish(state)
            elif action == "reward":
                reward = getattr(state, "card_rewards", None)
                if reward:
                    self.click(reward.button.center)
            else:
                attribute = {"menu": "little_menu_rect", "speed": "speed_button_rect",
                             "shovel": "shovel_box_rect", "resume": "return_button_rect"}[action]
                rect = getattr(state, attribute, None)
                if rect:
                    self.click(rect.center)
        elif action == "mute":
            cvalue = 0 if self.game.game_info[c.SOUND_VOLUME] else 0.5
            self.game.game_info[c.SOUND_VOLUME] = cvalue
            pg.mixer.music.set_volume(cvalue)
            for sound in c.SOUNDS:
                sound.set_volume(cvalue)
            self.save(self.game.game_info)
        elif action == "export":
            self.save(self.game.game_info)
            self.notify("export", json.loads(self.last_save))
        elif action == "import":
            data = sanitize_save(item["save"], c)
            self.game.game_info.update(data)
            self.save(self.game.game_info)
            self.to_menu()
        elif action == "home":
            self.to_menu()

    def to_menu(self):
        self.ended = False
        self.game.done = False
        self.game.pending_clicks.clear()
        self.game.state.cleanup()
        self.game.state_name = self.c.MAIN_MENU
        self.game.state = self.game.state_dict[self.c.MAIN_MENU]
        self.game.state.startup(self.game.current_time, self.game.game_info)

    def publish(self, force=False):
        if not self.game or (not force and self.game_ms - self.last_publish < 100):
            return
        self.last_publish = self.game_ms
        c, state = self.c, self.game.state
        from source.component.custom_campaign import DESCRIPTIONS
        cards = getattr(getattr(state, "menubar", None), "card_list", [])
        guide = getattr(state, "first_lawn_guide", None)
        payload = {"state": self.game.state_name, "ended": self.ended,
                   "level": self.game.game_info[c.LEVEL_NUM],
                   "mode": self.game.game_info.get(c.GAME_MODE),
                   "title": pg.display.get_caption()[0],
                   "sun": getattr(getattr(state, "menubar", None), "sun_value", 0),
                   "speed": getattr(state, "speed_multiplier", 1),
                   "paused": getattr(state, "show_game_menu", False),
                   "muted": self.game.game_info[c.SOUND_VOLUME] == 0,
                   "canSpeed": bool(getattr(state, "canToggleSpeed", lambda: False)()),
                   "selected": getattr(state, "plant_name", None),
                   "cards": [], "guide": None, "reward": None}
        for index, card in enumerate(cards):
            conveyor = not hasattr(card, 'info')
            name = card.plant_name if conveyor else card.info[0]
            desc = DESCRIPTIONS.get(name, (name, ()))
            payload["cards"].append({
                "index": index, "id": name, "name": desc[0],
                "description": list(desc[1]), "cost": 0 if conveyor else card.sun_cost,
                "cooldown": 0 if conveyor else card.frozen_time / 1000,
                "remaining": 0 if conveyor else max(0, (card.frozen_timer + card.frozen_time - state.current_time) / 1000),
                "available": True if conveyor else card.canClick(state.menubar.sun_value, state.current_time),
                "selected": getattr(card, "clicked", False),
                "image": "cards/" + (card.card_name if conveyor else card.info[1]) + ".png"})
        if guide and guide.active:
            payload["guide"] = {"title": guide.steps[guide.step][0],
                                "text": guide.steps[guide.step][1],
                                "step": guide.step + 1, "total": len(guide.steps),
                                "interactive": len(guide.steps) > 1 and guide.step not in (0, 6)}
        reward = getattr(state, "card_rewards", None)
        if reward:
            payload["reward"] = {"stage": reward.stage,
                                 "names": [c.PLANT_DISPLAY_NAMES[n] for n in reward.names]}
        if payload != self.last_state:
            self.notify("state", payload)
            self.last_state = payload
