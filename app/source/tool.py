import json
import logging
import os
import shutil
from abc import abstractmethod
from collections import deque

import pygame as pg
from pygame.locals import *

from . import constants as c

logger = logging.getLogger('main')

# 状态机 抽象基类
class State:
    def __init__(self):
        self.start_time = 0
        self.current_time = 0
        self.done = False   # false 代表未做完
        self.next = None    # 表示这个状态退出后要转到的下一个状态
        self.persist = {}   # 在状态间转换时需要传递的数据

    # 当从其他状态进入这个状态时，需要进行的初始化操作
    @abstractmethod
    def startup(self, current_time: int, persist: dict):
        # 前面加了@abstractmethod表示抽象基类中必须要重新定义的method（method是对象和函数的结合）
        pass

    # 当从这个状态退出时，需要进行的清除操作
    def cleanup(self):
        self.done = False
        return self.persist

    # 在这个状态运行时进行的更新操作
    @abstractmethod
    def update(self, surface: pg.Surface, keys, current_time: int):
        # 前面加了@abstractmethod表示抽象基类中必须要重新定义的method
        pass

    # 工具：范围判断函数，用于判断点击
    def inArea(self, rect: pg.Rect, x: int, y: int):
        if rect.x <= x <= rect.right and rect.y <= y <= rect.bottom:
            return True
        else:
            return False

    # 工具：用户数据保存函数
    def saveUserData(self):
        with open(c.USERDATA_PATH, 'w', encoding='utf-8') as f:
            userdata = {}
            for i in self.game_info:
                if i in c.INIT_USERDATA:
                    userdata[i] = self.game_info[i]
            data_to_save = json.dumps(userdata, sort_keys=True, indent=4)
            f.write(data_to_save)


