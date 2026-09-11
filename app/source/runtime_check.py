"""Reject mixed source/asset versions before opening a saved game."""
from importlib import import_module
from pathlib import Path


class StartupVersionMismatch(RuntimeError):
    pass


def source_snapshot():
    root = Path(__file__).resolve().parent.parent
    files = list((root / 'source').rglob('*.py'))
    files += list((root / 'resources' / 'generated_sources').glob('*.png'))
    return {str(path): (path.stat().st_mtime_ns, path.stat().st_size) for path in files}


def validate_runtime(constants, graphics, plants):
    """Check the constants, card registry, constructor and animation as one unit."""
    features = (
        ('PORTRAITHEALER', 'PortraitHealer', ('Idle', 'Charge', 'Release', 'Recover')),
        ('PORTRAITCHOMPER', 'PortraitChomper', ('Idle', 'Attack', 'Chew', 'Swallow')),
        ('PORTRAITTHREEPEATER', 'PortraitThreepeater', ('Idle', 'Charge', 'Shoot', 'Recover')),
        ('PORTRAITBOOMERANG', 'PortraitBoomerang', ('Idle', 'Charge', 'Throw', 'Wait', 'Catch')),
    )
    missing = []
    for attribute, class_name, phases in features:
        name = getattr(constants, attribute, None)
        if name is None:
            missing.append('constants.' + attribute)
            continue
        index = constants.PLANT_CARD_INDEX.get(name)
        if index is None:
            missing.append(name + ' 选卡索引')
        else:
            entry = constants.PLANT_CARD_INFO[index]
            if entry[0] != name or entry[1] not in graphics:
                missing.append(name + ' 卡片素材')
        if not hasattr(plants, class_name):
            missing.append('plant.' + class_name)
        for key in (name, *(name + phase for phase in phases)):
            if not graphics.get(key):
                missing.append(key + ' 动画')
    for attribute in ('PORTRAIT_PEA', 'PORTRAITTHREEPEATER_INTERVAL', 'PORTRAITTHREEPEATER_DAMAGE',
                      'CUSTOM_CAMPAIGN_VERSION', 'CUSTOM_CAMPAIGN_CLEARED', 'CUSTOM_ENDLESS_BEST'):
        if not hasattr(constants, attribute):
            missing.append('constants.' + attribute)
    if missing:
        raise StartupVersionMismatch('模块版本不一致：' + '、'.join(missing))


def load_game_modules():
    before = source_snapshot()
    try:
        constants = import_module('source.constants')
        tool = import_module('source.tool')
        level = import_module('source.state.level')
        mainmenu = import_module('source.state.mainmenu')
        screen = import_module('source.state.screen')
    except Exception as error:
        if source_snapshot() != before:
            raise StartupVersionMismatch('启动期间游戏文件发生了更新。') from error
        raise
    if source_snapshot() != before:
        raise StartupVersionMismatch('启动期间游戏文件发生了更新。')
    validate_runtime(constants, tool.GFX, level.plant)
    return constants, tool, level, mainmenu, screen
