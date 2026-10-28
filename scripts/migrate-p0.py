#!/usr/bin/env python3
"""P0 迁移脚本：HTML 清理 + <picture> + meta + .reveal 策略。

可重复执行（幂等）。若某个替换的命中数与预期不符，会直接报错退出，
避免"以为改了其实没改"。
"""
import os
import re
import sys

SITE = "https://www.yencigi.com"  # TODO: 换成正式域名后重跑本脚本
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PAGES = {
    "index.html": {
        "title": "颜植季 YENCIGI — 原生修护，减少反复",
        "desc": "颜植季 YENCIGI，再生医学与美学护肤成果。以自研 MCRF 丝素蛋白为核心，"
                "潜心专研国人敏弱屏障问题。全系无酒精、无香精、无防腐剂。",
        "url": "/",
        "og_image": "assets/hero-products.jpg",
        "is_home": True,
    },
}
for slug, name in [
    ("toner", "焕能悦活修护水"),
    ("lotion", "焕能悦颜修护乳"),
    ("cream", "焕能菁华修护霜"),
    ("serum", "焕能舒润调理精华液"),
    ("cleanser", "焕颜净澈洁面慕斯"),
    ("mask", "焕能沁润凝萃面膜"),
]:
    PAGES[f"product-{slug}.html"] = {
        "url": f"/product-{slug}.html",
        "product": slug,
        "og_image": f"assets/p-{slug}.jpg",
    }


# ---------- 工具 ----------
def jpeg_size(path):
    """不依赖 PIL：从 SOF 段读 JPEG 尺寸。"""
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
            h = int.from_bytes(data[i + 5:i + 7], "big")
            w = int.from_bytes(data[i + 7:i + 9], "big")
            return w, h
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg = int.from_bytes(data[i + 2:i + 4], "big")
        i += 2 + seg
    return None


def png_size(path):
    with open(path, "rb") as f:
        data = f.read(33)
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def img_size(path):
    if path.endswith(".png"):
        return png_size(path)
    if path.endswith(".jpg"):
        return jpeg_size(path)
    return None


def sub_exact(html, old, new, count, label):
    n = html.count(old)
    if n != count:
        sys.exit(f"[FAIL] {label}: 预期 {count} 处，实际 {n} 处")
    return html.replace(old, new)


# ---------- 1. index.html：清编辑器残留 ----------
def clean_editor_artifacts(html, path):
    before = len(html.encode())
    html = re.sub(r'\s*data-page-node-id="[^"]*"', "", html)
    html = re.sub(r'<style id="__dm_[^>]*>.*?</style>', "", html, flags=re.S)
    html = html.replace('<body style="">', "<body>")
    # 零宽字符（编辑器粘贴残留）会让搜索和复制出问题
    html = html.replace("\u200b", "")
    after = len(html.encode())
    print(f"  {path}: 清理编辑器残留 {before} -> {after} B (-{100*(before-after)/before:.1f}%)")
    return html


# ---------- 2. header 硬编码 scrolled ----------
def fix_header(html):
    return sub_exact(
        html,
        '<header class="site-header scrolled"',
        '<header class="site-header"',
        1,
        "header scrolled",
    )


# ---------- 3. 在 head 里打 js 标记（.reveal 兜底用） ----------
def inject_js_flag(html, path):
    marker = '<script>document.documentElement.classList.add("js")</script>'
    if marker in html:
        return html
    m = re.search(r'(<meta name="viewport"[^>]*>)', html)
    if not m:
        sys.exit(f"[FAIL] {path}: 找不到 viewport meta")
    return html[: m.end()] + "\n" + marker + html[m.end():]


# ---------- 4. <img> -> <picture>，并补尺寸/懒加载 ----------
LAZY_EXEMPT = ("hero-visual", "pd-hero-media", "brand", "footer-logo")


def enhance_images(html, path, is_home):
    stats = {"picture": 0, "lazy": 0, "size": 0}

    def repl(m):
        tag = m.group(0)
        ctx = html[max(0, m.start() - 220): m.start()]
        sm = re.search(r'src="(assets/[^"]+)"', tag)
        if not sm:
            return tag
        src = sm.group(1)

        # 尺寸
        if "width=" not in tag:
            dims = img_size(src)
            if dims:
                tag = tag[:-1] + f' width="{dims[0]}" height="{dims[1]}">'
                stats["size"] += 1

        # 懒加载（首屏元素豁免）；首屏大图给高优先级
        near = ctx[-160:]
        exempt = any(k in near for k in LAZY_EXEMPT)
        if "loading=" not in tag and not exempt:
            tag = tag[:-1] + ' loading="lazy" decoding="async">'
            stats["lazy"] += 1
        elif exempt and ("hero-visual" in near or "pd-hero-media" in near):
            if "fetchpriority" not in tag:
                tag = tag[:-1] + ' fetchpriority="high">'

        # AVIF
        avif = src.rsplit(".", 1)[0] + ".avif"
        if os.path.exists(avif) and "<picture>" not in ctx:
            stats["picture"] += 1
            return f'<picture><source type="image/avif" srcset="{avif}">{tag}</picture>'
        return tag

    html = re.sub(r"<img\b[^>]*>", repl, html)
    print(f"  {path}: picture={stats['picture']} lazy={stats['lazy']} size={stats['size']}")
    return html


# ---------- 5. video 可访问性 ----------
def enhance_videos(html, path):
    n = 0

    def repl(m):
        nonlocal n
        tag = m.group(0)
        if "aria-label" in tag:
            return tag
        n += 1
        extra = ' disablepictureinpicture aria-label="品牌影片"'
        return tag[:-1] + extra + ">"

    html = re.sub(r"<video\b[^>]*>", repl, html)
    if n:
        print(f"  {path}: video 可访问性 {n} 处")
    return html


# ---------- 6. head meta ----------
def inject_meta(html, path, meta):
    if "og:title" in html:
        return html
    if "product" in meta:
        title = re.search(r"<title>([^<]*)</title>", html).group(1)
        desc = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
    else:
        title, desc = meta["title"], meta["desc"]
    url = SITE + meta["url"]
    og_img = SITE + "/" + meta.get("og_image", "assets/hero-products.jpg")

    block = f"""<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="颜植季 YENCIGI">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_img}">
<meta property="og:locale" content="zh_CN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_img}">
<meta name="theme-color" content="#faf9f7">
"""
    if meta.get("is_home"):
        block += """<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Organization","name":"颜植季 YENCIGI",
"url":"%s","logo":"%s/assets/logo.png","description":"%s"}
</script>
""" % (SITE, SITE, meta["desc"])

    return html.replace("</head>", block + "</head>", 1)


# ---------- 主流程 ----------
def main():
    for path, meta in PAGES.items():
        html = open(path, encoding="utf-8").read()
        html = clean_editor_artifacts(html, path) if meta.get("is_home") else html
        html = fix_header(html)
        html = inject_js_flag(html, path)
        html = enhance_images(html, path, bool(meta.get("is_home")))
        html = enhance_videos(html, path)
        html = inject_meta(html, path, meta)
        # 统一引号（产品页里混了单引号）
        html = html.replace("<li class='reveal'>", '<li class="reveal">')
        html = html.replace("<li class='reveal d1'>", '<li class="reveal d1">')
        open(path, "w", encoding="utf-8").write(html)
        print(f"  -> {path} 完成 ({os.path.getsize(path)} B)")


if __name__ == "__main__":
    main()
