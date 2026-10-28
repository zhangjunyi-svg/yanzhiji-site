# 颜植季 YENCIGI 官网 · 优化方案

> 基于对仓库现有 7 个页面 / 30 个静态资源 / 30.5 MiB 产物的实测（数据均为本地实测，附复现命令）。
> 结论：**站点形态没错，问题不在"静态 HTML"，也不在"没上 React"。**

---

## 0. 三个判断，先说结论

| 你的判断 | 结论 | 理由 |
| --- | --- | --- |
| "全是静态资源的 HTML" | **这不是缺陷，是这个站的最优形态** | 全站 0 表单、0 接口、0 第三方脚本、0 运行时状态。纯静态是 LCP/SEO/成本三项最优解 |
| "要兼容对象存储" | **已经兼容了，今天就能传 COS** | 它就是一个静态目录。缺的不是"兼容"，是 6 项配置（MIME / 缓存头 / 压缩 / Range / 防盗链 / 刷新） |
| "用 React + TS 重构" | **现在没必要，且会让性能变差** | `main.js` 只有 1.4KB gzip，换成 React 至少 +45KB gzip 运行时，首屏从"HTML 到即见"变成"等 JS 解析完才见" |

**真正的性能瓶颈不在框架层，而在两个地方：**

1. **视频 29.1 MiB**（首页滚动到底的下载量），占站点产物 95%
2. **首页 HTML 里 12.5 KiB gzip 是可视化编辑器残留属性**（`data-page-node-id`），占首页压缩后体积的 57%

这两项修完，首页字节数下降约 75%，**不需要写一行 React**。

---

## 1. 现状体检（实测）

### 1.1 体积构成

| 类别 | 体积 | 说明 |
| --- | --- | --- |
| 视频 7 个 | **29.1 MiB** | 720×1280 / 30fps / 0.6–1.1 Mbps，已做 faststart（moov 前置，这点是对的） |
| 图片 23 个 | **1.3 MiB** | JPG，无 WebP/AVIF，无响应式尺寸 |
| HTML 7 页 | 144 KiB（gzip ≈ 51 KiB） | 首页单页 54.9 KiB raw / 21.8 KiB gzip |
| CSS 1 个 | 50 KiB（gzip 9.6 KiB） | 单文件全站共用 |
| JS 1 个 | 3.8 KiB（gzip 1.4 KiB） | 原生，无依赖 |
| **站点产物合计** | **30.5 MiB** | 仓库另有 31 MiB `.git`，不计入 |

> 30 MiB 的站点里，**95.4% 是视频**。这是全站唯一的量级问题。

### 1.2 用户实际下载量

| 页面 | 首屏 | 滚动到底 |
| --- | --- | --- |
| 首页 | HTML 21.8K + CSS 9.6K + JS 1.4K + 首图 105K ≈ **138 KiB** | **≈ 30.2 MiB**（6 支影片 + MCRF 视频自动播放） |
| 产品详情页 | ≈ 150 KiB | ≈ 3.7–5.5 MiB（影片需点击才加载，`preload="none"`，这点也是对的） |

按 1 万次完整浏览估算：**≈ 295 GB 流量落在视频上**。优化到 480p 后 ≈ 75 GB。

### 1.3 首页 HTML 的构成拆解

```
原始 56,185 B
├─ data-page-node-id 属性 568 个 ....... 24,424 B  ← 可视化编辑器（DM）导出残留
├─ 滚动字幕重复内容（claim-biz-track）.. 3,981 B  ← 同一串文字复制了 5 遍
├─ 编辑器内联 <style> 2 段 .............    ~300 B
└─ 真实内容 ........................... ~27,000 B
```

去掉编辑器残留后：

| | raw | gzip |
| --- | --- | --- |
| 现在 | 56,185 B（54.9 KiB） | **22,349 B（21.8 KiB）** |
| 清理后 | 31,335 B（30.6 KiB） | **9,573 B（9.3 KiB）** |

**gzip 后减少 57%（约 12.5 KiB）。** 原因是那 568 个随机 20 位 ID 几乎无法被压缩（每个约 120 bit 熵），相当于每访问一次首页就白传 12.5 KiB。

