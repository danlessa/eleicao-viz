# CLAUDE.md

Electoral maps of the São Paulo metro area (RMSP) by polling place: president 2022 2nd round, mayor 2024 1st and
2nd rounds. The deliverable is the self-contained `rmsp_eleicoes_2022_2024_locais.html` (~13 MB, Leaflet and all data
inlined), served via GitHub Pages (`index.html` redirects to it). See README.md (Portuguese) for color conventions,
data sources and the pipeline order.

## Working on this repo
- The full pipeline can't be re-run from the repo: it needs raw TSE files and
  `geocoded_polling_stations.csv.gz` (54 MB, not committed), and its intermediates (`bundle_*.json`,
  `tri_agg_2024.csv`, `rmsp_locais_2024_*.csv`, `rmsp_voronoi*.gpkg`, …) aren't committed either. Scripts in `scripts/`
  assume those flat files sit in the cwd.
- To change published colors or labels without the raw inputs, patch the artifacts directly (see
  `scripts/apply_overrides.py`): the HTML embeds `const DATA={'2022':{…},'2024':{…},'2024_2T':{…}}`. Parse each bundle
  with `json.JSONDecoder().raw_decode` and re-dump with `ensure_ascii=False, separators=(',',':')`, which round-trips
  byte-for-byte. Each bundle has `props` (circles) and `vor.features[].properties` (Voronoi cells); patch both.
- The PNGs can be regenerated with the original `render2.py 2024` / `render_two.py 2024_2T` in a scratch dir by
  extracting their inputs from the committed gpkgs (`locais_voronoi`, `locais_pontos`, `municipios` layers) and using
  `data/rmsp_prefeito_2024_1T_polos_por_local.csv` as `tri_agg_2024.csv`. The 2022 PNG/bundle isn't affected by 2024 changes.
- No Python env is checked in. Use `uv run --no-project --with geopandas --with pyogrio --with matplotlib --with scipy python …`.
- When rewriting CSVs with pandas, read with `float_precision='round_trip'` and keep nullable int columns
  (`NR_VOTAVEL_*`) as `str`, or every row's diff churns.

## Color semantics (2024)
- 1T poles per municipality: 0 = ~Lula (orange), 1 = ~Bolsonaro (teal), 2 = outlier (purple). Fields suffixed `_0/_1/_2`
  (`v`, `s`, `NM_VOTAVEL_`, `NR_VOTAVEL_`, `SG_`, `rank_`, `r_lula22_`) are indexed by pole, not by rank.
- 2T: A = red (~Lula side), B = blue; `pct` = share of A.
- Poles come from each candidate's correlation with Lula 2022, except where `scripts/overrides.py` pins them by
  municipality code and candidate number. The user decides these by political knowledge; add new ones there and
  re-run `scripts/apply_overrides.py`, then update the note strings in `render2.py` / `render_two.py` /
  `apply_overrides.py` and the README.
- Municipality codes are TSE codes (`CD_MUNICIPIO`), not IBGE ones. Example: Diadema 63770, Itapevi 65510, Mauá 66893,
  São Caetano 70777, Taboão da Serra 71579.
