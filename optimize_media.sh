#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

# Input dirs (current)
AUDIO_IN="audio"
IMAGES_IN="images"

# Output dirs (optimized)
AUDIO_OUT="audio_opt"
IMAGES_OUT="images_opt"

echo "==> Optimizing AUDIO into $AUDIO_OUT (mono, 44.1kHz, ~112kbps; trim silence)"
find "$AUDIO_IN" -type f \( -iname '*.wav' -o -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.aac' \) -print0 | \
  while IFS= read -r -d '' f; do
    rel="${f#$AUDIO_IN/}"
    out="$AUDIO_OUT/${rel%.*}.mp3"
    mkdir -p "$(dirname "$out")"
    ffmpeg -v error -y -i "$f" -ac 1 -ar 44100 \
      -af "silenceremove=start_periods=1:start_silence=0.1:start_threshold=-35dB:stop_periods=1:stop_silence=0.2:stop_threshold=-35dB" \
      -b:a 112k "$out"
    echo "AUDIO: $rel -> ${out#$AUDIO_OUT/}"
  done

echo "==> Optimizing IMAGES into $IMAGES_OUT (width 900px, WebP q=70, stripped)"
find "$IMAGES_IN" -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \) -print0 | \
  while IFS= read -r -d '' f; do
    rel="${f#$IMAGES_IN/}"
    out="$IMAGES_OUT/${rel%.*}.webp"
    mkdir -p "$(dirname "$out")"
    magick "$f" -resize 900x -strip -quality 70 "$out"
    echo "IMAGE: $rel -> ${out#$IMAGES_OUT/}"
  done

echo "==> Done."