> 复现：`python3 -c "import re,gzip;s=open('index.html').read();t=re.sub(r'\s*data-page-node-id=\"[^\"]*\"','',s);print(len(gzip.compress(s.encode(),9)),len(gzip.compress(t.encode(),9)))"`

### 1.4 结构性问题清单

| # | 问题 | 影响 | 位置 |
| --- | --- | --- | --- |
| 1 | 首页 568 个 `data-page-node-id` + 2 段 `__dm_*` 内联样式 | +12.5 KiB gzip，暴露内部工具 | `index.html` |
| 2 | `id="channels"` 重复两次（section 与 footer） | HTML 无效，锚点行为不确定 | `index.html:425,489` |
| 3 | `<header class="site-header scrolled">` 硬编码 `scrolled` | 首屏顶部就带毛玻璃/阴影，滚动时闪一下 | 全部 7 页 |
| 4 | 首页 68 个 `.reveal` 中有 58 个硬编码了 `visible` | 首页入场动画实际**不执行**；而 PDP 是纯 `.reveal`（依赖 JS 加类） | `index.html` vs `product-*.html` |
| 5 | `.reveal { opacity: 0 }` + 靠 JS 加 `.visible` | **JS 失效/被拦截时，产品页正文整段不可见**；百度等不执行 JS 的抓取器可能拿到空白 | `style.css:421` |
| 6 | 页脚公司名不一致：首页"杭州丝妍科技有限公司" / 产品页"臻妍科技（杭州）有限公司" | 主体信息错误，合规风险 | 7 页 footer |
| 7 | 无 `og:` / `twitter:` / `canonical` / JSON-LD | 微信、小红书、微博分享时无卡片图，搜索无 Products 富摘要 | 全部 7 页 |
| 8 | 无 `robots.txt` / `sitemap.xml` | 收录效率低 | 根目录 |
| 9 | 大部分 `<img>` 无 `width/height`，容器也无 `aspect-ratio`（如 `.hero-visual img`） | CLS 偏高 | 多处 |
| 10 | 6 支影片在 3 列网格中可能同时自动播放 | 移动端 CPU/电量/解码占用高 | `main.js:66` |
| 11 | 产品卡片文案与详情页手工复制两份 | 改价/改文案需改两处，已出现不一致风险 | `index.html` ↔ `product-*.html` |

### 1.5 已经做对的地方（别改）

- 无 Web 字体，纯系统字体栈 → 零字体请求、零 FOIT
- 视频 `preload="none"` + `poster` + `IntersectionObserver` 进出视口播放/暂停
- 视频已 faststart（`moov` 在文件头，可边下边播）
- 图片 `loading="lazy"`（产品卡、推荐位）
- 语义化结构清晰（section/header/footer/figure/figcaption）
- 零第三方脚本（没有统计、没有客服挂件、没有字体 CDN）
- `vercel.json` 已配置安全响应头与资源缓存
- 已有响应式断点（1080 / 720）

---

## 2. 逐条回答你的两个提议

### 2.1 "全是静态 HTML" —— 不是问题，是优势

判断一个站点该不该上框架，看三件事：

| 维度 | 本站现状 | 需要框架的门槛 |
| --- | --- | --- |
| 数据来源 | 纯手写文案 | CMS / API / 数据库 |
| 交互状态 | 滚动动画、播放、复制口令 | 登录、购物车、筛选、搜索、表单提交 |
| 页面数量 | 7 页 | 20+ 页且结构高度同构 |
| 团队协作 | 单人 | 多人并行改同一批页面 |

本站四项全部落在"不需要"那一侧。**"静态"在这里不是技术债，是技术选型正确。**

### 2.2 对象存储 —— 已经兼容，缺的是配置

它就是一个 `index.html` + `assets/` 的目录，COS / OSS / R2 / S3 全都能直接放。**"上 React" 不会让它更兼容对象存储**，因为构建产物依旧是静态文件。

真正需要对齐的是这 6 件事（详见 §6）：

