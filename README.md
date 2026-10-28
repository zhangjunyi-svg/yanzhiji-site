# 颜植季 YENCIGI · 品牌官网

> 中国医用蚕丝材料先行者 —— 医疗器械 · 医疗美容 · 功效护肤 · 核心原料

品牌官网静态站点，纯 HTML/CSS/JS 实现，无构建步骤、无框架依赖，可直接托管于任意静态托管平台。

## 页面结构

| 文件 | 内容 |
| --- | --- |
| `index.html` | 首页（首屏、品牌宣言、品牌理念、蚕丝简史、MCRF 科技、产品系列、产品影像、官方渠道、页脚） |
| `product-toner.html` | 焕能悦活修护水 |
| `product-lotion.html` | 焕能悦颜修护乳 |
| `product-cream.html` | 焕能菁华修护霜 |
| `product-serum.html` | 焕能舒润调理精华液 |
| `product-cleanser.html` | 焕颜净澈洁面慕斯 |
| `product-mask.html` | 焕能沁润凝萃面膜 |
| `style.css` | 全站样式（含响应式 1080 / 720 断点） |
| `main.js` | 滚动揭示动画、数字计数、视频滚动播放、口令复制 |
| `assets/` | 产品图、质地图、科学图、品牌 Logo、7 支短视频及封面 |

## 本地预览

```bash
# 任选其一，任一起静态服务器即可（不要用 file:// 直接打开，视频与字体需要 http）
python3 -m http.server 8899
# 或
npx serve .
```

浏览器打开 http://localhost:8899 。

## 视觉规范

- 主色：薰衣草紫 `#7A5FC0` / 深紫 `#43356B` / 暖米白 `#FAF9F7`
- 标题：衬线宋体；编号与英文索引：Didone 斜体
- 段落：正文灰紫、宽字距，信息密度克制

## 部署

### Vercel（推荐用于预览 / 海外访问）

仓库已包含 `vercel.json`，导入 GitHub 仓库后无需任何构建配置：

- Framework Preset：**Other**
- Build Command：留空
- Output Directory：留空（默认根目录）
- 之后每次 `git push` 自动重新部署

自定义域名：Vercel 项目 → Settings → Domains → 添加域名，按提示在 DNS 服务商配置记录
（根域名 `A 76.76.21.21`，或子域名 `CNAME cname.vercel-dns.com`）。

> 注意：Vercel 节点在境外，**中国大陆访问速度不稳定**，正式对外建议配合国内 CDN 或国内静态托管。

### 腾讯云 COS + CDN（推荐用于中国大陆正式访问）

1. 创建 **COS 存储桶**，权限设为「公有读私有写」，开启「静态网站」功能（默认索引 `index.html`）
2. 将本仓库所有文件上传至存储桶根目录（可用 `coscmd` / 控制台拖拽 / CI 同步）
3. 创建 **CDN 加速域名**，源站选择该 COS 桶，回源协议 HTTPS
4. 域名需完成 **ICP 备案**后方可启用 CDN 加速
5. CDN 配置「缓存过期时间」：`*.html` 设为 0（不缓存），`assets/*` 设为 7 天

### 双线加速（国内 + 海外都快的方案）

DNS 分线路解析（云解析支持「境内 / 境外」分流）：

- 境外线路 → CNAME 到 Vercel
- 境内线路 → CNAME 到腾讯云 CDN

同一域名，国内用户走 CDN、海外用户走 Vercel，两端都是本地就近节点。

## 许可

品牌视觉素材版权归杭州丝妍科技有限公司所有，仅供本项目使用。
