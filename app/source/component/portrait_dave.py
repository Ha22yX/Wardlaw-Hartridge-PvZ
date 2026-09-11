"""First-lawn onboarding: real collection/planting, with the battle clock stopped."""
import math
from pathlib import Path

import pygame as pg

from .. import constants as c
from .plant import Sun
from .pvz_ui import paper_panel, draw_button


CARDS = (c.GRINDEVOURER, c.GASSUNFLOWER)

# The words describe the actual customized mechanics, not the vanilla plants.
STEPS = (
    ('邻居，先别急。', '我是这片草坪的凯夫。锅是头盔，不是晚饭。\n今天先学三件事：收阳光、选植物、守住这条路。'),
    ('先把阳光收起来', '看到发光的头像了吗？那就是这里的阳光。\n单击它，收下 25 阳光。别光盯着他的脸。'),
    (f'选一株{c.PLANT_DISPLAY_NAMES[c.GRINDEVOURER]}', f'点上方亮起的{c.PLANT_DISPLAY_NAMES[c.GRINDEVOURER]}卡片，花费 100 阳光。\n选卡后再点草地；右键可以取消选择。'),
    ('种到亮起的格子', f'把{c.PLANT_DISPLAY_NAMES[c.GRINDEVOURER]}种在黄色框里。\n它会自动发射追踪子弹，不用你手动瞄准。'),
    (f'再选一株{c.PLANT_DISPLAY_NAMES[c.GASSUNFLOWER]}', f'火力有了，还得有收入。\n点上方{c.PLANT_DISPLAY_NAMES[c.GASSUNFLOWER]}卡片，花费 50 阳光。'),
    (f'把{c.PLANT_DISPLAY_NAMES[c.GASSUNFLOWER]}放后面', f'种在{c.PLANT_DISPLAY_NAMES[c.GRINDEVOURER]}左边的亮格里。\n它首次约 6 秒产阳光，之后每 {c.GASSUNFLOWER_SUN_INTERVAL / 1000:g} 秒产一次。'),
    ('行，开工！', f'这关共 4 波，阳光要记得捡，后排保收入。\n胜利后会获得{c.PLANT_DISPLAY_NAMES[c.PORTRAITTALLNUT]}和{c.PLANT_DISPLAY_NAMES[c.PORTRAITCHOMPER]}！'),
)


def load_poses():
    path = Path(__file__).resolve().parents[2] / 'resources' / 'generated_sources' / 'portrait_dave_sheet.png'
    sheet = pg.image.load(str(path)).convert_alpha()
    # Only edge-connected black is background; dark hair and plaid stay intact.
    black = pg.mask.from_threshold(sheet, (0, 0, 0), (10, 10, 10, 255))
    black.connected_component((0, 0)).to_surface(
        sheet, setcolor=(0, 0, 0, 0), unsetcolor=None)
    pieces = pg.mask.from_surface(sheet).connected_components(10000)
    if len(pieces) != 2:
        raise ValueError('Dave atlas must contain two separate character silhouettes')
    rects = sorted((m.get_bounding_rects()[0] for m in pieces), key=lambda r: r.x)
    scale = min(205 / max(r.w for r in rects), 220 / max(r.h for r in rects))
    poses = []
    for rect in rects:
        sprite = pg.transform.smoothscale(sheet.subsurface(rect),
                                        (round(rect.w * scale), round(rect.h * scale)))
        canvas = pg.Surface((220, 230), pg.SRCALPHA)
        canvas.blit(sprite, sprite.get_rect(midbottom=(110, 230)))
        poses.append(canvas)
    return poses