1. **MIME 映射**：COS 默认按扩展名推断，`.avif` / `.webp` / `.woff2` / `.mjs` 常被识别成 `application/octet-stream` → 浏览器不渲染
2. **缓存头**：对象元数据里的 `Cache-Control`，按文件类型分档（现在没有 hashed 文件名，所以 HTML 必须 `no-cache`）
3. **压缩**：COS 源站不压缩，必须在 CDN 开 Brotli/Gzip
4. **Range 回源**：视频拖动进度条依赖它
5. **防盗链**：29 MiB 视频是最容易被刷流量的对象
6. **发布与回滚**：`coscmd sync` + 目录刷新；没有 hashed 文件名时，回滚要连 HTML 一起刷

> 关键点：**COS 静态网站不支持 URL rewrite（SPA 兜底）**，只有"索引文档 + 错误文档"。
> 这直接决定了下面 2.3 的结论。

### 2.3 React + TS：没必要，而且更慢

#### 四种形态的实测/测算对比（首页）

| 形态 | HTML(gzip) | JS(gzip) | 首屏 LCP | COS 兼容 | 百度收录 |
| --- | --- | --- | --- | --- | --- |
| **现状（纯静态）** | 21.8 KiB | 1.4 KiB | 基线 | ✅ 直接放 | ✅ |
| 现状 + 清理编辑器残留 | **9.3 KiB** | 1.4 KiB | **−100~200ms** | ✅ | ✅ |
| Astro / 11ty 静态生成（SSG） | ~10 KB | 0–2 KB | 持平 | ✅ 需目录式路由 | ✅ |
| Next.js `output: export` | ~12 KB | ~90 KB | +100~300ms | ✅ 需 `trailingSlash` | ✅ |
| **React SPA（Vite/CRA）** | ~1 KB | **~48 KB** | **+600~1500ms** | ❌ 需 CDN 重写 | ⚠️ 差 |

#### 为什么 SPA 在这个站上必然更慢（三个机制，不是猜测）

1. **首屏被 JS 锁死**
   现在是"HTML 到 → 文字可见"。SPA 是"HTML 到（空 `#root`）→ 下载 48KB JS → 解析 → 执行 → 才出现第一行字"。
   4G + 中端安卓机上，这一跳就是 0.6–1.5s 的 LCP 损失。而本站**首屏就是品牌主张文字**，是 LCP 元素本身。

2. **对象存储没有 rewrite**
   `product-toner.html` 是 7 个独立文件，COS 直接按路径命中。React Router 的 `/product/toner` 在 COS 上要么 404，要么用"错误文档 → index.html"兜底 —— 而错误文档会返回 **404 状态码**，搜索引擎直接判定死链。要救只能上 CDN 的 URL 重写（腾讯云 CDN 支持，但属额外链路，且仍不如真静态稳）。

3. **SEO 与分享卡片**
   品牌官网的核心 KPI 是"搜品牌名能搜到、分享出去有卡片"。CSR 交付的是空壳 HTML，百度对这种结构的收录质量长期不如静态 HTML。而这段内容是营销资产，不是应用界面。

#### React 的真正收益在什么条件下成立

不是"不能用 React"，而是"这四条至少命中两条才划算"：

- [ ] 未来 12 个月要接 **CMS / 商城 / 会员**（内容需要接口驱动）
- [ ] 页面数量要涨到 **20+**，且大量重复结构（如 SKU 从 6 个到 60 个）
- [ ] 需要**真正的应用状态**（购物车、筛选、搜索、登录）
- [ ] 团队现有成员**都是 React 技术栈**，维护成本比"静态 HTML + 构建脚本"更低

目前命中 0 条。**其中第 2 条最可能先发生** —— 一旦产品线扩张，这时也不是"上 React"，而是"上 SSG + 内容集合"。

#### TS 可以单独拿走，且值得

把产品/成分/功效数据从 HTML 里抽出来，用 TS 定义并由构建期校验，收益是真实的：

