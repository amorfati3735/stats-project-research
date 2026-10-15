#!/usr/bin/env bash
# Reproducible dataset download for the SONIQ project directory. No credentials required.
#
#   bash scripts/fetch_data.sh              # Spotify sets (the original direction)
#   bash scripts/fetch_data.sh --with-fma   # ... plus the optional FMA metadata (~342 MB, slow)
#   bash scripts/fetch_data.sh --india      # the India candidates (monsoon direction)
#   bash scripts/fetch_data.sh --all        # everything except FMA
#
# Downloads into data/raw/. Re-running is safe (curl -o overwrites).
# (curl -o overwrites). Nothing here needs an API key.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/raw

WANT_FMA=0
WANT_SPOTIFY=0
WANT_INDIA=0
for arg in "$@"; do
  case "$arg" in
    --with-fma) WANT_FMA=1; WANT_SPOTIFY=1 ;;
    --india)    WANT_INDIA=1 ;;
    --all)      WANT_SPOTIFY=1; WANT_INDIA=1 ;;
    "")         WANT_SPOTIFY=1 ;;
    *) echo "unknown flag: $arg" >&2; exit 2 ;;
  esac
done

if [[ "$WANT_SPOTIFY" == 1 ]]; then
  echo "[spotify 1/2] Kaggle 'Spotify Tracks Dataset' mirror (114,000 tracks, 20,118,244 B)"
  curl -sSL -o data/raw/kaggle_spotify_tracks_114k.csv \
    "https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv"

  echo "[spotify 2/2] TidyTuesday 'Spotify Songs' 2020-01-21 (32,833 tracks, 7,971,379 B)"
  curl -sSL -o data/raw/tidytuesday_spotify_songs.csv \
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2020/2020-01-21/spotify_songs.csv"

  if [[ "$WANT_FMA" == 1 ]]; then
    echo "[spotify 3/3] FMA metadata (OPTIONAL, 358,412,441 B, slow) — best-effort"
    curl -sSL -C - -o data/raw/fma_metadata.zip \
      "https://os.unil.cloud.switch.ch/fma/fma_metadata.zip" \
      || echo "    WARNING: FMA download flickered (this endpoint truncates connections). Re-run to resume."
    if [[ -s data/raw/fma_metadata.zip ]] && unzip -tq data/raw/fma_metadata.zip >/dev/null 2>&1; then
      ( cd data/raw && unzip -oq fma_metadata.zip -d fma_metadata )
    else
      echo "    WARNING: FMA archive incomplete/invalid — recorded as DOCUMENTED ONLY in the audit."
    fi
  fi
fi

if [[ "$WANT_INDIA" == 1 ]]; then
  # Primary dataset for the monsoon direction — 36 meteorological subdivisions,
  # monthly + seasonal + annual, 1901-2015. IMD via data.gov.in; Kaggle copy is
  # CC BY-SA 4.0. Expected size 437,910 B.
  #   sha256 fdc0b7fd8fccea2aab3910014ca7cacdd2f9faee511adda22b43cf30b680b4ec
  echo "[india 1/5] Rainfall, 36 subdivisions, 1901-2015 (PRIMARY, 437,910 B)"
  curl -sSL -o data/raw/rainfall_alt.csv \
    "https://raw.githubusercontent.com/MainakRepositor/Datasets/master/rainfall%20in%20india%201901-2015.csv"

  echo "[india 2/5] Rainfall mirror extended to 2017 (sensitivity check only, 441,180 B)"
  curl -sSL -o data/raw/rainfall_1901_2015.csv \
    "https://raw.githubusercontent.com/raghav0807/Rainfall-Data-Analysis-Visualization-/main/Dataset.csv"

  echo "[india 3/5] CPCB daily city air quality 2015-2020, CC0 (2,574,056 B)"
  curl -sSL -o data/raw/aqi_city_day.csv \
    "https://raw.githubusercontent.com/adityarc19/aqi-india/main/city_day.csv"

  echo "[india 4/5] Crop area & production 1997-2015, CC0 (15,316,741 B)"
  curl -sSL -o data/raw/crop_production.csv \
    "https://raw.githubusercontent.com/Vishnukurra101/crop-production-india/main/crop_production.csv"

  echo "[india 5/5] Daily electricity demand per state, CC BY 4.0 (807,563 B)"
  curl -sSL -o data/raw/corrected_daily_energy_met_MU.csv \
    "https://zenodo.org/records/14983362/files/corrected_daily_energy_met_MU.csv?download=1"

  echo
  echo "NOTE: the CPI file (data/raw/cpi_india.csv, 20,232,662 B) is NOT auto-downloaded"
  echo "      because the CKAN URL embeds a resource UUID. Fetch it manually from:"
  echo "      https://ckandev.indiadataportal.com/dataset/b8836317-263c-4e11-a94c-32e5b295cd30"
  echo "      (resource: consumer_price_index.csv). The official api.mospi.gov.in endpoint"
  echo "      is unreachable from here (legacy TLS renegotiation disabled in OpenSSL 3)."
fi

echo "done. sizes:"
ls -l data/raw 2>/dev/null || true
