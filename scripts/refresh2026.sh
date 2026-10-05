#!/bin/sh
# Election night: fetch newly published boletins, rebuild bundle_2026.json and the HTML, upload it to GCS.
# Run from the work dir (see build2026.py for its inputs; combine.py also needs tpl3.html, package/ and the other bundles).
set -e
python3 ../scripts/scrape_bu2026.py 16
python3 ../scripts/parse_bu2026.py | tail -1
uv run --no-project --with geopandas --with pyogrio --with scipy python ../scripts/build2026.py | tail -1
cp ../scripts/tpl3.html . && python3 ../scripts/combine.py
sh ../scripts/publish_gcs.sh rmsp_eleicoes_2022_2024_locais.html
