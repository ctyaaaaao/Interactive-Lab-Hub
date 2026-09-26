#!/usr/bin/env bash

set -euo pipefail

VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

# Ask the user for a numerical input using Piper
python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "What is your zip code?" \
  | aplay -r 22050 -f S16_LE -t raw -

# Record the user's answer for 5 seconds
arecord -d 5 -f cd -c 1 -r 16000 number_answer.wav
