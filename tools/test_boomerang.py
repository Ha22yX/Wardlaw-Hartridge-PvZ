"""Eleven-card layout and finite-range, once-per-leg piercing regression."""
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

with tempfile.TemporaryDirectory(prefix='pvz-boomerang-test-') as tmp:
    c.USERDATA_PATH = str(Path(tmp) / 'save.json')
    c.USERLOG_PATH = str(Path(tmp) / 'log.txt')
    from web_platform import BrowserPlatform
    BrowserPlatform().prepare_save(c)
    from source.runtime_check import load_game_modules
    c, tool, level, *_ = load_game_modules()
    from source.component.custom_campaign import cards_for, REWARDS
    from source.component.portrait_boomerang import SIZE, ReturningBoomerang
    from source.component import menubar
    game = tool.Control()
    game.game_info.update({c.GAME_MODE: c.MODE_ADVENTURE, c.LEVEL_NUM: 4})
    scene = level.Level()
    scene.startup(0, game.game_info)
    assert c.CARD_MAX_NUM == len(scene.menubar.card_list) == 11
    assert c.PORTRAITBOOMERANG in REWARDS[3]
    assert [len(cards_for(s)) for s in range(1, 6)] == [2, 4, 6, 11, 11]
    cards = scene.menubar.card_list
    for a, b in zip(cards, cards[1:]):
        assert a.rect.right < b.rect.left
    assert cards[-1].rect.right < scene.menubar.rect.right
    assert not cards[-1].rect.colliderect(scene.shovel_box_rect)
    panel = menubar.Panel(c.CARDS_TO_CHOOSE, 9999, c.BACKGROUND_DAY)
    for name in cards_for(4):
        panel.addCard(panel.card_list[c.PLANT_CARD_INDEX[name]])
    assert len(panel.selected_cards) == 11 and panel.selected_cards[-1].rect.right < 600

    scene.first_lawn_guide.finish(scene)
    scene.menubar.sun_value = 9999
    scene.menubar.update(0)
    seed = cards[-1]
    assert seed.info[0] == c.PORTRAITBOOMERANG
    scene.click_result = (c.PORTRAITBOOMERANG, seed)
    scene.setupMouseImage(*scene.click_result)
    scene.addPlant(scene.map.getMapGridPos(2, 2))
    owner = next(iter(scene.plant_groups[2]))
    assert not seed.canClick(9999, 0)
    assert owner.name == c.PORTRAITBOOMERANG

    def enemy(dx, row=2, hypno=False):
        z = pg.sprite.Sprite(scene.zombie_groups[row])
        z.rect = pg.Rect(0, 0, 20, 60)
        z.rect.center = (owner.rect.centerx + dx, owner.rect.bottom - 40)
        z.name, z.state, z.health = c.NORMAL_ZOMBIE, c.WALK, 1000
        z.is_hypno = hypno
        z.hits = []
        def damage(amount, **kwargs):
            z.hits.append(amount)
            z.health -= amount
        z.setDamage = damage
        return z

    victims = [enemy(dx) for dx in (60, 160, 320, 400)]
    outside, behind, upper, hypno = enemy(401), enemy(-40), enemy(100, 1), enemy(200, hypno=True)
    owner.update({c.CURRENT_TIME: 0})
    assert owner.phase == 'Charge'
    owner.update({c.CURRENT_TIME: 349})
    assert owner.projectile is None
    owner.update({c.CURRENT_TIME: 350})
    shot = owner.projectile
    assert owner.phase == 'Throw' and shot.alive()
    for t in range(370, 1251, 20):
        shot.update({c.CURRENT_TIME: t})
    assert shot.rect.centerx == owner.rect.centerx + 400
    assert all(z.hits == [20] for z in victims)
    for t in range(1270, 2151, 20):
        shot.update({c.CURRENT_TIME: t})
    assert all(z.hits == [20, 20] for z in victims)
    assert all(not z.hits for z in (outside, behind, upper, hypno))
    assert not shot.alive()
    owner.update({c.CURRENT_TIME: 2150})
    assert owner.phase == 'Catch'
    owner.update({c.CURRENT_TIME: 2500})
    owner.update({c.CURRENT_TIME: 2850})
    assert owner.projectile is not shot and owner.projectile.alive()
    # One delayed frame must still trace both legs, with no duplicate hits.
    owner.projectile.update({c.CURRENT_TIME: 5000})
    assert all(len(z.hits) == 4 for z in victims)
    orphan = ReturningBoomerang(owner, 6000, tool.GFX)
    scene.bullet_groups[2].add(orphan)
    owner.kill()
    orphan.update({c.CURRENT_TIME: 7800})
    assert not orphan.alive()

    for phase in ('Idle', 'Charge', 'Throw', 'Wait', 'Catch'):
        frames = tool.GFX[c.PORTRAITBOOMERANG + phase]
        assert len(frames) == 24
        assert len({pg.image.tobytes(f, 'RGBA') for f in frames}) > 1
        for f in frames:
            b = f.get_bounding_rect()
            assert f.get_size() == SIZE and b.left > 0 and b.right < SIZE[0]
            assert b.top > 0 and b.bottom < SIZE[1]
    output = os.environ.get('PVZ_TEST_CAPTURE_DIR')
    if output:
        Path(output).mkdir(parents=True, exist_ok=True)
        scene.plant_groups[2].add(owner)
        owner.image = tool.GFX[c.PORTRAITBOOMERANG][0]
        for group in scene.zombie_groups:
            group.empty()
        scene.head_group.empty()
        scene.draw(game.screen)
        pg.image.save(game.screen, str(Path(output) / '回旋镖游戏预览.png'))
    print('PASS 11 nonoverlapping packets, planting/cooldown, 5-tile boundary, piercing twice, excluded lanes/hypno, large frame, owner death, cadence and 120 rooted animation frames')
pg.quit()
