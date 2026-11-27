# 颜植季 YENCIGI 官网交接文档

> 整理日期：2026-11-27。本文所列状态均在当天核实：线上文件与 GitHub `main` 分支（提交 `5ac116a`）逐字节一致。

## 1. 一览

| 项目 | 内容 |
| --- | --- |
| 官网地址 | https://www.yencigi.com （主站，规范地址带 www） |
| 裸域 | `yencigi.com`，HTTP / HTTPS 都 301 跳转到 `https://www.yencigi.com` |
| 运营主体 | 杭州丝妍科技有限公司 |
| ICP 备案号 | 浙ICP备2026096837号-1（页脚已展示，链接到 beian.miit.gov.cn） |
| 公安联网备案 | **未办理**，页脚已留隐藏位置（见第 6 节） |
| GitHub 仓库 | https://github.com/zhangjunyi-svg/yanzhiji-site （SSH：`git@github.com:zhangjunyi-svg/yanzhiji-site.git`） |
| 生产分支 | `main` |
| 服务器 | 阿里云 ECS `121.196.152.156`（杭州） |
| 技术形态 | 纯静态站点（HTML + CSS + 原生 JS），无构建步骤、无数据库、无后端 |

## 2. 服务器

| 项目 | 内容 |
| --- | --- |
| 云厂商 / 地域 | 阿里云 ECS，华东 1（杭州）可用区 B（cn-hangzhou-b） |
| 实例 ID | `i-bp1ecxou55n3kfeyrkpe` |
| 公网 IP | `121.196.152.156` |
| 系统 | Ubuntu 22.04.5 LTS |
| 磁盘 | 系统盘 40G，已用约 10% |
| 登录方式 | `ssh root@121.196.152.156`，使用 SSH 密钥免密登录。交接时把接手人的公钥加入服务器 `/root/.ssh/authorized_keys`，不要传递私钥 |
| 安全组 | 需放行 TCP 22（SSH）、80、443 |
| Web 服务 | nginx 1.18，开机自启 |

### 关键路径

| 用途 | 路径 |
| --- | --- |
| 网站根目录 | `/var/www/yanzhiji-site`（属主 `www-data`） |
| nginx 站点配置 | `/etc/nginx/sites-available/yanzhiji-site`（已软链到 `sites-enabled`，默认站点已删除） |
| 公共静态规则 | `/etc/nginx/snippets/yanzhiji-site.conf`（根目录、gzip、安全头、缓存、404 页） |
| HTTPS 证书 | `/etc/letsencrypt/live/www.yencigi.com/` |
| 证书验证目录 | `/var/www/yanzhiji-site/.well-known/acme-challenge/`（**部署时不能删**） |

### nginx 结构

- 80 端口默认站：IP 直接访问时也能打开网站，同时作为证书验证的兜底。
- 80 端口域名：`www` 和裸域统一 301 到 `https://www.yencigi.com`，保留证书验证路径。
- 443 裸域：301 到 www 主站。
- 443 www 主站：HTTP/2、TLS 1.2/1.3、HSTS 一年。
- 缓存：图片 / 视频 / 字体 7 天，CSS / JS 1 天，HTML 不缓存；不存在的页面返回自定义 `404.html`。
- `/etc/nginx/mime.types` 已注册 `image/avif`。

### HTTPS 证书

- Let's Encrypt，覆盖 `www.yencigi.com` 和 `yencigi.com`，webroot 方式签发。
- 当前证书到期：**2027-02-16**；`certbot.timer` 已启用，会在到期前自动续期（2026-11-19 演练续期成功）。
- 查看状态：`ssh root@121.196.152.156 'certbot certificates; systemctl status certbot.timer'`

## 3. 域名

- 域名：`yencigi.com`，解析记录 `www` 和 `@` 都是 A 记录，指向 `121.196.152.156`。
- ICP 备案已完成（浙ICP备2026096837号-1）。**换服务器时只能换到已接入该备案的阿里云资源，迁到其他云厂商需要先办理备案接入。**
- 域名注册商账号与 DNS 控制台：<!-- 待填：注册商（如阿里云万网）、账号归属人 -->**待填**。

## 4. 仓库与部署内容

### 目录

| 文件 | 说明 | 是否上线 |
| --- | --- | --- |
| `index.html` | 首页（品牌理念、蚕丝简史、MCRF 科技、产品系列、产品影像、官方渠道） | 是 |
| `product-toner.html` 等 6 个 | 产品详情页：修护水、修护乳、修护霜、精华液、洁面慕斯、面膜 | 是 |
| `404.html` | 自定义 404 页（`noindex`） | 是 |
| `style.css` / `main.js` | 全站样式与交互脚本 | 是 |
| `assets/` | 图片（JPG/WebP/AVIF）、产品视频、OG 分享图、图标，共 56 个文件约 12MB | 是 |
| `robots.txt` / `sitemap.xml` | 爬虫规则与站点地图（7 个页面） | 是 |
| `scripts/` | 图片 / 视频压缩脚本、百度推送脚本 | 否 |
| `README.md` / `OPTIMIZATION-PLAN.md` / `HANDOVER.md` | 文档 | 否 |
| `vercel.json` | Vercel 托管配置（备用，生产环境未使用） | 否 |

### 提交历史要点