# 进行游戏控制 循环 事件响应
class Control:
    def __init__(self):
        self.screen = pg.display.get_surface()
        self.done = False
        self.clock = pg.time.Clock()    # 创建一个对象来帮助跟踪时间
        self.keys = pg.key.get_pressed()
        self.mouse_pos = None
        self.pending_clicks = deque()
        self.mouse_click = [
            False,
            False,
        ]  # value:[left mouse click, right mouse click]
        self.current_time = 0.0
        self.state_dict = {}
        self.state_name = None
        self.state = None
        try:
            # 存在存档即导入
            # 先自动修复读写权限(Python权限规则和Unix不一样，420表示unix的644，Windows自动忽略不支持项)
            os.chmod(c.USERDATA_PATH, 420)
            with open(c.USERDATA_PATH, encoding='utf-8') as f:
                userdata = json.load(f)
        except FileNotFoundError:
            self.setupUserData()
        except json.JSONDecodeError:
            logger.warning('用户存档解码错误！程序将新建初始存档！\n')
            self.setupUserData()
        else:   # 没有引发异常才执行
            self.game_info = {}
            # 导入数据，保证了可运行性，但是放弃了数据向后兼容性，即假如某些变量在以后改名，在导入时可能会被重置
            need_to_rewrite = False
            if userdata.get(c.CUSTOM_CAMPAIGN_VERSION) != 1:
                # One-time migration only; retain the complete original save.
                backup = c.USERDATA_PATH + '.before-custom-campaign.json'
                if not os.path.exists(backup):
                    shutil.copy2(c.USERDATA_PATH, backup)
                userdata[c.LEVEL_NUM] = 1
                userdata[c.CUSTOM_CAMPAIGN_VERSION] = 1
                need_to_rewrite = True
            for key in c.INIT_USERDATA:
                if key in userdata:
                    self.game_info[key] = userdata[key]
                else:
                    self.game_info[key] = c.INIT_USERDATA[key]
                    need_to_rewrite = True
            if need_to_rewrite:
                with open(c.USERDATA_PATH, 'w', encoding='utf-8') as f:
                    savedata = json.dumps(
                        self.game_info, sort_keys=True, indent=4
                    )
                    f.write(savedata)
        # 存档内不包含即时游戏时间信息，需要新建
        self.game_info[c.CURRENT_TIME] = 0

        # 50为目前的基础帧率，乘以倍率即是游戏帧率
        self.fps = 50 * self.game_info[c.GAME_RATE]

    def setupUserData(self):
        if not os.path.exists(os.path.dirname(c.USERDATA_PATH)):
            os.makedirs(os.path.dirname(c.USERDATA_PATH))
        with open(c.USERDATA_PATH, 'w', encoding='utf-8') as f:
            savedata = json.dumps(c.INIT_USERDATA, sort_keys=True, indent=4)
            f.write(savedata)
        self.game_info = c.INIT_USERDATA.copy()   # 内部全是不可变对象，浅拷贝即可

    def setup_states(self, state_dict: dict, start_state):
        self.state_dict = state_dict
        self.state_name = start_state
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.current_time, self.game_info)

    def update(self):
        # 自 pygame_init() 调用以来的毫秒数 * 游戏速度倍率，即游戏时间
        self.current_time = self.game_clock() * self.game_info[c.GAME_RATE]

        if self.state.done:
            self.flip_state()

        # Deliver each press once, in order, even if several arrived in one frame.
        if self.pending_clicks:
            button, self.mouse_pos = self.pending_clicks.popleft()
            self.mouse_click[:] = [button == 1, button == 3]

        self.state.update(
            self.screen, self.current_time, self.mouse_pos, self.mouse_click
        )
        self.mouse_pos = None
        self.mouse_click[0] = False
        self.mouse_click[1] = False

    def game_clock(self):
        return pg.time.get_ticks()

    # 状态转移
    def flip_state(self):
        if self.state.next == c.EXIT:
            pg.quit()
            os._exit(0)
        self.state_name = self.state.next
        persist = self.state.cleanup()
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.current_time, persist)

    def event_loop(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            elif event.type == pg.KEYDOWN:
                self.keys = pg.key.get_pressed()
                if event.key == pg.K_f:
                    pg.display.set_mode(
                        c.SCREEN_SIZE, pg.HWSURFACE | pg.FULLSCREEN
                    )
                elif event.key == pg.K_u:
                    pg.display.set_mode(c.SCREEN_SIZE)
                else:
                    handler = getattr(self.state, 'handle_key', None)
                    if handler and handler(event) == 'level_changed':
                        # Clicks aimed at the old level must not leak into the new one.
                        self.pending_clicks.clear()
                        self.mouse_pos = None
                        self.mouse_click[:] = [False, False]
            elif event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button in (1, 3):
                # Current mouse state may already be released or at another position.
                # Use the event snapshot; ignore middle button and legacy wheel events.
                self.pending_clicks.append((event.button, event.pos))

    def run(self):
        while not self.done:
            self.event_loop()
            self.update()
            pg.display.update()
            self.clock.tick(self.fps)


def get_image(
    sheet: pg.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    colorkey: tuple[int] = c.BLACK,
    scale: int = 1,
) -> pg.Surface:
    # 不保留alpha通道的图片导入
    image = pg.Surface([width, height])
    rect = image.get_rect()

    image.blit(sheet, (0, 0), (x, y, width, height))
    if colorkey:
        image.set_colorkey(colorkey)
    image = pg.transform.scale(
        image, (int(rect.width * scale), int(rect.height * scale))
    )
    return image


def get_image_alpha(
    sheet: pg.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    colorkey: tuple[int] = c.BLACK,
    scale: int = 1,
) -> pg.Surface:
    # 保留alpha通道的图片导入
    image = pg.Surface([width, height], SRCALPHA)
    rect = image.get_rect()

    image.blit(sheet, (0, 0), (x, y, width, height))
    image.set_colorkey(colorkey)
    image = pg.transform.scale(
        image, (int(rect.width * scale), int(rect.height * scale))
    )
    return image


def load_image_frames(
    directory: str, image_name: str, colorkey: tuple[int], accept: tuple[str]
) -> list[pg.Surface]:
    frame_list = []
    tmp = {}
    # image_name is "Peashooter", pic name is "Peashooter_1", get the index 1
    index_start = len(image_name) + 1
    frame_num = 0
    for pic in os.listdir(directory):
        name, ext = os.path.splitext(pic)
        if ext.lower() in accept:
            index = int(name[index_start:])
            img = pg.image.load(os.path.join(directory, pic))
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
                img.set_colorkey(colorkey)
            tmp[index] = img
            frame_num += 1

    for i in range(frame_num):  # 这里注意编号必须连续，否则会出错
        frame_list.append(tmp[i])
    return frame_list


# colorkeys 是设置图像中的某个颜色值为透明,这里用来消除白边
def load_all_gfx(
    directory: str,
    colorkey: tuple[int] = c.WHITE,
    accept: tuple[str] = ('.png', '.jpg', '.bmp', '.gif', '.webp'),
) -> dict[str : pg.Surface]:
    graphics = {}
    for name1 in os.listdir(directory):
        # subfolders under the folder resources\graphics
        dir1 = os.path.join(directory, name1)
        if os.path.isdir(dir1):
            for name2 in os.listdir(dir1):
                dir2 = os.path.join(dir1, name2)
                if os.path.isdir(dir2):
                    # e.g. subfolders under the folder resources\graphics\Zombies
                    for name3 in os.listdir(dir2):
                        dir3 = os.path.join(dir2, name3)
                        # e.g. subfolders or pics under the folder resources\graphics\Zombies\ConeheadZombie
                        if os.path.isdir(dir3):
                            # e.g. it"s the folder resources\graphics\Zombies\ConeheadZombie\ConeheadZombieAttack
                            image_name, _ = os.path.splitext(name3)
                            graphics[image_name] = load_image_frames(
                                dir3, image_name, colorkey, accept
                            )
                        else:
                            # e.g. pics under the folder resources\graphics\Plants\Peashooter
                            image_name, _ = os.path.splitext(name2)
                            graphics[image_name] = load_image_frames(
                                dir2, image_name, colorkey, accept
                            )
                            break
                else:
                    # e.g. pics under the folder resources\graphics\Screen
                    name, ext = os.path.splitext(name2)
                    if ext.lower() in accept:
                        img = pg.image.load(dir2)
                        if img.get_alpha():
                            img = img.convert_alpha()
                        else:
                            img = img.convert()
                            img.set_colorkey(colorkey)
                        graphics[name] = img
    return graphics


# Also cover alternate launchers importing tool after pygame initialization.
# The first click should both activate the window AND reach the game.
os.environ['SDL_MOUSE_FOCUS_CLICKTHROUGH'] = '1'
pg.display.set_caption(c.ORIGINAL_CAPTION)  # 设置标题
SCREEN = pg.display.set_mode(c.SCREEN_SIZE)   # CSS fits the unchanged 800x600 framebuffer.
pg.mixer.set_num_channels(255)  # 设置可以同时播放的音频数量，默认为8，经常不够用
if os.path.exists(
    c.ORIGINAL_LOGO
):    # 设置窗口图标，仅对非Nuitka时生效，Nuitka不需要包括额外的图标文件，自动跳过这一过程即可
    pg.display.set_icon(pg.image.load(c.ORIGINAL_LOGO))

GFX = load_all_gfx(c.PATH_IMG_DIR)

from .component.sun_gas_effects import install_assets

install_assets(GFX)

from .component.portrait_nut_assets import install_assets as install_portrait_nut

install_portrait_nut(GFX)

from .component.portrait_cherry import install_assets as install_portrait_cherry

install_portrait_cherry(GFX)

from .component.grin_animation import install_assets as install_grin_animation

install_grin_animation(GFX)

from .component.headphone_boxer import install_assets as install_headphone_boxer

install_headphone_boxer(GFX)

from .component.portrait_potato import install_assets as install_portrait_potato

install_portrait_potato(GFX)

from .component.portrait_squash import install_assets as install_portrait_squash

install_portrait_squash(GFX)

from .component.portrait_healer import install_assets as install_portrait_healer

install_portrait_healer(GFX)

from .component.portrait_chomper import install_assets as install_portrait_chomper

install_portrait_chomper(GFX)

from .component.portrait_threepeater import install_assets as install_portrait_threepeater

install_portrait_threepeater(GFX)

from .component.avatar_sun_assets import install_assets as install_avatar_sun

install_avatar_sun(GFX)

from .component.face_shovel import install_assets as install_face_shovel

install_face_shovel(GFX)

from .component.portrait_zombie_assets import install_assets as install_portrait_zombie

install_portrait_zombie(GFX)

from .component.elite_zombie_assets import install_assets as install_elite_zombie

install_elite_zombie(GFX)

from .component.plant_layout import install_layout

install_layout(GFX)