```ts
// src/data/products.ts
export type Product = {
  slug: string;
  name: string;
  en: string;
  tag: string;
  price: number;
  spec: string;
  lede: string;
  texture: { image: string; lead: string; features: string[] };
  efficacy: { value: string; label: string; source: string }[];
  formula: { core: string; main: { name: string; desc: string }[]; extra: string[] };
  film: { mp4: string; poster: string };
};
```

`index.html` 的产品卡和 6 个 PDP 都从同一份数据渲染 → 彻底消灭 §1.4 第 11 条的手工双写。**这不需要 React，只需要一个构建步骤。**

---

## 3. 真正该做的优化（按 ROI 排序）

### P0-1 · 视频压缩：29.1 MiB → 7.3 MiB（−75%）

实测（`ffmpeg`，同一素材重编码）：

| 素材 | 现状 | 720p CRF27 | 480p CRF30 |
| --- | --- | --- | --- |
| v-lotion.mp4 | 4,973 KiB | 3,210 KiB（−35%） | **1,229 KiB（−75%）** |
| v-toner.mp4 | 2,739 KiB | — | **581 KiB（−79%）** |

按 6 支网格片 × 480p + MCRF 片 × 720p 推算：**29.1 MiB → 9.6 MiB**；全部 480p 则 **→ 7.3 MiB**。

策略：

- **网格内 6 支影片** → 480×854，CRF 30，`-preset slow`，保留 `+faststart`
  （网格内单卡宽度约 380–420px，480p 在 2x 屏上足够）
- **MCRF 大屏视频 + PDP 单支影片** → 720×1280，CRF 27（若要极致，也压到 480p）
- 音轨：默认静音的网格片 → `-an`；需要"开启声音"的 → AAC 64k mono
- 进阶（可选）：追加 AV1 或 HEVC 版本，用 `<source>` 降级；先做 h264 收益已达 75%

```bash
# 网格版（无声，480p）
ffmpeg -i v-toner.mp4 -vf scale=480:-2 -c:v libx264 -crf 30 -preset slow \
  -pix_fmt yuv420p -movflags +faststart -an v-toner.480.mp4

# 大屏版（有声音，720p）
ffmpeg -i v-mcrf.mp4 -c:v libx264 -crf 27 -preset slow -pix_fmt yuv420p \
  -c:a aac -b:a 64k -ac 1 -movflags +faststart v-mcrf.720.mp4
```

### P0-2 · 清理编辑器残留：21.8 KiB → 9.3 KiB（−57%）

```bash
# 1. 删除所有 data-page-node-id
perl -pi -e 's/\s*data-page-node-id="[^"]*"//g' index.html
# 2. 删除 __dm_* 内联样式块
perl -0pi -e 's/<style id="__dm_[^>]*>.*?<\/style>//gs' index.html
```

同时删掉 `claim-biz-track` 里 5 遍重复的滚动字幕（保留 2 遍，CSS `translateX(-50%)` 只需两份即可无缝循环）→ 再省 ~2.4KB。

### P0-3 · 图片：1.3 MiB → ~0.6 MiB

实测（`ffmpeg libaom-av1`）：

| 素材 | 现状 JPG | AVIF CRF25/30 | 降幅 |
| --- | --- | --- | --- |
| hero-products.jpg (1490×846) | 105 KB | **20 KB** | −81% |
| p-toner.jpg (900×900) | 46 KB | **15 KB** | −67% |

做法：

- 用 `<picture>` 提供 AVIF → WebP → JPG 三级降级（Safari 16.4+ 支持 AVIF，WebP 全覆盖）
- 海报图（7 张，合计 **488 KB**）按 480px 宽重出，仅此一项省约 350KB
- 为所有 `<img>` 补 `width/height`，或给容器加 `aspect-ratio` → CLS 归零
- 首图 `<link rel="preload" as="image" imagesrcset=...>` 提前 1 个 RTT

### P0-4 · 首屏关键路径

- 首页 `/assets/hero-products.jpg` 加 `fetchpriority="high"` + preload
- 7 张 `poster` 改为"占位图 + 进入视口再挂 `poster`"（否则 488KB 会在页面加载时就请求）
- 去掉硬编码的 `class="... scrolled"`，交还 JS 控制
- `.reveal` 改为**默认可见、JS 加动画类**（`html.js .reveal{opacity:0}`），保证无 JS 时内容可读

