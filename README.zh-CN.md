<h1 align="center">Wardlaw Hartridge PvZ · 人像草坪保卫战</h1>

<p align="center">熟悉的草坪，熟悉的面孔，不太正常的校园日常。<br/>以 Wardlaw Hartridge School 国际生的抽象整活与校园梗为主题的个人《植物大战僵尸》改版。</p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong> ·
  <a href="https://pvz.rosebeg.com/">在线游玩</a> ·
  <a href="#快速开始">快速开始</a> · <a href="#来源与使用说明">来源与使用说明</a>
</p>

<p align="center">
  <img alt="Python 3.12" src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img alt="游戏引擎：Pygame CE" src="https://img.shields.io/badge/Game-Pygame_CE-568B35?style=for-the-badge" />
  <img alt="浏览器运行环境：WebAssembly" src="https://img.shields.io/badge/Browser-WebAssembly-654FF0?style=for-the-badge&logo=webassembly&logoColor=white" />
</p>

<p align="center">
  <img src="dist/custom-cover-v2.png" alt="项目封面插画：人物主题植物与僵尸在草坪两侧对阵" width="100%" />
  <br/><sub>项目封面插画；实际游戏使用独立的角色动画素材。</sub>
</p>

## 项目介绍

把校园里的熟人和梗，搬到需要认真防守的草坪上。Wardlaw Hartridge PvZ 将人物形象融入植物、僵尸和自定义引导角色 **「凯夫」**，配上专属动画、攻击方式与音效，让整活成为可以亲手玩的一场战役。

