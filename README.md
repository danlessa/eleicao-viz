# RMSP — resultados eleitorais por local de votação

Mapa interativo: https://storage.googleapis.com/eleicao-viz/rmsp_eleicoes_2022_2024_locais.html (auto-contido, ~30 MB,
~5 MB com gzip; hospedado no GCS por `scripts/publish_gcs.sh`; no repositório, `rmsp_eleicoes_2022_2024_locais.html` e
`index.html` só redirecionam para lá, para não inchar o histórico do git). Eleições (seletor): presidente 2º turno 2006, 2010, 2014, 2018 e 2022, prefeito 2024
1º turno, prefeito 2024 2º turno (7 municípios), eleições gerais 2026 1º turno (presidente, governador, senador,
deputado federal e estadual; seletor de cargo). Modos: Voronoi (área geográfica) ou círculos
(área ∝ votos) com escala, relaxação por colisão (Dorling) no navegador e opacidade; mapas-base OSM e rmsampa-v2.

## Convenções de cor
- **Presidente 2T e 2024 2T** — divergente vermelho/azul, cinza em 50/50, escala esticada ao percentil 95 do desvio
  (por ano, então os tons não são comparáveis entre anos). Vermelho = candidato do PT (Lula 2006/2022, Dilma 2010/2014,
  Haddad 2018); azul = Alckmin, Serra, Aécio, Bolsonaro (2018/2022) / no 2024 2T, candidato cuja votação por local se correlaciona positivamente com a de Lula 2022 (2024 2T).
- **2024 1T** — polos definidos empiricamente por município pela correlação (Pearson, entre locais) da fração de
  votos de cada um dos 3 primeiros com a fração de Lula 2022 no mesmo local: laranja = mais correlato a Lula,
  verde-azulado = mais correlato a Bolsonaro, roxo = intermediário ("outlier"). Se os 2 primeiros somam ≥85% dos
  válidos, escala bipolar entre os dois polos presentes; senão mistura ternária em OKLab (matiz = direção,
  croma = dominância do líder, saturando em 60%; cinza = empate). Há ainda a visualização por candidato
  (1º/2º/3º colocado no município) em escala sequencial única, com opção de círculos ∝ votos do candidato.
- **2026 1T** — majoritários: os 3 mais votados na RMSP, polos pela correlação (entre locais) da fração de cada um com
  a fração de Lula 2026 no mesmo local (laranja = mais correlato, verde-azulado = menos, roxo = intermediário); se os 2
  primeiros somam ≥85% dos válidos, escala bipolar entre eles (mesma paleta OKLab do 2024 1T). Presidente usa a escala
  vermelho/azul dos 2º turnos (vermelho = Lula, azul = Flávio Bolsonaro, fração de Lula entre os dois, esticada ao p95). Senador: 2 votos por
  eleitor e cada coligação lança até 2 nomes, então o mapa é bipolar entre as duas chapas (coligações) mais votadas,
  somando os dois candidatos de cada uma; percentuais sobre o total de votos para senador. Também há a visualização por candidato. Deputados: fração dos
  válidos do local por partido/federação (nominais + legenda) ou por candidato (60 mais votados na RMSP), escala
  sequencial esticada ao p95. Ajustes manuais de polo: chaves `2026_presidente`, `2026_governador`, `2026_senador` em
  `overrides.py`.
- **Ajustes manuais** (`scripts/overrides.py`) — onde a correlação rotula mal um candidato, o polo é fixado à mão:
  São Caetano (PODE outlier, PL ~Bolsonaro), Itapevi (PSB ~Lula, PODE outlier), Taboão da Serra (PSDB ~Lula,
  PODE outlier, UNIÃO ~Bolsonaro), Diadema (MDB outlier), Mauá (PT ~Lula). No 2T: Mauá PT vermelho, Taboão UNIÃO azul.

## Dados
- `data/pres2t_sp.csv.gz` — TSE votação por seção 2022, SP, presidente 2º turno
- `data/pres2t_rmsp_{2006,2010,2014,2018}.csv.gz` — TSE votação por seção, presidente 2º turno, RMSP (recortados do
  arquivo `votacao_secao_ANO_BR.zip`; o arquivo `_SP` não traz presidente)
- `data/prefeito_1t_rmsp_2024.csv.gz`, `data/prefeito_2t_rmsp_2024.csv.gz` — TSE votação por seção 2024, prefeito, RMSP
- `data/corr_2024_1t.csv`, `data/corr_2024_2t.csv` — r de cada candidato vs. Lula 2022, por município
- `data/rmsp_prefeito_2024_1T_polos_por_municipio.csv` / `_por_local.csv` — atribuição de polos e cores
- `data/geojs-35-mun.json` — limites municipais SP (IBGE via tbrugz/geodata-br)
- 2026: boletins de urna por seção (`.bu`, ASN.1) do site de resultados do TSE (`resultados.tse.jus.br/oficial/ele2026/
  arquivo-urna/3220/…`), baixados durante a apuração; locais e coordenadas de `eleitorado_local_votacao_2026.zip`
  (cdn.tse.jus.br, já traz latitude/longitude); nomes de `consulta_cand_2026.zip`. Quando o TSE publicar
  `votacao_secao_2026`, ele substitui os boletins como fonte
- coordenadas dos locais: fdhidalgo/geocode_br_polling_stations (`geocoded_polling_stations.csv.gz`, 54 MB, não incluído;
  v0.16 para 2006–2018, com as coordenadas de cada ano)
- `*_locais.gpkg` — camadas `locais_voronoi`, `locais_pontos`, `municipios` (EPSG:31983); `*_locais.csv` — tabela por local
- `rmsp_prefeito_2024_1T_candidatos_por_local.csv` — candidato × local (formato longo)

## Pipeline (scripts/)
1. `agg.py`, `build_geo.py` — 2022: agrega por local, junta coordenadas, Voronoi recortado por município
2. `run2024.py` — 2024 1T: agregação por local e Voronoi
3. `corr_poles.py` — correlação candidato × Lula 2022 por município (1T e 2T)
4. `tri2024b.py` — polos e cores ternárias do 1T; `build_2t.py` — dados/Voronoi/polos do 2T
   `build_pres.py ANO` — presidente 2T 2006–2018: agregação por local, coordenadas do ano, Voronoi e entregáveis
   (`rmsp_presidente_ANO_2T_locais.{csv,gpkg}`)
5. `render2.py 2024`, `render_two.py 2006|2010|2014|2018|2022|2024_2T` — PNGs estáticos + bundles JSON
   `scrape_bu2026.py`, `parse_bu2026.py`, `build2026.py` — 2026 1T: baixa os boletins da RMSP (re-executável; pega os
   que faltam), decodifica para uma tabela por seção e monta `bundle_2026.json`; `refresh2026.sh` roda tudo e o
   `combine.py` em sequência (pasta de trabalho `work2026/`, fora do git)
6. `combine.py` — monta o HTML único a partir de `tpl3.html` e dos bundles (Leaflet 1.9.4 de `package/dist/`, embutido)
- `overrides.py` — ajustes manuais de polo (usados por `tri2024b.py` e `build_2t.py`)
- `apply_overrides.py` — aplica `overrides.py` direto nos artefatos publicados (HTML, CSVs, gpkg do 2T) sem rodar o pipeline
- `poles.py` — heurística partidária anterior (não usada mais; mantida para referência)
- `_old/` — PNGs de versões anteriores da paleta