### P0-5 · 缓存与压缩

| 资源 | 现在 | 建议 |
| --- | --- | --- |
| `*.html` | Vercel 默认 / CDN 0 缓存 | `public, max-age=0, s-maxage=300, stale-while-revalidate=86400` + 发布后刷新 |
| `assets/*` | `max-age=86400`（1 天，无 hash） | 引入 hash 后 `public, max-age=31536000, immutable` |
| 视频 / 大图 | 同 assets | `public, max-age=2592000` |
| 压缩 | 依赖平台 | CDN 显式开启 Brotli；确认 `text/html`、`text/css`、`js`、`svg` 被压缩 |

> `max-age=86400` + 无 hash 文件名 = 改了图，用户最多看 24 小时旧版。这是当前配置最实际的坑。

### P1 · 结构：加一层薄构建（3–5 天）

解决的是**维护成本**，不是性能：

- `header` / `footer` 7 处重复 → 1 个组件
- 产品数据双写 → 1 份 `products.ts`
- 资源加 hash → 可以放心上 immutable 缓存
- 按页裁剪 CSS（首页独享 21KB，PDP 独享 23KB，现在两边都全量加载 50KB）
- 自动生成 `sitemap.xml` / `robots.txt` / `og` 标签

---

## 4. 方案选型（三档，按需选一）

### 方案 A · 保持纯静态 + 60 行构建脚本（成本最低）

```
src/
  partials/header.html  partials/footer.html
  data/products.ts
  pages/index.html  pages/product-toner.html ...
scripts/build.mjs        # 替换占位符 + 压缩 HTML/CSS + hash + sitemap
dist/                    # 上传到 COS 的目录
```

- 依赖：`esbuild`（可选）、`sharp`/`ffmpeg`（图片视频）、Node 内置
- 优点：产物与今天完全一致，零运行时；团队无需学新东西
- 缺点：模板能力弱，复杂布局靠手工 include

### 方案 B · Astro + TypeScript（推荐，若确定要做组件化）

```astro
---
// src/pages/product/[slug].astro
import Layout from '../../layouts/Layout.astro';
import { products } from '../../data/products';
export function getStaticPaths() {
  return products.map((p) => ({ params: { slug: p.slug }, props: { p } }));
}
const { p } = Astro.props;
---
<Layout title={`${p.name} — 颜植季 YENCIGI`} description={p.lede}>
  <ProductHero product={p} />
  <EfficacyGrid items={p.efficacy} />
</Layout>
```

`astro.config.mjs`：

```js
export default {
  output: 'static',
  trailingSlash: 'always',        // → product/toner/index.html，COS 目录索引直接命中
  build: { format: 'directory' },
  vite: { build: { assetsInlineLimit: 0 } }
};
```

- 默认**输出零 JS**，只对需要交互的段落用 `<script>`（就是现在的 `main.js`，原样搬）
- `astro:assets` 构建期自动产出 AVIF/WebP + `srcset` → P0-3 免费完成
- 组件化消灭 7 处 header/footer 重复
- 学习成本：`.astro` 文件 ≈ HTML + frontmatter + `{}` 插值，会 HTML 就能写

### 方案 C · Next.js 静态导出（仅当 12 个月内要接 CMS/商城）

```js
// next.config.js
module.exports = { output: 'export', trailingSlash: true, images: { unoptimized: true } };
```

- 必须 `unoptimized: true`（对象存储没有 `/_next/image` 服务）→ 图片优化要自己做
- 首屏多 ~90KB gzip 的 hydration 运行时，换来的是你现在用不到的能力
- **只在命中 §2.3 四个条件中的两条以上时才选**

### 明确不推荐

- ❌ **React SPA（Vite + React Router）**：COS 无 rewrite、SEO 差、LCP 退化，三项全踩
- ❌ **CRA**：已停止维护
- ❌ 为了"看起来现代"而引入状态管理 / UI 组件库（本站 0 个交互组件需要它）

---

## 5. 落地路线图

