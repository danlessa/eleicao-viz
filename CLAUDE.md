# CLAUDE.md

Electoral maps of the São Paulo metro area (RMSP) by polling place: president 2nd round 2006/2010/2014/2018/2022,
mayor 2024 1st and 2nd rounds, general election 2026 1st round (five offices, one tab with a cargo selector). The deliverable is the self-contained `rmsp_eleicoes_2022_2024_locais.html` (~30 MB,
Leaflet and all data inlined; filename kept for link stability). It is hosted on GCS (bucket `gs://eleicao-viz`, project
`danlessa`, uploaded gzip-encoded by `scripts/publish_gcs.sh`), not in git: the repo's copy of that file and `index.html`
are full-page iframes of https://storage.googleapis.com/eleicao-viz/rmsp_eleicoes_2022_2024_locais.html, so the public
link stays https://abiru.to/eleicao-viz/ (GitHub Pages, custom domain) and old links keep working. Get the full file with `curl --compressed -O <that URL>`. See README.md (Portuguese) for color conventions,
data sources and the pipeline order.

## Working on this repo
- Presidential 2006–2018 is reproducible from committed data plus the geocode file: `build_pres.py YEAR` then
  `render_two.py YEAR`. TSE president-by-section data is in `votacao_secao_YEAR_BR.zip` (cdn.tse.jus.br/estatistica/
  sead/odsele/votacao_secao/), not the `_SP` file; fdhidalgo release v0.16 has per-year coordinates keyed by
  (ano, cd_localidade_tse, nr_zona, nr_locvot).
- `combine.py` rebuilds the HTML byte-for-byte from `bundle_*.json` + `tpl3.html` + Leaflet 1.9.4 (`package/dist/`,
  from unpkg). Missing bundles can be extracted from the published HTML (`const DATA={'2006':…}`, `const MUN=…`).
- The rest of the pipeline (2022, 2024) can't be re-run from the repo: it needs raw TSE files and
  `geocoded_polling_stations.csv.gz` (54 MB, not committed), and its intermediates (`bundle_*.json`,
  `tri_agg_2024.csv`, `rmsp_locais_2024_*.csv`, `rmsp_voronoi*.gpkg`, …) aren't committed either. Scripts in `scripts/`
  assume those flat files sit in the cwd.
- To change published colors or labels without the raw inputs, patch the artifacts directly (see
  `scripts/apply_overrides.py`; download the full HTML first and re-upload it with `publish_gcs.sh` afterwards): the HTML embeds `const DATA={'2006':{…},…,'2022':{…},'2024':{…},'2024_2T':{…}}`. Parse each bundle
  with `json.JSONDecoder().raw_decode` and re-dump with `ensure_ascii=False, separators=(',',':')`, which round-trips
  byte-for-byte. Each bundle has `props` (circles) and `vor.features[].properties` (Voronoi cells); patch both.
- The PNGs can be regenerated with the original `render2.py 2024` / `render_two.py 2024_2T` in a scratch dir by
  extracting their inputs from the committed gpkgs (`locais_voronoi`, `locais_pontos`, `municipios` layers) and using
  `data/rmsp_prefeito_2024_1T_polos_por_local.csv` as `tri_agg_2024.csv`. The 2022 PNG/bundle isn't affected by 2024 changes.
- 2026 comes from the live results site, not dados abertos: `scrape_bu2026.py` fetches each RMSP section's `.bu`
  (pleito 3220; per-section files appear ~1h after the section is received, and mirrors can 404 briefly),
  `parse_bu2026.py` decodes the BER by field position (no spec file needed), `build2026.py` builds `bundle_2026.json`.
  Work dir `work2026/` is gitignored; `scripts/refresh2026.sh` runs the whole chain once;
  `scripts/live2026.sh` scrapes continuously and republishes to GCS every 10 min (touch `work2026/STOP` to end it). `bundle_2026.json` has no per-feature
  colors: `cargos[k].V[key][i]` are vote columns aligned with `props` (`key` = candidate number, `p<party>`, `f<federation>`),
  and the template computes colors per cargo/view. Presidente also carries `prev` (2022 1T Lula/Bolsonaro/válidos per
  2026 point, from `data/pres1t_rmsp_2022.csv.gz`) for the `d:*` (pp) and `a:*` (votes) change views, plus 2022
  aptos/comp/branco/nulo (`data/pres1t_rmsp_2022_detalhes.csv.gz`) and `props[].aptos` for the abstention views `x:*`/`y:*`. The TSE `_SP` 2022 file has
  no president; the `_BR` one answered 429, so that extract came from Base dos Dados via `bq` (project `danlessa`). Coordinates come from TSE's `eleitorado_local_votacao_2026` (has lat/long).
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
