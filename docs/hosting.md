# Hosting Notes / 托管说明

Operational details retained from the previous README. These describe the existing deployment; they are not prerequisites for running the project locally.

以下信息从原 README 移入，记录现有部署，不是本地运行的前置条件。

| Item / 项目 | Existing setup / 现有配置 |
| --- | --- |
| Site / 正式站点 | <https://pvz.rosebeg.com/> |
| Hosting / 托管 | Owner-managed BaoTa / Nginx server / 用户自有宝塔与 Nginx 服务器 |
| Static root / 静态根目录 | `/www/wwwroot/pvz.rosebeg.com/current` |
| TLS certificate / 证书 | Let's Encrypt |
| Renewal timer / 自动续期 | `certbot-renew.timer` |
| Deploy hook / 续期钩子 | `/etc/letsencrypt/renewal-hooks/deploy/50-pvz-nginx` |

Manual renewal check on the server / 在服务器上人工检查续期：

```sh
/usr/local/sbin/pvz-renew-ssl.sh --dry-run --run-deploy-hooks --no-random-sleep-on-renew
```

The site-specific hook checks and reloads Nginx only after successful renewal of this certificate. The original deployment notes state that SSH login credentials were unchanged and no BaoTa API key was used or disclosed.

站点级钩子仅在该证书成功续期后检查并重载 Nginx。原部署记录注明：未修改 SSH 登录凭据，未使用或公开宝塔接口密钥。

For a separate deployment, build the project and serve the contents of `dist/` from a static HTTPS host. The browser loads its runtime from Pygbag's CDN, so the first launch is not fully offline. See the [English README](../README.md#quickstart) or [中文说明](../README.zh-CN.md#快速开始) for local build commands.

另行部署时，构建项目并使用静态 HTTPS 服务托管 `dist/` 中的文件。浏览器运行环境来自 Pygbag CDN，首次启动不是完全离线的；本地构建命令见上述 README。