| 阶段 | 内容 | 工期 | 预期收益 | 风险 |
| --- | --- | --- | --- | --- |
| **P0 今天就能做** | 视频转码、清编辑器残留、图片 AVIF、补 meta/og/sitemap、修 §8 的 bug | **0.5–1 天** | 首页 **30.2 → 7.3–9.6 MiB**；HTML gzip **21.8→9.3 KiB**；图片 **1.3→0.6 MiB** | 极低，纯产物替换 |
| **P1 一周内** | 加薄构建（方案 A 或 B）、数据抽 `products.ts`、hash + immutable、CSS 分页 | 3–5 天 | 改一处全站生效；缓存命中率提升；CSS 每页少 40% | 低，可灰度 |
| **P2 按需** | CMS（内容运营自助）、多语言、结构化数据、A/B | 按需求 | 运营效率 | 中 |

### 只做三件事的版本

1. **转视频到 480p**（−21.8 MiB，占全部收益的 90%）
2. **清 `data-page-node-id`**（首页 gzip −57%）
3. **给 HTML 补 `og` + `sitemap.xml` + 修重复 `id`**（分享与收录）

一个下午，首页从 30.2 MiB 降到 7.3–9.6 MiB（**−68~76%**），LCP 预计 −0.3~0.6s。

---

## 6. 对象存储落地清单（腾讯云 COS + CDN）

### 6.1 桶与静态网站

1. 桶权限：**公有读私有写**
2. 开启「静态网站」：索引文档 `index.html`，错误文档 `404.html`，强制 HTTPS
3. **必须绑定自定义域名**（部分厂商默认域名对 HTML 会触发下载行为，且无法配 HTTPS 证书）
4. 中国大陆加速需 **ICP 备案**

### 6.2 MIME 类型（最容易踩的坑）

COS 按扩展名推断，以下必须在控制台「文件类型映射」补齐，或上传时 `--mimetype` 显式指定：

| 扩展名 | Content-Type |
| --- | --- |
| `.avif` | `image/avif` |
| `.webp` | `image/webp` |
| `.woff2` | `font/woff2` |
| `.mjs` | `text/javascript; charset=utf-8` |
| `.json` | `application/json` |
| `.svg` | `image/svg+xml` |
| `.mp4` | `video/mp4` |
| `.xml` | `application/xml` |

漏配 `.avif` → 浏览器拿到 `application/octet-stream` → 图片直接裂开。

### 6.3 缓存头（对象元数据）

| 路径 | Cache-Control |
| --- | --- |
| `/*.html` | `public, max-age=0, s-maxage=300, stale-while-revalidate=86400` |
| `/assets/**`（有 hash） | `public, max-age=31536000, immutable` |
| `/assets/media/**`（图/视频） | `public, max-age=2592000` |
| `/robots.txt` `/sitemap.xml` | `public, max-age=3600` |

```bash
# 上传时按类型设头（coscmd 支持 -H 传对象元数据）
coscmd upload -rs dist/ / && \
coscmd upload -r -H '{"Cache-Control":"public, max-age=0, s-maxage=300"}' dist/*.html / && \
coscmd upload -r -H '{"Cache-Control":"public, max-age=31536000, immutable"}' dist/assets/*.css dist/assets/*.js /assets/
```

### 6.4 CDN 必开项

| 配置 | 值 | 为什么 |
| --- | --- | --- |
| 智能压缩 / Brotli | 开（`text/*`、`js`、`json`、`svg`） | COS 源站不压缩，不开等于白传 3 倍文本 |
| Range 回源 | 开 | 视频拖进度条 |
| 分片回源 | 开（>10MB） | 大视频首帧更快 |
| HTTP/3 / QUIC | 开 | 移动端弱网收益明显 |
| TLS 最低版本 | 1.2 | 合规 |
| 缓存键 | 只按 URL，忽略 Cookie/Header | 提高命中率 |
| 防盗链 | Referer 白名单（含空 Referer 策略）+ 可签发 URL | 29 MiB 视频被刷流量代价最高 |
| 发布后刷新 | 目录刷新 `/` + `/*.html` | 无 hash 时的必需动作 |