class FirstLawnGuide:
    def __init__(self, scene, now):
        from .dave_audio import DaveVoice
        self.voice = DaveVoice()
        self.steps = STEPS
        self.heading = '第一关教学 · 学完再出怪'
        self.active = True
        self.step = 0
        self.step_started = now
        self.now = now
        self.revealed = False
        self.sun = None
        self.poses = load_poses()
        self.title_font = pg.font.Font(c.FONT_PATH, 23)
        self.font = pg.font.Font(c.FONT_PATH, 18)
        self.small = pg.font.Font(c.FONT_PATH, 15)
        self.next_rect = pg.Rect(606, 548, 158, 33)
        self.skip_rect = pg.Rect(642, 112, 140, 32)
        self.attack_cell = (3, 2)
        self.sun_cell = (2, 2)
        scene.menubar.update(max(1, scene.current_time))

    def card(self, scene, name):
        return next(card for card in scene.menubar.card_list
                    if card.index == c.PLANT_CARD_INDEX[name])

    def target_rect(self, scene):
        if self.step == 1 and self.sun:
            return self.sun.rect.inflate(14, 14)
        if self.step in (2, 4):
            name = c.GRINDEVOURER if self.step == 2 else c.GASSUNFLOWER
            return self.card(scene, name).rect.inflate(8, 8)
        if self.step in (3, 5):
            col, row = self.attack_cell if self.step == 3 else self.sun_cell
            x, y = scene.map.getMapGridPos(col, row)
            return pg.Rect(x - 35, y - 80, 70, 78)
        return None

    def advance(self, scene, now):
        self.step += 1
        self.step_started, self.revealed = now, False
        if self.step == 1:
            self.sun = Sun(395, 255, 395, 255)
            scene.sun_group.add(self.sun)

    def finish(self, scene):
        self.active = False
        self.voice.stop()
        if self.sun:
            self.sun.kill()
        if scene.drag_plant:
            scene.click_result[1].clicked = False
            scene.removeMouseImage()

    def update(self, scene, now, pos, clicks):
        self.now = now
        self.update_voice(scene, now)
        if pos and clicks[0] and self.skip_rect.collidepoint(pos):
            self.finish(scene)
            return
        # Cancellation returns to the matching selection instruction.
        if clicks[1] and self.step in (3, 5):
            scene.click_result[1].clicked = False
            scene.removeMouseImage()
            self.step -= 1
            self.step_started, self.revealed = now, False
            return
        if not pos or not clicks[0]:
            if self.step in (3, 5):
                scene.setupHintImage()
            return
        if self.step in (0, 6):
            if self.next_rect.collidepoint(pos):
                if self.step == 6:
                    self.finish(scene)
                else:
                    self.advance(scene, now)
            else:
                self.revealed = True
            return
        target = self.target_rect(scene)
        if target is None or not target.collidepoint(pos):
            return
        if self.step == 1:
            if self.sun.checkCollision(*pos):
                scene.menubar.increaseSunValue(self.sun.sun_value)
                c.SOUND_COLLECT_SUN.play()
                self.advance(scene, now)
        elif self.step in (2, 4):
            result = scene.menubar.checkCardClick(pos)
            if result:
                scene.click_result = result
                scene.setupMouseImage(*result)
                result[1].clicked = True
                c.SOUND_CLICK_CARD.play()
                self.advance(scene, now)
        elif self.step in (3, 5):
            cell = self.attack_cell if self.step == 3 else self.sun_cell
            if scene.map.getMapIndex(*pos) != cell:
                return
            scene.addPlant(pos)
            if not scene.drag_plant:
                self.advance(scene, now)

    def update_voice(self, scene, now):
        speaking = not self.revealed and now - self.step_started < len(self.steps[self.step][1]) * 32
        self.voice.update(now, speaking, scene.game_info[c.SOUND_VOLUME])

    def lines(self, text, width=510):
        rows = []
        for paragraph in text.split('\n'):
            line = ''
            for ch in paragraph:
                if self.font.size(line + ch)[0] > width:
                    rows.append(line)
                    line = ''
                line += ch
            rows.append(line)
        return rows

    def draw(self, surface, scene):
        target = self.target_rect(scene)
        veil = pg.Surface(c.SCREEN_SIZE, pg.SRCALPHA)
        veil.fill((12, 23, 18, 98))
        if target:
            pg.draw.rect(veil, (0, 0, 0, 0), target.inflate(8, 8), border_radius=9)
        surface.blit(veil, (0, 0))
        if target:
            pulse = 3 + int((math.sin(self.now / 180) + 1) * 1.5)
            pg.draw.rect(surface, (255, 224, 92), target, pulse, border_radius=8)
            tx, ty = target.centerx, target.bottom + 16
            pg.draw.polygon(surface, (255, 224, 92),
                            [(tx, ty - 10), (tx - 8, ty + 3), (tx + 8, ty + 3)])

        surface.blit(paper_panel((220, 32)), (18, 112))
        surface.blit(self.small.render(self.heading, True, (75, 57, 30)), (31, 119))
        draw_button(surface, self.skip_rect, '跳过引导', self.small)

        panel = pg.Rect(224, 423, 560, 167)
        surface.blit(paper_panel(panel.size), panel)
        surface.blit(self.small.render(f'凯夫    {self.step + 1} / {len(self.steps)}', True, (82, 108, 52)), (245, 436))
        title, body = self.steps[self.step]
        surface.blit(self.title_font.render(title, True, (41, 57, 30)), (244, 459))
        chars = len(body) if self.revealed else max(0, int((self.now - self.step_started) / 32))
        visible = body[:chars]
        for i, line in enumerate(self.lines(visible)):
            surface.blit(self.font.render(line, True, (52, 57, 39)), (245, 496 + i * 23))
        speaking = chars < len(body)
        # Mouth/gesture poses use a fixed root; only small breathing motion is added.
        pose = self.poses[(int(self.now / 170) % 2) if speaking else 0]
        breath = 1 + math.sin(self.now / 450) * 0.008
        frame = pg.transform.smoothscale(pose, (220, round(230 * breath)))
        surface.blit(frame, frame.get_rect(midbottom=(112, 600)))
        if self.step in (0, 6):
            text = '开始守草坪' if len(self.steps) == 1 or self.step == 6 else '开始教学'
            draw_button(surface, self.next_rect, text, self.font)
        else:
            surface.blit(self.small.render('单击黄色框里的目标', True, (112, 121, 79)), (582, 561))


class StageIntro(FirstLawnGuide):
    def __init__(self, scene, now, stage):
        from .custom_campaign import INTROS
        super().__init__(scene, now)
        self.steps = INTROS[stage]
        self.heading = f'第 {stage} 关 · 凯夫介绍'

    def target_rect(self, scene):
        return None

    def update(self, scene, now, pos, clicks):
        self.now = now
        self.update_voice(scene, now)
        if pos and clicks[0]:
            if self.next_rect.collidepoint(pos) or self.skip_rect.collidepoint(pos):
                self.finish(scene)
            else:
                self.revealed = True
                self.voice.stop()
