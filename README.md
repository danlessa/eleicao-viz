# RMSP — resultados eleitorais por local de votação

Mapa interativo: `rmsp_eleicoes_2022_2024_locais.html` (auto-contido, ~13 MB). Camadas: presidente 2022 2º turno,
prefeito 2024 1º turno, prefeito 2024 2º turno (7 municípios). Modos: Voronoi (área geográfica) ou círculos
(área ∝ votos) com escala, relaxação por colisão (Dorling) no navegador e opacidade; mapas-base OSM e rmsampa-v2.

## Convenções de cor
- **2022 2T e 2024 2T** — divergente vermelho/azul, cinza em 50/50, escala esticada ao percentil 95 do desvio.
  Vermelho = Lula (2022) / candidato cuja votação por local se correlaciona positivamente com a de Lula 2022 (2024 2T).
- **2024 1T** — polos definidos empiricamente por município pela correlação (Pearson, entre locais) da fração de
  votos de cada um dos 3 primeiros com a fração de Lula 2022 no mesmo local: laranja = mais correlato a Lula,
  verde-azulado = mais correlato a Bolsonaro, roxo = intermediário ("outlier"). Se os 2 primeiros somam ≥85% dos
  válidos, escala bipolar entre os dois polos presentes; senão mistura ternária em OKLab (matiz = direção,
  croma = dominância do líder, saturando em 60%; cinza = empate). Há ainda a visualização por candidato
  (1º/2º/3º colocado no município) em escala sequencial única, com opção de círculos ∝ votos do candidato.

## Dados
- `data/pres2t_sp.csv.gz` — TSE votação por seção 2022, SP, presidente 2º turno
- `data/prefeito_1t_rmsp_2024.csv.gz`, `data/prefeito_2t_rmsp_2024.csv.gz` — TSE votação por seção 2024, prefeito, RMSP
- `data/corr_2024_1t.csv`, `data/corr_2024_2t.csv` — r de cada candidato vs. Lula 2022, por município
- `data/rmsp_prefeito_2024_1T_polos_por_municipio.csv` / `_por_local.csv` — atribuição de polos e cores
- `data/geojs-35-mun.json` — limites municipais SP (IBGE via tbrugz/geodata-br)
- coordenadas dos locais: fdhidalgo/geocode_br_polling_stations (`geocoded_polling_stations.csv.gz`, 54 MB, não incluído)
- `*_locais.gpkg` — camadas `locais_voronoi`, `locais_pontos`, `municipios` (EPSG:31983); `*_locais.csv` — tabela por local
- `rmsp_prefeito_2024_1T_candidatos_por_local.csv` — candidato × local (formato longo)

## Pipeline (scripts/)
1. `agg.py`, `build_geo.py` — 2022: agrega por local, junta coordenadas, Voronoi recortado por município
2. `run2024.py` — 2024 1T: agregação por local e Voronoi
3. `corr_poles.py` — correlação candidato × Lula 2022 por município (1T e 2T)
4. `tri2024b.py` — polos e cores ternárias do 1T; `build_2t.py` — dados/Voronoi/polos do 2T
5. `render2.py 2024`, `render_two.py 2022|2024_2T` — PNGs estáticos + bundles JSON
6. `combine.py` — monta o HTML único a partir de `tpl3.html` e dos bundles (Leaflet embutido)
- `poles.py` — heurística partidária anterior (não usada mais; mantida para referência)
- `_old/` — PNGs de versões anteriores da paleta