### 6.5 关键限制（决定架构）

> **COS 静态网站不支持 URL rewrite**，只有索引文档 + 错误文档。
> 因此：**多页目录式路由**（`product/toner/index.html`）是唯一在 COS 上"零妥协"的路由方案。
> React SPA 想在这跑，只能靠 CDN 重写或"错误文档返回 404"兜底 —— 后者直接损害 SEO。

所以 `astro.config` 的 `trailingSlash: 'always'` / `next.config` 的 `trailingSlash: true` 不是可选项，是**对象存储兼容性的前提**。

### 6.6 发布流程（GitHub Actions 骨架）

```yaml
- run: pnpm build
- run: pip install coscmd
- run: |
    coscmd config -a ${{ secrets.COS_ID }} -s ${{ secrets.COS_KEY }} \
      -b ${{ secrets.COS_BUCKET }} -r ap-guangzhou
    coscmd upload -rs dist/ /
- run: |
    # 刷新 CDN：目录刷新 + 根
    curl -s "https://cdn.api.qcloud.com/v2/index.php?..." 
```

回滚：保留上一版 `dist/` 的 COS 前缀（`/v20261028/`）或直接对象版本控制。

---

## 7. 验收指标

| 指标 | 现状（估算） | 目标 |
| --- | --- | --- |
| 首页首屏传输 | ~138 KiB | **< 120 KiB** |
| 首页滚动到底 | **30.2 MiB** | **< 10 MiB** |
| 首页 HTML（gzip） | 21.8 KiB | **< 10 KiB** |
| LCP（4G / 中端安卓） | 基线 | **< 2.5s** |
| CLS | 有跳变（首图无尺寸） | **< 0.1** |
| Lighthouse 移动端性能 | 待测 | **≥ 90** |
| 百度/微信抓取正文可见 | 产品页依赖 JS ⚠️ | **纯 HTML 可见** |
| 万次完整浏览流量 | **≈ 295 GB** | **≈ 75 GB** |

测量方法：

```bash
# 本地基线（无工具时用 curl 估体积）
curl -s -H 'Accept-Encoding: gzip' -o /dev/null -w '%{size_download} %{time_total}\n' http://localhost:8899/

# 有 Chrome 时
npx lighthouse http://localhost:8899 --preset=desktop --only-categories=performance,seo
npx lighthouse http://localhost:8899 --form-factor=mobile --throttling.cpuSlowdownMultiplier=4
```

---

## 8. 附：Bug 清单（与性能无关，但应一起修）

| # | 问题 | 修法 |
| --- | --- | --- |
| 1 | `id="channels"` 出现两次 | footer 改成 `id="footer"`，导航锚点指向 section |
| 2 | 公司主体名不一致（丝妍 vs 臻妍） | 统一为工商注册全称，7 处 |
| 3 | header 硬编码 `scrolled` | 删除，由 `main.js` 首次调用 `onScroll()` 决定 |
| 4 | 首页 `.reveal` 混入 `visible`、PDP 全部依赖 JS | 统一策略：`html.js .reveal{opacity:0}` + JS 加 `.visible` |
| 5 | 产品页 `<li class='reveal'>` 用单引号 | 统一双引号，避免格式化工具反复改动 |
| 6 | `claim-biz-track` 内容重复 5 遍 | 保留 2 遍 |
| 7 | `video` 缺 `aria-label` / `disablepictureinpicture` | 补上 |
| 8 | 无 `og:image`（1200×630） | 用 hero 图裁一张 |

---

## 9. 一句话总结

> 你的直觉有一半是对的：这个站确实"太静态了"——但问题不是静态，而是**静态产物没做过工程化处理**：编辑器残留白传 12.5 KiB、29 MiB 视频原样上线、7 个页面手工同步。
> 这些用**构建步骤 + 资源压缩 + COS/CDN 配置**就能全部解决，**不需要 React**。
> 真要上组件框架，选 **Astro（静态输出、零运行时）**，而不是 React SPA —— 后者在对象存储上没有 rewrite、在 SEO 上没有 HTML、在首屏上多 45KB 运行时，三项都是净损失。
