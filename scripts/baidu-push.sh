#!/usr/bin/env bash
# 把 sitemap.xml 中的全部页面主动推送给百度（普通收录 · API 提交）
# 用法：BAIDU_TOKEN=你的token ./scripts/baidu-push.sh
set -euo pipefail

SITE="https://www.yencigi.com"
: "${BAIDU_TOKEN:?请先设置 BAIDU_TOKEN（百度搜索资源平台 → 普通收录 → API 提交 中的 token）}"

cd "$(dirname "$0")/.."
urls=$(mktemp)
trap 'rm -f "$urls"' EXIT
grep -o '<loc>[^<]*</loc>' sitemap.xml | sed -e 's/<loc>//' -e 's#</loc>##' > "$urls"

echo "推送 $(wc -l < "$urls" | tr -d ' ') 个链接："
cat "$urls"
curl -sS -H 'Content-Type: text/plain' --data-binary @"$urls" \
  "http://data.zz.baidu.com/urls?site=${SITE}&token=${BAIDU_TOKEN}"
echo
