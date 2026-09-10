"""Five portrait-only stages, fixed decks, clear-gated waves and card rewards."""
import math
import random
import pygame as pg
from .. import constants as c
from .pvz_ui import paper_panel, draw_button

STARTERS = (c.GRINDEVOURER, c.GASSUNFLOWER)
REWARDS = {
    1: (c.PORTRAITTALLNUT, c.PORTRAITCHOMPER),
    2: (c.PORTRAITCHERRYBOMB, c.PORTRAITPOTATOMINE),
    3: (c.HEADPHONEBOXER, c.PORTRAITSQUASH, c.PORTRAITHEALER, c.PORTRAITTHREEPEATER),
    4: (),
}
ALL_CARDS = STARTERS + REWARDS[1] + REWARDS[2] + REWARDS[3]
TITLES = ('初见草坪', '三路挑战', '初出茅庐', '全员出击', '无尽守卫')
# Finite levels have explicit encounter budgets, not endless-mode scaling.
WAVE_COUNTS = {1: (1, 2, 2, 3), 2: (3, 5, 7, 9),
               3: (4, 7, 10, 13, 16), 4: (6, 10, 14, 18, 22, 26)}
PREPARATION_MS = (18000, 24000, 30000, 32000, 18000)
REST_MS = (10000, 12000, 10000, 8000, 8000)
INTROS = {
    2: (('三条路，都要守住！', f'草坪增加到三行，游戏更有挑战性了！\n带上{c.PLANT_DISPLAY_NAMES[c.PORTRAITTALLNUT]}和{c.PLANT_DISPLAY_NAMES[c.PORTRAITCHOMPER]}，保护好每一路。'),),
    3: (('初出茅庐', f'你已经是初出茅庐了，加油吧少年！\n五行草坪，{c.PLANT_DISPLAY_NAMES[c.PORTRAITCHERRYBOMB]}和{c.PLANT_DISPLAY_NAMES[c.PORTRAITPOTATOMINE]}也来帮忙了。'),),
    4: (('全员集合！', '你已经解锁了所有的植物，少年，加油面对未来吧！\n发挥十位伙伴的本领，胜利后就能挑战无尽模式。'),),
    5: (('无尽守卫', '每一波清完，下一波才会到来，而且会更难。\n阵容和阳光会保留。少年，看看你能守住多少波！'),),
}


def cards_for(stage):
    return STARTERS + sum((REWARDS[n] for n in range(1, min(stage, 4))), ())


def map_for(stage):
    return {c.BACKGROUND_TYPE: (c.BACKGROUND_SINGLE if stage == 1 else
                              c.BACKGROUND_TRIPLE if stage == 2 else c.BACKGROUND_DAY),
            c.GAME_TITLE: f'自定义 {stage}/5 · {TITLES[stage - 1]}',
            c.INIT_SUN_NAME: (150, 200, 250, 300, 350)[stage - 1],
            c.SHOVEL: 1, c.SPAWN_ZOMBIES: c.SPAWN_ZOMBIES_LIST, c.ZOMBIE_LIST: (),
            c.NUM_FLAGS: 1, c.INCLUDED_ZOMBIES: (c.NORMAL_ZOMBIE,),
            'custom_stage': stage}