| 提交 | 内容 |
| --- | --- |
| `1732015` | 官网首版 |
| `7ed208e` / `42a8185` | 性能优化：视频降到 480p、图片生成 AVIF、`<picture>` 加载、SEO 基础、404 页 |
| `07ff7ed` / `e713499` | 统一公司主体名、页脚整理 |
| `98cc05d` | 全站 SEO、结构化数据、OG 分享图、ICP 备案号（PR #1 合并） |
| `523e762` | 百度 SEO 强化、公安备案预留位、百度推送脚本（PR #2 合并，当前线上版本） |

### 已完成的 SEO

- 每页独立的标题、描述、关键词；产品页标题含品类词。
- `canonical`、Open Graph / Twitter 分享卡片、JSON-LD 结构化数据（Organization、WebSite、Product）。
- 百度专用：禁止转码（`no-transform` / `no-siteapp`）、PC 与移动适配声明（`applicable-device`）。
- `robots.txt` 放行百度蜘蛛，屏蔽 `scripts/` 和 `.md`；`sitemap.xml` 含 7 个页面。
- 百度站点验证、百度统计代码以注释形式预留（见第 6 节）。

## 5. 如何更新上线

在本机仓库根目录执行（rsync 只传有变化的文件）：

```bash
git checkout main && git pull --ff-only origin main
```

先预演，确认将要变更的文件：

```bash
rsync -azni --delete --exclude '.git' --exclude '.gitignore' --exclude '.well-known' --exclude 'vercel.json' --exclude 'scripts/' --exclude '*.md' ./ root@121.196.152.156:/var/www/yanzhiji-site/
```

确认无误后正式同步并修正权限：

```bash
rsync -azi --delete --exclude '.git' --exclude '.gitignore' --exclude '.well-known' --exclude 'vercel.json' --exclude 'scripts/' --exclude '*.md' ./ root@121.196.152.156:/var/www/yanzhiji-site/ && ssh root@121.196.152.156 'chown -R www-data:www-data /var/www/yanzhiji-site'
```

注意事项：

- **必须排除 `.well-known`**，否则 `--delete` 会删掉证书验证目录，导致 HTTPS 证书续期失败。
- 只从 `main` 部署。改动先走分支和 PR，合并后再上线，避免线上与仓库不一致。
- 改了页面后，更新 `sitemap.xml` 中对应页面的 `<lastmod>`，并运行一次百度推送脚本。
- 修改 nginx 配置后先执行 `nginx -t` 检查，再 `systemctl reload nginx`。

## 6. 待办事项

### 需要尽快处理

- [ ] **公安联网备案**：网站开通后 30 日内到 [beian.mps.gov.cn](https://beian.mps.gov.cn/) 办理。拿到编号后，在 8 个页面页脚的 `.footer-psb` 处替换两处 `33010XXXXXXXXX`，删除该行和前面分隔符上的 `hidden`；如需官方图标，存为 `assets/beian-psb.png`（页面注释里有现成代码）。
- [ ] **核对 ICP 备案号**：到 [beian.miit.gov.cn](https://beian.miit.gov.cn/) 确认 `浙ICP备2026096837号-1` 与实际备案一致（该号码由早先的会话写入，未找到原始来源）。
- [ ] **百度搜索资源平台**：在 [ziyuan.baidu.com](https://ziyuan.baidu.com/) 添加 `https://www.yencigi.com`（HTTPS），选「HTML 标签验证」，把验证码填进 `index.html` 头部的 `baidu-site-verification` 并取消注释，部署后点验证。
- [ ] **提交 sitemap**：平台 → 普通收录 → sitemap，提交 `https://www.yencigi.com/sitemap.xml`。
- [ ] **主动推送**：平台 → 普通收录 → API 提交，取得 token 后运行 `BAIDU_TOKEN=你的token ./scripts/baidu-push.sh`。

### 可选 / 后续

- [ ] **百度统计**：在 [tongji.baidu.com](https://tongji.baidu.com/) 新增站点，把各页 `</head>` 前注释块里的 `YOUR_HM_ID` 换成实际 ID 并取消注释。
- [ ] **观察收录**：新站一般 1～4 周开始收录，在百度搜索资源平台「索引量」中查看。
- [ ] **页脚信息**：地址目前只写到「浙江省杭州市西湖区」，可补充完整地址与联系方式；页脚「官方渠道」链接目前都指向首页的渠道区块，若有各平台店铺链接可替换。
- [ ] **清理旧分支**：`feat/perf-p0`、`feat/baidu-seo` 都已合并，可在 GitHub 上删除。
- [ ] **服务器安全**：目前用 root 直接登录，建议改为普通用户 + sudo，并关闭 SSH 密码登录。
- [ ] **账号归属**：把阿里云账号、域名注册商、GitHub 仓库、百度平台账号的归属人与登录方式记录到公司内部（不要写进本仓库）。

## 7. 常用检查命令

线上各页面与爬虫文件是否正常：

```bash
for p in / /product-toner.html /robots.txt /sitemap.xml /no-such-page; do curl -s -o /dev/null -w "$p %{http_code}\n" https://www.yencigi.com$p; done
```

服务器上的文件是否与本地 `main` 一致（无输出即一致）：

```bash
rsync -azni --checksum --delete --exclude '.git' --exclude '.gitignore' --exclude '.well-known' --exclude 'vercel.json' --exclude 'scripts/' --exclude '*.md' ./ root@121.196.152.156:/var/www/yanzhiji-site/ | grep -v '^\.'
```

> 若本机开了代理软件（DNS 解析出 `198.18.x.x`），`curl http://www.yencigi.com` 可能返回空响应，属于代理问题，不是网站故障；关闭代理或在服务器上测试即可。
