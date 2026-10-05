#!/bin/sh
# Election night, two loops in parallel (run from the work dir; see refresh2026.sh for the one-shot version):
# - scraping: back-to-back passes of scrape_bu2026.py (a pass can take 20+ min while most files are still 404)
# - publishing: every 10 min, if new .bu files arrived, rebuild bundle + HTML and upload to GCS
# Stops after an hour with no new files, or after 8 h. Touch STOP to end it early.
rm -f STOP
( while ps -eo args | grep -q "^python3 ../scripts/scrape_bu2026.py"; do sleep 20; done  # let a pass already running finish
  while [ ! -e STOP ]; do python3 ../scripts/scrape_bu2026.py 16 | tail -1; sleep 30; done ) &
last=$(ls bu | wc -l); same=0; i=0
while [ ! -e STOP ]; do
  sleep 600; i=$((i+1)); n=$(ls bu | wc -l)
  if [ "$n" -ne "$last" ]; then
    python3 ../scripts/parse_bu2026.py | tail -1
    uv run --no-project --with geopandas --with pyogrio --with scipy python ../scripts/build2026.py | tail -1
    cp ../scripts/tpl3.html . && python3 ../scripts/combine.py > /dev/null
    sh ../scripts/publish_gcs.sh rmsp_eleicoes_2022_2024_locais.html > /dev/null 2>&1 && echo "$(date +%H:%M) published ($n files)"
    last=$n; same=0
  else
    same=$((same+1)); echo "$(date +%H:%M) nothing new ($n files)"
  fi
  { [ $same -ge 6 ] || [ $i -ge 48 ]; } && touch STOP
done
wait; echo DONE
