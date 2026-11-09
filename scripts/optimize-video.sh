#!/usr/bin/env bash
# 视频压缩：720x1280 CRF 原片 -> 480x854 CRF30 + AAC 48k mono
#
# 依据：站点内所有视频展示宽度均 <= 480px
#   .film-card（3 列网格，单卡约 384px）
#   .pd-film-frame（max-width: 460px）
#   .science-media（0.9fr 栅格约 461px）
# 480x854 在 1x 屏上无需放大，2x 屏接受一次上采样。
#
# 用法：./scripts/optimize-video.sh [--dry-run]
set -euo pipefail
cd "$(dirname "$0")/.."

CRF="${CRF:-30}"
ABR="${ABR:-48k}"
WIDTH="${WIDTH:-480}"
DRY=""
[[ "${1:-}" == "--dry-run" ]] && DRY=1

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

total_before=0
total_after=0

for f in assets/*.mp4; do
  [[ "$f" == *".bak.mp4" ]] && continue
  w=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$f")
  if [[ -n "$w" && "$w" -le "$WIDTH" ]]; then
    printf '%-18s 已是 %spx 宽，跳过\n' "$(basename "$f")" "$w"
    continue
  fi
  before=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f")
  out="$tmp/$(basename "$f")"

  ffmpeg -v error -y -i "$f" \
    -vf "scale=${WIDTH}:-2:flags=lanczos" \
    -c:v libx264 -crf "$CRF" -preset slow -profile:v high -pix_fmt yuv420p \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -c:a aac -b:a "$ABR" -ac 1 \
    -movflags +faststart "$out"

  after=$(stat -f%z "$out" 2>/dev/null || stat -c%s "$out")
  pct=$(awk -v a="$before" -v b="$after" 'BEGIN{printf "%.0f", (1-b/a)*100}')
  printf '%-18s %7.0f KiB -> %7.0f KiB  (-%s%%)\n' "$(basename "$f")" \
    "$(awk -v v="$before" 'BEGIN{print v/1024}')" \
    "$(awk -v v="$after" 'BEGIN{print v/1024}')" "$pct"

  total_before=$((total_before + before))
  total_after=$((total_after + after))

  [[ -z "$DRY" ]] && mv "$out" "$f" && touch "$f"
done

awk -v a="$total_before" -v b="$total_after" \
  'BEGIN{printf "\nTOTAL %.1f MiB -> %.1f MiB  (-%.0f%%)\n", a/1048576, b/1048576, (1-b/a)*100}'