项目基于 [wszqkzqk/pypvz](https://github.com/wszqkzqk/pypvz)，加入五关自定义战役、11 张角色卡，以及通过 Pygbag 和 CPython WebAssembly 运行 Python 游戏的浏览器移植。原始 **800 × 600** 游戏画面按比例适配屏幕，保留完整棋盘与卡栏。

这是一个**个人非官方改版**，不代表学校或《植物大战僵尸》官方。游戏界面和对话以简体中文为主，仓库以私有形式保存源码和自定义人物素材。

## 在线游玩

打开 **[pvz.rosebeg.com](https://pvz.rosebeg.com/)**，点击 **Start the game**，等待运行环境与素材加载完成。选择 **「开始冒险吧」** 进入战役，或选择 **「玩玩小游戏」**。

- **种植：** 先点卡片，再点空闲草坪格；收集阳光以种下更多植物。
- **查看介绍：** 电脑悬停卡片半秒，触屏设备长按卡片。
- **管理阵容：** 用铲子移除植物，用游戏内加速按钮切换二倍速。
- **手机体验：** 横屏可以获得更大的棋盘画面；切到后台时，游戏与音频会自动暂停。

首次启动需要联网下载完整素材及 Pygbag CDN 上的运行环境；浏览器音频需要通过点击或触摸启用。

### 进度与存档

进度保存在当前浏览器中，可在 **「操作 / 存档」** 中导出 JSON 备份，或在另一台设备导入。刷新**不会保留未结束的对局**，清除浏览器数据会删除本地进度。网页存档与桌面版存档分开保存。

## 游戏特色

| 特色 | 当前内容 |
| --- | --- |
| 人物主题阵容 | 自定义植物、普通与精英僵尸、引导对话、角色动画和音效 |
| 11 张角色卡 | 阳光生产、追踪射击、阻挡、吞食、爆炸、近战、治疗、三线射击与回旋镖 |
| 战役成长 | 固定阵容、种植教学、通关奖励，草坪从一行扩展到三行、五行 |
| 无尽守卫 | 第五关逐波提升敌人强度，波次之间保留阵容和阳光 |
| 小游戏 | 自定义战役之外保留原有小游戏菜单 |
| 战斗反馈 | 卡片说明、部分角色的血条，以及二倍速 |
| 浏览器适配 | 鼠标与触屏、等比例显示、本地存档、失焦自动暂停和静音 |

**「回头浪子」** 向同路前方最多五格投掷穿透回旋镖，去程和回程可分别命中每只敌人一次，并包含待机、蓄力、投掷、等待和接回动画。

### 五关战役

| 关卡 | 名称 | 草坪 | 成长与目标 |
| --- | --- | --- | --- |
| 1 | 初见草坪 | 一行 | 从两张卡起步，通关解锁阻挡与吞食角色 |
| 2 | 三路挑战 | 三行 | 通关解锁樱桃炸弹与土豆雷角色 |
| 3 | 初出茅庐 | 五行 | 通关解锁拳手、窝瓜、治疗、三线射手和回旋镖角色 |
| 4 | 全员出击 | 五行 | 使用全部 11 张卡，完成最后一个有限波次关卡 |
| 5 | 无尽守卫 | 五行 | 挑战不断增强的敌人，刷新最佳波次纪录 |

### 可选快捷键

以下快捷键方便体验和调试，正常通关不需要使用。

| 按键 | 功能 |
| --- | --- |
| `9` | 增加 100 阳光 |
| `0` | 清空植物卡片冷却 |
| `-` | 上一关 |
| `=` / `+` | 下一关 |

## 快速开始

准备 **Python 3.12**、[uv](https://docs.astral.sh/uv/) 和 Git。克隆代码需要拥有此私有仓库的访问权限。

```sh
git clone https://github.com/Ha22yX/Wardlaw-Hartridge-PvZ.git
cd Wardlaw-Hartridge-PvZ
uv sync
uv run python tools/build_web.py
uv run python -m http.server 8787 --bind 127.0.0.1 --directory dist
```

访问 **[localhost:8787](http://127.0.0.1:8787/)**，通过 HTTP 服务打开游戏，不要直接双击 `index.html`。构建脚本将 Python 源码与游戏资源打包成素材归档；浏览器运行环境首次加载仍然需要联网。

生成的 `dist/` 目录可部署到静态 HTTPS 网站。现有站点使用 Nginx，服务器路径与证书维护信息见 [托管说明](docs/hosting.md)。

## 实现方式

浏览器通过 **Pygbag 0.9.3**、**pygame-ce 2.5.x** 和 **CPython 3.12 WebAssembly** 运行现有 Python/Pygame 游戏。HTML、CSS 和 JavaScript 负责加载界面、自适应排版、浏览器音频生命周期与存档操作。

- `app/main.py`：异步浏览器主循环，保留每秒 50 个逻辑帧及原有二倍速行为。
- `app/web_platform.py`：连接游戏状态与浏览器存档、触屏输入、音频和页面可见性。
- `app/source/`：玩法规则、角色行为、战役进度、菜单和小游戏。
- `app/resources/`：角色、界面、动画和音频素材。
- `tools/build_web.py`：导出界面素材，生成带内容哈希且限制大小的资源归档。

```text
app/
  main.py                 浏览器游戏入口
  web_platform.py         浏览器适配
  source/                 游戏逻辑与自定义角色
  resources/              角色、动画、字体与音频
dist/                     静态网站与打包后的游戏素材
tools/                    构建脚本与回归检查
docs/hosting.md           现有部署与维护记录
pyproject.toml            Python 版本与依赖
uv.lock                   依赖锁定文件
UPSTREAM_README.md        保留的原项目说明
```

### 开发检查

完成 `uv sync` 后，以下检查不需要单独的桌面版项目。JavaScript 检查还需要 Node.js。

```sh
uv run python tools/test_campaign_clock.py
uv run python tools/test_chomper.py
uv run python tools/test_healer.py
uv run python tools/test_boomerang.py
node tools/test_audio_lifecycle.mjs
node tools/test_boot_lifecycle.mjs
```

更完整的迁移检查涵盖源码/素材一致性、战役场景、教学种植、加速按钮、小游戏和存档导入导出：

```sh
uv run python tools/test_migration.py
```

其中桌面版一致性对照需要同级 `../pypvz/` 目录中的**对应桌面改版项目**。单独克隆本仓库不包含该目录，也不能用任意上游版本代替对照基线。

### 验证状态

此前项目记录显示，**2026 年 9 月 10 日**曾在正式站点检查浏览器启动、第一关七步教学、中文显示、两种初始植物的实际种植，以及横竖屏布局。音频生命周期另有隔离检查。这些检查不代表已经在所有真实手机和浏览器上完成全部关卡。

WebMCP 为兼容浏览器提供读取游戏状态和选择卡片的工具；正常游玩仍通过可见游戏界面操作。

## 来源与使用说明

- **直接基于：** [wszqkzqk/pypvz](https://github.com/wszqkzqk/pypvz)，原始说明完整保留在 [UPSTREAM_README.md](UPSTREAM_README.md)。
- **更早上游：** 原项目注明基于 [marblexu/PythonPlantsVsZombies](https://github.com/marblexu/PythonPlantsVsZombies)，部分代码整合自 [callmebg/PythonPlantsVsZombies](https://github.com/callmebg/PythonPlantsVsZombies)。
- **本改版新增：** 人物主题角色与素材、自定义战役、玩法扩展和浏览器适配。

《植物大战僵尸》素材归各自权利人所有。人物图片由用户提供，随本私有项目保存。保留上游个人学习研究用途声明；本改版不声称拥有原素材版权，也不为上游代码、游戏素材或人物图片另行授予许可。
