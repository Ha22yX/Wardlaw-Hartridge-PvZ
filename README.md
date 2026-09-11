# Wardlaw Hartridge PvZ · 人像草坪保卫战

以 **Wardlaw Hartridge School 国际生的抽象整活文化**为主题的改版《植物大战僵尸》。将人物形象融入植物、僵尸和引导角色，保留熟悉的草坪塔防玩法，加入自定义动画、技能、关卡与网页体验。

本项目是个人非官方改版，不代表学校或《植物大战僵尸》官方。仓库以 private 形式保存源码及人物素材。

**原项目 / 原作者仓库：[wszqkzqk/pypvz](https://github.com/wszqkzqk/pypvz)**。本改版在该 Python 实现的基础上进行角色定制、玩法扩展和浏览器移植，并非从零原创的游戏引擎。

## 改版内容

- 人物主题植物与僵尸、自定义引导角色「凯夫」、角色动画与技能音效。
- 11 格顶部卡栏；「回头浪子」向同路前方 5 格投掷穿透回旋镖，去回程各命中一次，含待机、蓄力、投掷、等待和接回动画。
- 前四关循序推进：一行、三行、五行草坪，固定植物阵容与通关解锁奖励。
- 第五关为逐波提升难度的无尽模式，同时保留小游戏入口。
- 卡片介绍、治疗血条、二倍速，以及 `9`（增加 100 阳光）、`0`（清空植物卡片冷却）、`-`（上一关）、`=` / `+`（下一关）快捷键。
- 自适应网页显示、开始与加载界面、浏览器存档，以及切到后台自动暂停和静音。

## 网页移植

浏览器通过 Pygbag / CPython WebAssembly 执行现有 Python 游戏，不是 JavaScript 简化重写。

## 保持不变

- `app/resources/`：保存本改版使用的完整角色、界面、动画和音频资源，包括自定义素材。
- `app/source/`：原角色、动画、伤害、血量、冷却、费用、碰撞、地图、五关战役、奖励、无尽难度、小游戏、菜单、教学、音效代码。
- 原始 800 × 600 游戏画面，按比例适配屏幕，不拉伸或裁掉棋盘。

## 仅平台适配

- `app/main.py`：异步浏览器主循环，原 50 逻辑帧率，保留游戏原有二倍速。
- `app/web_platform.py`：浏览器存档、触屏点击、声音、页面可见性。
- `source/tool.py` 仅新增时钟接口，并让 CSS 管理画面缩放。
- 正式入口显示人物主题封面和 `Start the game` 按钮，点击后加载游戏并开启声音；加载完成前锁定游戏交互。电脑和手机都保留完整原卡栏、菜单和棋盘。
- 进度存储在当前浏览器，可导入/导出原 JSON 存档。不会修改桌面版存档。
- 浏览器首次播放音频需要用户手势；首次打开需下载完整素材和运行环境。
- 窗口失焦或标签页隐藏时，同时暂停模拟、HTMLAudio 音乐与 WebAudio 音效。
- WASM / JavaScript 之间采用 ASCII JSON 转义，修复加载文字与卡片说明的中文乱码。

## 正式托管

正式地址：https://pvz.rosebeg.com/ 。运行在用户的宝塔/Nginx 服务器，静态根目录为 `/www/wwwroot/pvz.rosebeg.com/current`。
HTTPS 由 Let's Encrypt 签发，通过现有 `certbot-renew.timer` 自动续期。
人工 SSH 检查入口：`/usr/local/sbin/pvz-renew-ssl.sh --dry-run --run-deploy-hooks --no-random-sleep-on-renew`。
站点级续期钩子：`/etc/letsencrypt/renewal-hooks/deploy/50-pvz-nginx`；只有该证书成功续期后才检查并重载 Nginx。
该次部署未修改任何 SSH 登录凭据，也未使用或公开宝塔接口密钥。

## 本地运行 / 更新

```sh
uv sync
uv run python tools/build_web.py
uv run python -m http.server 8787 --bind 127.0.0.1 --directory dist
```

访问 `http://127.0.0.1:8787/`。不要直接双击 HTML。`dist/` 可部署到静态 HTTPS 网站。
运行环境从 Pygbag 官方 CDN 加载；首次启动需要联网，不是完全离线版。

```sh
uv run python tools/test_migration.py
```

以上测试校验源码/素材一致性、五关场景、真实教学种植、单击加速、全部小游戏启动和存档；其中桌面版一致性对照需要同级目录 `../pypvz/` 中的对应桌面改版，单独克隆本仓库不会包含该对照目录。

不依赖桌面版对照目录的回归测试：

```sh
uv run python tools/test_campaign_clock.py
uv run python tools/test_chomper.py
node tools/test_audio_lifecycle.mjs
node tools/test_boot_lifecycle.mjs
```

2026-09-10 已在正式域名实测浏览器启动、第一关七步教学、中文、两种植物的真实种植，并检查横竖屏尺寸。
音频生命周期另有隔离测试；未声称在每种真实手机或浏览器上全部通关。
WebMCP 为支持浏览器提供读取游戏状态和选择卡片工具，不替代可见游戏操作。

## 来源

- 直接基于：[wszqkzqk/pypvz](https://github.com/wszqkzqk/pypvz)。原项目说明完整保留在 [UPSTREAM_README.md](UPSTREAM_README.md)。
- 原项目注明的上游：[marblexu/PythonPlantsVsZombies](https://github.com/marblexu/PythonPlantsVsZombies)，部分代码整合自 [callmebg/PythonPlantsVsZombies](https://github.com/callmebg/PythonPlantsVsZombies)。
- 本改版新增人物主题角色、素材、关卡与浏览器适配；原有代码和素材的归属不因此改变。

PvZ 素材归原权利人；人物图片来自用户，仅随本私有项目保存。保留原项目个人学习研究用途声明，不声称拥有原素材版权，也不为上游代码和素材另行授予许可。