class CampaignBattle:
    def __init__(self, scene):
        self.stage = scene.map_data['custom_stage']
        self.total = (4, 4, 5, 6, None)[self.stage - 1]
        self.wave = 0
        self.pending = 0
        self.spawned = 0
        self.in_wave = False
        self.finished = False
        self.best = scene.game_info.get(c.CUSTOM_ENDLESS_BEST, 0)
        self.next_wave = scene.current_time + PREPARATION_MS[self.stage - 1]
        self.next_spawn = 0
        self.font = pg.font.Font(c.FONT_PATH, 16)
        self.rows = (2,) if self.stage == 1 else (1, 2, 3) if self.stage == 2 else tuple(range(5))

    def difficulty(self, wave):
        if self.stage == 5:
            # Bound simultaneous workload, but never cap the health progression.
            return min(60, 6 + 2 * wave), 1 + .10 * (wave - 1), 1 + .035 * (wave - 1), min(1.6, 1 + .015 * (wave - 1))
        return WAVE_COUNTS[self.stage][wave - 1], (0.8, 1, 1.05, 1.15)[self.stage - 1], 1, 1

    def spawn_interval(self):
        if self.stage == 5:
            return max(450, 1300 - self.wave * 35)
        return max(1000, (3000, 2200, 1700, 1400)[self.stage - 1] - 120 * (self.wave - 1))

    def update(self, scene, now):
        if self.finished:
            return
        if not self.in_wave:
            if now < self.next_wave:
                return
            self.wave += 1
            scene.wave_num = self.wave
            self.pending = self.difficulty(self.wave)[0]
            self.spawned = 0
            self.next_spawn = now
            self.in_wave = True
        if self.pending and now >= self.next_spawn:
            from .zombie import PortraitZombie, ElitePortraitZombie
            row = self.rows[(self.spawned + self.wave - 1) % len(self.rows)]
            every = max(3, 9 - self.wave // 5) if self.stage == 5 else 7
            elite = self.stage > 1 and (self.spawned + self.wave) % every == 0
            cls = ElitePortraitZombie if elite else PortraitZombie
            _, y = scene.map.getMapGridPos(0, row)
            enemy = cls(c.ZOMBIE_START_X + random.randint(0, 30), y, scene.head_group)
            _, hp, damage, speed = self.difficulty(self.wave)
            enemy.health = round(enemy.health * hp)
            enemy.damage = round(enemy.damage * damage)
            enemy.speed *= speed
            scene.zombie_groups[row].add(enemy)
            self.spawned += 1
            self.pending -= 1
            self.next_spawn = now + self.spawn_interval()
        # Include death animations; no next wave while even one enemy remains.
        if self.pending == 0 and not any(scene.zombie_groups):
            self.in_wave = False
            if self.stage == 5:
                if self.wave > scene.game_info.get(c.CUSTOM_ENDLESS_BEST, 0):
                    scene.game_info[c.CUSTOM_ENDLESS_BEST] = self.wave
                    self.best = self.wave
                    scene.saveUserData()
            elif self.wave == self.total:
                self.finished = True
                return
            self.next_wave = now + REST_MS[self.stage - 1]

    def draw(self, surface, now):
        if self.finished or self.total is not None:
            return
        suffix = '无尽' if self.total is None else str(self.total)
        text = f'第 {self.stage} 关  ·  波次 {self.wave}/{suffix}'
        if self.stage == 5:
            text += f'  ·  最佳 {self.best}'
        if not self.in_wave:
            text += f'  ·  下一波 {max(0, math.ceil((self.next_wave - now) / 1000))} 秒'
        else:
            text += f'  ·  待入场 {self.pending}'
        label = self.font.render(text, True, (70, 54, 30))
        rect = label.get_rect(bottomright=(787, 594)).inflate(16, 10)
        surface.blit(paper_panel(rect.size), rect)
        surface.blit(label, (rect.x + 8, rect.y + 5))


DESCRIPTIONS = {
    c.GRINDEVOURER: (c.PLANT_DISPLAY_NAMES[c.GRINDEVOURER], ('跨行追踪，自动寻找僵尸。', f'每 {c.GRINDEVOURER_SHOOT_INTERVAL / 1000:g} 秒发射一颗子弹，伤害 {c.GRINDEVOURER_DAMAGE}。', '适合后排稳定输出。')),
    c.GASSUNFLOWER: (c.PLANT_DISPLAY_NAMES[c.GASSUNFLOWER], ('种下约 6 秒首次生产阳光。', f'之后每 {c.GASSUNFLOWER_SUN_INTERVAL / 1000:g} 秒生产 25 阳光。', '保护好它，才能持续补充阵容。')),
    c.PORTRAITTALLNUT: (c.PLANT_DISPLAY_NAMES[c.PORTRAITTALLNUT], ('4500 生命值，负责挡住僵尸。', '受损会显示血条和破损状态。', '放在输出植物前方保护伙伴。')),
    c.PORTRAITCHOMPER: (c.PLANT_DISPLAY_NAMES[c.PORTRAITCHOMPER], ('吞下同一行前方的一个僵尸。', '吞食后咀嚼 10 秒才能再次进食。', '咀嚼期间仍然会受到攻击。')),
    c.PORTRAITCHERRYBOMB: (c.PLANT_DISPLAY_NAMES[c.PORTRAITCHERRYBOMB], ('短暂蓄力后爆炸，一次性使用。', '对附近三行造成 1800 爆炸伤害。', '适合处理聚集的僵尸。')),
    c.PORTRAITPOTATOMINE: (c.PLANT_DISPLAY_NAMES[c.PORTRAITPOTATOMINE], ('埋入地下，约 15 秒后准备完成。', '成熟后被踩中造成 1800 伤害。', '未成熟时会被吃掉，请提前布置。')),
    c.HEADPHONEBOXER: (c.PLANT_DISPLAY_NAMES[c.HEADPHONEBOXER], ('同一行近战连击：20 / 20 / 40。', '前方攻击距离 220，可隔坚果打击。', '搭配坚果可以安全持续输出。')),
    c.PORTRAITSQUASH: (c.PLANT_DISPLAY_NAMES[c.PORTRAITSQUASH], ('发现附近僵尸后急眼、跳起砸下。', '落地对同一行附近敌人造成 1800。', '一次性使用，适合紧急救场。')),
    c.PORTRAITHEALER: (c.PLANT_DISPLAY_NAMES[c.PORTRAITHEALER], ('种下 2 秒首疗，每 15 秒治疗 3×3。', '恢复最大血量 25%，每株上限 150。', '同株 15 秒内不叠加治疗，不复活。')),
    c.PORTRAITTHREEPEATER: (c.PLANT_DISPLAY_NAMES[c.PORTRAITTHREEPEATER], ('同时射击本行及相邻的上下两行。', '每 1.4 秒一轮，每颗豌豆伤害 20。', '边缘处不会向草坪外发射。')),
}


class CardTooltip:
    DELAY = 500

    def __init__(self):
        self.card = None
        self.since = 0
        self.visible = False
        self.font = pg.font.Font(c.FONT_PATH, 16)
        self.title_font = pg.font.Font(c.FONT_PATH, 20)

    def update(self, cards, pos, now, enabled=True):
        hovered = next((card for card in cards if card.rect.collidepoint(pos)
                        and card.info[0] in DESCRIPTIONS), None) if enabled and pos else None
        if hovered is not self.card:
            self.card, self.since = hovered, now
        self.visible = hovered is not None and now - self.since >= self.DELAY

    def draw(self, surface):
        if not self.visible:
            return
        card = self.card
        title, lines = DESCRIPTIONS[card.info[0]]
        rect = pg.Rect(max(8, min(452, card.rect.centerx - 168)), card.rect.bottom + 10, 340, 154)
        surface.blit(paper_panel(rect.size), rect)
        surface.blit(self.title_font.render(title, True, (41, 64, 32)), (rect.x + 14, rect.y + 10))
        cost = f'{card.sun_cost} 阳光  ·  卡片冷却 {card.frozen_time / 1000:g} 秒'
        surface.blit(self.font.render(cost, True, (116, 87, 42)), (rect.x + 14, rect.y + 40))
        for i, line in enumerate(lines):
            surface.blit(self.font.render(line, True, (51, 62, 44)), (rect.x + 14, rect.y + 69 + i * 24))


class CardRewards:
    """Falling unlock cards. A single explicit button can collect the whole set."""
    def __init__(self, stage, now):
        from .. import tool
        self.stage = stage
        self.started = self.now = now
        self.names = REWARDS[stage]
        self.claimed = set()
        self.images = [tool.GFX[c.PLANT_CARD_INFO[c.PLANT_CARD_INDEX[name]][1]] for name in self.names]
        self.background = tool.get_image(tool.GFX[c.GAME_VICTORY_IMAGE], 0, 0, 800, 600)
        self.button = pg.Rect(344, 553, 111, 26)
        self.rects = []
        self.font = pg.font.Font(c.FONT_PATH, 20)
        self.title_font = pg.font.Font(c.FONT_PATH, 34)
        self.button_font = pg.font.Font(c.FONT_PATH, 16)
        self.layout(now)

    def layout(self, now):
        self.now = now
        self.rects = []
        for i in range(len(self.names)):
            t = max(0, min(1, (now - self.started - i * 130) / 650))
            y = round(-180 + 466 * (1 - (1 - t) ** 3))
            self.rects.append(pg.Rect(400 - len(self.names) * 65 + i * 130 + 15, y, 100, 140))

    def update(self, now, pos, clicks):
        self.layout(now)
        if now - self.started < 1100 or not pos or not clicks[0]:
            return False
        for i, rect in enumerate(self.rects):
            if rect.collidepoint(pos) and i not in self.claimed:
                self.claimed.add(i)
                c.SOUND_COLLECT_SUN.play()
        if self.button.collidepoint(pos):
            self.claimed.update(range(len(self.names)))
            return True
        return False

    def draw(self, surface):
        surface.fill(c.WHITE)
        surface.blit(self.background, (0, 0))
        surface.blit(paper_panel((548, 265)), (117, 241))
        sub = f'第 {self.stage} 关通关！领取新植物，下一关自动加入' if self.names else '第四关通关！下一站：无尽模式'
        label = self.font.render(sub, True, (132, 84, 37))
        surface.blit(label, label.get_rect(center=(391, 264)))
        for i, (image, rect) in enumerate(zip(self.images, self.rects)):
            surface.blit(image, rect)
            if self.now - self.started >= 1100:
                label = self.font.render('已领取' if i in self.claimed else '点击领取', True, (104, 78, 35))
                surface.blit(label, label.get_rect(center=(rect.centerx, rect.bottom + 28)))
        draw_button(surface, self.button, '领取并继续' if self.names else '进入无尽', self.button_font)
