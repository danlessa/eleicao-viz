#!/bin/sh
# Upload the map to the public GCS bucket (gzip-encoded; GCS transcodes for clients without gzip).
# usage: sh publish_gcs.sh path/to/rmsp_eleicoes_2022_2024_locais.html
set -e
gzip -9 -c "$1" > "$1.gz"
gcloud storage cp "$1.gz" gs://eleicao-viz/rmsp_eleicoes_2022_2024_locais.html --content-encoding=gzip \
  --content-type='text/html; charset=utf-8' --cache-control='public, max-age=60' --quiet
rm "$1.gz"
