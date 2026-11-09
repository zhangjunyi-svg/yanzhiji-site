#!/usr/bin/env bash
# 图片优化
#   1) 内容图：生成 AVIF（crf30, cpu-used 6），保留原 JPG 作为 <picture> 兜底
#   2) 视频封面：缩到 480px 宽并以 JPEG q5 重编码（poster 无法用 <picture>，只保留 JPG）
#
# 用法：./scripts/optimize-images.sh [--check]
set -euo pipefail
cd "$(dirname "$0")/.."

CRF="${CRF:-30}"
CHECK=""
[[ "${1:-}" == "--check" ]] && CHECK=1

size() { stat -f%z "$1" 2>/dev/null || stat -c%s "$1"; }

echo "== AVIF（内容图） =="
for f in assets/*.jpg; do
  [[ "$f" == *.mp4.jpg ]] && continue
  out="${f%.jpg}.avif"
  [[ -n "$CHECK" && -f "$out" ]] && continue
  ffmpeg -v error -y -i "$f" -c:v libaom-av1 -still-picture 1 \
    -crf "$CRF" -cpu-used 6 -pix_fmt yuv420p "$out"
  b=$(size "$f"); a=$(size "$out")
  awk -v n="$(basename "$f")" -v b="$b" -v a="$a" \
    'BEGIN{printf "%-24s %6.0f KiB -> %5.0f KiB  (-%.0f%%)\n", n, b/1024, a/1024, (1-a/b)*100}'
done

echo
echo "== 视频封面（480px JPG） =="
for f in assets/*.mp4.jpg; do
  [[ -n "$CHECK" ]] && continue
  w=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$f")
  if [[ -n "$w" && "$w" -le 480 ]]; then
    printf '%-24s 已是 %spx 宽，跳过\n' "$(basename "$f")" "$w"
    continue
  fi
  out="${f%.jpg}.tmp.jpg"
  ffmpeg -v error -y -i "$f" -vf "scale=480:-2:flags=lanczos" -q:v 5 "$out"
  b=$(size "$f"); a=$(size "$out")
  mv "$out" "$f"; touch "$f"
  awk -v n="$(basename "$f")" -v b="$b" -v a="$a" \
    'BEGIN{printf "%-24s %6.0f KiB -> %5.0f KiB  (-%.0f%%)\n", n, b/1024, a/1024, (1-a/b)*100}'
done
