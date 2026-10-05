# 2026 1st round (presidente, governador, senador, deputado federal/estadual) by polling place -> bundle_2026.json
# usage: python build2026.py   (cwd needs votos_secao_rmsp_2026.csv.gz from parse_bu2026.py, sp-cs.json,
#   eleitorado_local_votacao_2026_SP.csv, consulta_cand_2026_{BR,SP}.csv, tse2ibge.json, geojs-35-mun.json,
#   rmsp_prefeito_2024_1T_locais.csv + rmsp_presidente_2022_2T_locais_raw.csv (fallback coordinates), agg.py, tri2024.py, overrides.py)
import json, re, numpy as np, pandas as pd, geopandas as gpd
from shapely.ops import voronoi_diagram, unary_union
from overrides import assign_poles
exec(open('agg.py').read().split('geo = pd.read_csv')[0])
exec(open('tri2024.py').read().split('# OKLab helpers')[1].split('# endpoints')[0])
T2I = {int(k): v for k, v in json.load(open('tse2ibge.json')).items()}
key = ['CD_MUNICIPIO', 'NR_ZONA', 'NR_LOCAL_VOTACAO']
CARGOS = [(1, 'presidente', 'Presidente', 'maj'), (3, 'governador', 'Governador', 'maj'), (5, 'senador', 'Senador', 'maj'),
          (6, 'depfed', 'Deputado federal', 'prop'), (7, 'depest', 'Deputado estadual', 'prop')]
NTOP = 60  # candidates offered per proportional office

# --- votes ---
v = pd.read_csv('votos_secao_rmsp_2026.csv.gz', sep=';', dtype={'NR_PARTIDO': 'Int64'})
sec = v.drop_duplicates(key + ['NR_SECAO', 'CD_ELEICAO'])
cs = json.load(open('sp-cs.json'))
n_total = sum(len(z['sec']) for mu in cs['abr'][0]['mu'] if int(mu['cd']) in T2I for z in mu['zon'])
n_sec = sec[sec.CD_ELEICAO == 6257].groupby(key).NR_SECAO.nunique().rename('n_secoes')
comp = sec[sec.CD_ELEICAO == 6257].groupby(key).QT_COMPARECIMENTO.sum().rename('total')
print('sections parsed', int(n_sec.sum()), 'of', n_total)

# --- polling places: TSE 2026 coordinates, 2024 geocoded ones where TSE has none ---
e = pd.read_csv('eleitorado_local_votacao_2026_SP.csv', sep=';', encoding='latin1', decimal=',')
e = e[e.CD_MUNICIPIO.isin(T2I)]
loc = e.groupby(key).agg(lat=('NR_LATITUDE', 'first'), long=('NR_LONGITUDE', 'first'), NM_LOCAL_VOTACAO=('NM_LOCAL_VOTACAO', 'first'),
                         DS_LOCAL_VOTACAO_ENDERECO=('DS_ENDERECO', 'first'), ds_bairro=('NM_BAIRRO', 'first'),
                         n_secoes_tot=('NR_SECAO', 'size')).reset_index()
bad = loc.lat.isna() | (loc.lat == -1)
l24 = pd.concat([pd.read_csv(f)[key + ['long', 'lat']].dropna() for f in ('rmsp_prefeito_2024_1T_locais.csv', 'rmsp_presidente_2022_2T_locais_raw.csv')]).drop_duplicates(key)
fb = loc[bad].drop(columns=['long', 'lat']).merge(l24, on=key, how='left')
loc.loc[bad, ['long', 'lat']] = fb[['long', 'lat']].values
print('locais', len(loc), 'without TSE coords', int(bad.sum()), '-> still missing', int(loc.lat.isna().sum()))
loc['cod_localidade_ibge'] = loc.CD_MUNICIPIO.map(T2I); loc['municipio'] = loc.cod_localidade_ibge.map(RMSP)
loc = loc.merge(n_sec, on=key, how='left').merge(comp, on=key, how='left').fillna({'n_secoes': 0, 'total': 0})
lost = loc[loc.lat.isna()]
print('votes at locais without coordinates:', int(lost.total.sum()), f'({100 * lost.total.sum() / max(1, loc.total.sum()):.3f}%)')
loc = loc.dropna(subset=['lat'])

# co-located polling places are merged into one point (as in the other years)
loc['lon_r'], loc['lat_r'] = loc.long.round(5), loc.lat.round(5)
loc['pt'] = loc.groupby(['cod_localidade_ibge', 'lon_r', 'lat_r']).ngroup()
J = lambda sep: (lambda x: sep.join(sorted(set(map(str, x)))))
pts = loc.groupby('pt').agg(cod_localidade_ibge=('cod_localidade_ibge', 'first'), municipio=('municipio', 'first'), long=('lon_r', 'first'),
                            lat=('lat_r', 'first'), NR_ZONA=('NR_ZONA', J('/')), NR_LOCAL_VOTACAO=('NR_LOCAL_VOTACAO', J('/')),
                            NM_LOCAL_VOTACAO=('NM_LOCAL_VOTACAO', J(' | ')), DS_LOCAL_VOTACAO_ENDERECO=('DS_LOCAL_VOTACAO_ENDERECO', 'first'),
                            ds_bairro=('ds_bairro', 'first'), n_secoes=('n_secoes', 'sum'), n_secoes_tot=('n_secoes_tot', 'sum'),
                            total=('total', 'sum'), n_locais=('NR_LOCAL_VOTACAO', 'size')).reset_index()
pts = pts[pts.n_secoes > 0].reset_index(drop=True)  # nothing counted there yet
N = len(pts); idx = dict(zip(pts.pt, pts.index))
v = v.merge(loc[key + ['pt']], on=key, how='inner'); v['i'] = v.pt.map(idx); v = v.dropna(subset=['i']); v['i'] = v.i.astype(int)
print('points', N)

# --- candidates and parties ---
cand = pd.concat([pd.read_csv(f'consulta_cand_2026_{u}.csv', sep=';', encoding='latin1') for u in ('BR', 'SP')])
cand = cand[cand.SG_UF.isin(['BR', 'SP'])]
NM = {(r.CD_CARGO, r.NR_CANDIDATO): r.NM_URNA_CANDIDATO for r in cand.itertuples()}
SG = {(r.CD_CARGO, r.NR_CANDIDATO): r.SG_PARTIDO for r in cand.itertuples()}
PARTY = cand.drop_duplicates('NR_PARTIDO').set_index('NR_PARTIDO').SG_PARTIDO.to_dict()
fed = cand[cand.NR_FEDERACAO > 0].drop_duplicates('NR_PARTIDO')
FEDNR = dict(zip(fed.NR_PARTIDO, fed.NR_FEDERACAO))
FEDNM = {r.NR_FEDERACAO: re.sub(r'\d+-', '', r.DS_COMPOSICAO_FEDERACAO) for r in fed.itertuples()}  # '13-PT/65-PC do B/43-PV' -> 'PT/PC do B/PV'

def col(sub, nr):
    a = np.zeros(N, dtype=int); g = sub[sub.NR_VOTAVEL == nr].groupby('i').QT_VOTOS.sum(); a[g.index] = g.values; return a

def share_of(sub, mask):
    a = np.zeros(N, dtype=int); g = sub[mask].groupby('i').QT_VOTOS.sum(); a[g.index] = g.values; return a

def okc(L, C, h): h = np.radians(h); return np.array([L, C * np.cos(h), C * np.sin(h)])
E = np.stack([okc(0.60, 0.14, 55), okc(0.60, 0.14, 175), okc(0.60, 0.14, 295)]); gray = E.mean(0)  # 0 orange 1 teal 2 purple
C = {}
lula = None
for cd, k, label, kind in CARGOS:
    sub = v[v.CD_CARGO == cd]
    nom, leg = sub.TP_VOTO == 'nominal', sub.TP_VOTO == 'legenda'
    validos = share_of(sub, nom | leg); branco = col(sub, 95); nulo = col(sub, 96)
    tot = sub[nom].groupby(['NR_VOTAVEL', 'NR_PARTIDO']).QT_VOTOS.sum().sort_values(ascending=False).reset_index()
    VT = int(validos.sum())
    keep = tot if kind == 'maj' else tot.head(NTOP)
    cands = [dict(nr=int(r.NR_VOTAVEL), nm=NM.get((cd, r.NR_VOTAVEL), str(r.NR_VOTAVEL)), sg=SG.get((cd, r.NR_VOTAVEL), PARTY.get(r.NR_PARTIDO, '')),
                  v=int(r.QT_VOTOS), s=round(100 * r.QT_VOTOS / VT, 2)) for r in keep.itertuples()]
    V = {str(c['nr']): col(sub, c['nr']) for c in cands}
    out = dict(label=label, kind=kind, validos=validos.tolist(), branco=branco.tolist(), nulo=nulo.tolist(), cands=cands, nominal_total=int(tot.QT_VOTOS.sum()))
    if kind == 'prop':
        pv = sub[nom | leg].groupby(['NR_PARTIDO', 'i']).QT_VOTOS.sum()
        parties = []; feds = {}
        for p, g in pv.groupby(level=0):
            a = np.zeros(N, dtype=int); a[g.index.get_level_values(1)] = g.values
            f = FEDNR.get(p)
            parties.append(dict(k=f'p{p}', nr=int(p), sg=PARTY.get(p, str(p)), fed=FEDNM.get(f, ''), v=int(a.sum()), s=round(100 * a.sum() / VT, 2)))
            V[f'p{p}'] = a
            if f: feds[f] = feds.get(f, 0) + a
        for f, a in feds.items():  # federations count as one party for seat allocation
            parties.append(dict(k=f'f{f}', nr=int(f), sg='Federação ' + FEDNM[f], fed='', v=int(a.sum()), s=round(100 * a.sum() / VT, 2))); V[f'f{f}'] = a
        out['parties'] = sorted(parties, key=lambda d: -d['v'])
    if cd == 1:
        lula = V['13'] / np.maximum(validos, 1)
    if kind == 'maj':
        # ternary: top 3 in the RMSP; poles from each one's correlation (between polling places) with Lula's 2026 share
        ok = validos > 0
        if cd == 5:  # two seats and each coalition runs up to two names: compare the two leading slates instead
            sq = cand[cand.CD_CARGO == 5].drop_duplicates('NR_CANDIDATO').set_index('NR_CANDIDATO')
            grp = {}
            for c in cands: grp.setdefault(sq.SQ_COLIGACAO.get(c['nr']), []).append(c)
            top = [dict(nr=f's{i}', nm=sq.NM_COLIGACAO[m[0]['nr']].title().replace(' Para ', ' para '), members=[c['nr'] for c in m],
                        v=sum(c['v'] for c in m)) for i, (g, m) in enumerate(sorted(grp.items(), key=lambda kv: -sum(c['v'] for c in kv[1]))[:2])]
            for u in top: V[u['nr']] = sum(V[str(n)] for n in u['members']); u['s'] = round(100 * u['v'] / VT, 2)
            top2 = sum(u['v'] for u in top) / VT; triway = False
        else:
            top = cands[:3]; top2 = (top[0]['v'] + top[1]['v']) / VT; triway = top2 < 0.85
        for c in top: c['r'] = round(float(np.corrcoef(V[str(c['nr'])][ok] / validos[ok], lula[ok])[0, 1]), 3)
        use = top if triway else top[:2]
        order = sorted(use, key=lambda c: -c['r'])
        for c, p in zip(order, assign_poles(f'2026_{k}', [c['nr'] for c in order])): c['pole'] = p
        W = np.zeros((N, 3)); present = np.zeros(3, bool)
        for c in use: W[:, c['pole']] = V[str(c['nr'])]; present[c['pole']] = True
        s = W.sum(1, keepdims=True); w = np.where(s > 0, W / np.maximum(s, 1e-9), present / present.sum())
        if triway:
            d = np.clip((w.max(1) - 1 / 3) / (0.6 - 1 / 3), 0, 1); vec = (w - 1 / 3) @ E[:, 1:]; ang = np.arctan2(vec[:, 1], vec[:, 0]); Cr = 0.14 * np.sqrt(d)
            lab = np.c_[np.full(N, 0.60), Cr * np.cos(ang), Cr * np.sin(ang)]
        else:
            pi, pj = np.flatnonzero(present)
            t = np.clip((w[:, pi] - 0.25) / 0.5, 0, 1)[:, None]
            lab = np.where(t >= 0.5, E[pi] * (2 * (t - 0.5)) + gray * (1 - 2 * (t - 0.5)), E[pj] * (1 - 2 * t) + gray * (2 * t))
        out['color'] = hexs(oklab_to_rgb(lab)); out['triway'] = bool(triway)
        if cd == 1 and not triway:
            # president: the 2nd-round maps' red/blue scale (render_two.py) instead of the 1T poles
            a, b = sorted(use, key=lambda c: c['pole'])
            va, vb = V[str(a['nr'])], V[str(b['nr'])]; s2 = va + vb
            pct = np.where(s2 > 0, 100 * va / np.maximum(s2, 1), 50.0)
            half = max(10, round(np.percentile(np.abs(pct[s2 > 0] - 50), 95))); lo, hi = 50 - half, 50 + half
            grad = ['#2c3e9e', '#7f95d6', '#e4e4e4', '#e69a86', '#b0142a']
            stops = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in grad], float)
            x = np.clip((pct - lo) / (hi - lo), 0, 1) * 4; i0 = np.minimum(x.astype(int), 3); f = (x - i0)[:, None]
            out['color'] = ['#%02x%02x%02x' % tuple(c) for c in np.round(stops[i0] * (1 - f) + stops[i0 + 1] * f).astype(int)]
            out['pc'] = ['#b0142a', '#2c3e9e']; out['grad'] = grad; out['hi'] = int(hi)
        if cd == 5:
            out['slates'] = top
            for u in top:
                for c in cands:
                    if c['nr'] in u['members']: c['pole'] = u['pole']
        print(label, 'top2 %.1f%%' % (100 * top2), [(c['nm'], c['s'], c.get('r'), c.get('pole')) for c in (top if cd == 5 else cands[:4])])
    else:
        print(label, 'parties', [(p['sg'], p['s']) for p in out['parties'][:6]], 'top cand', [(c['nm'], c['v']) for c in cands[:3]])
    out['V'] = {a: b.tolist() for a, b in V.items()}
    C[k] = out

# --- geometry: Voronoi per municipality (same as build_pres.py) ---
mun = gpd.read_file('geojs-35-mun.json'); mun['id'] = mun.id.astype(int); mun = mun[mun.id.isin(RMSP)].set_crs(4326)
crs = 31983; P = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts.long, pts.lat), crs=4326).to_crs(crs); mun_p = mun.to_crs(crs)
mun_geom = dict(zip(mun_p.id, mun_p.geometry)); cells = []
inside = np.array([mun_geom[int(m)].contains(g) for m, g in zip(P.cod_localidade_ibge, P.geometry)])
print('points outside their own municipality:', int((~inside).sum()))
for mid, grp in P.groupby('cod_localidade_ibge'):
    poly = mun_geom[int(mid)]; vd = voronoi_diagram(unary_union(grp.geometry.values), envelope=poly.buffer(5000))
    ix = gpd.GeoDataFrame(geometry=list(vd.geoms), crs=crs); j = gpd.sjoin(ix, grp[['geometry']], predicate='contains', how='inner')
    j['geometry'] = j.geometry.intersection(poly); j = j[~j.geometry.is_empty]; cells.append(j.set_index('index_right'))
cells = pd.concat(cells); vor = gpd.GeoDataFrame(pd.DataFrame({'i': P.index}).join(cells[['geometry']], how='inner'), geometry='geometry', crs=crs)
vor['geometry'] = vor.geometry.simplify(8); vor = vor.to_crs(4326)
def rnd(o):
    if isinstance(o, list): return [rnd(x) for x in o]
    if isinstance(o, float): return round(o, 5)
    if isinstance(o, dict): return {k: rnd(x) for k, x in o.items()}
    return o
gj = rnd(json.loads(vor[['i', 'geometry']].to_json(drop_id=True)))
area = mun_p.area.sum(); r = np.sqrt(pts.total.values / pts.total.sum() * area * 0.3 / np.pi)
P4 = P.to_crs(4326); dor = [[round(y, 5), round(x, 5), int(rr)] for x, y, rr in zip(P4.geometry.x, P4.geometry.y, r)]
ren = {'NM_LOCAL_VOTACAO': 'nome', 'DS_LOCAL_VOTACAO_ENDERECO': 'end', 'NR_ZONA': 'zona', 'NR_LOCAL_VOTACAO': 'nr', 'ds_bairro': 'bairro', 'municipio': 'mun'}
props = json.loads(pts.reset_index().rename(columns=ren | {'index': 'i'})[['i', 'mun', 'zona', 'nr', 'nome', 'end', 'bairro', 'n_secoes', 'n_secoes_tot', 'n_locais', 'total']].to_json(orient='records'))

# --- text ---
done = int(pts.n_secoes.sum())
pct_done = 100 * done / n_total
ts = f"{cs['dg']} {cs['hg']}"
partial = f'Apuração parcial: {done:,} de {n_total:,} seções da RMSP ({pct_done:.1f}%), boletins publicados até {ts}. '.replace(',', '.') if done < n_total else ''
title = 'Eleições gerais 2026 — 1º turno — RMSP'
note = (partial + 'Majoritários (presidente, governador, senador): os 3 mais votados na RMSP, com polos pela correlação (Pearson, entre '
        'locais) da fração de cada um com a fração de Lula no mesmo local em 2026: laranja = mais correlato a Lula, verde-azulado = mais '
        'correlato ao polo oposto, roxo = intermediário; se os 2 primeiros somam ≥85% dos válidos, escala bipolar entre eles. Presidente: '
        'como nos mapas de 2º turno, vermelho = Lula, azul = Flávio Bolsonaro, fração de Lula entre os dois, escala ajustada ao '
        'percentil 95 dos locais. Senador: '
        'cada eleitor votou em 2 nomes, então o mapa compara as duas chapas (coligações) mais votadas, somando os votos dos '
        'dois candidatos de cada uma; percentuais sobre o total de votos válidos para senador. Deputados: fração dos votos válidos do local '
        '(nominais + legenda) do candidato ou do partido. Fontes: TSE, boletins de urna por seção (resultados.tse.jus.br); locais de votação '
        'e coordenadas: TSE, eleitorado por local de votação 2026; limites IBGE. Locais no mesmo endereço foram agregados.')
tri_svg = []
Pt = np.array([[75, 8], [8, 122], [142, 122]]); NN = 12
for a in range(NN):
    for b in range(NN - a):
        c3 = NN - a - b
        for t_ in ([(a, b, c3), (a + 1, b, c3 - 1), (a, b + 1, c3 - 1)], [(a + 1, b, c3 - 1), (a + 1, b + 1, c3 - 2), (a, b + 1, c3 - 1)] if c3 >= 2 else []):
            if not t_: continue
            bc = np.array(t_) / NN; cen = bc.mean(0); d = min(max((cen.max() - 1 / 3) / (0.6 - 1 / 3), 0), 1); vec = (cen - 1 / 3) @ E[:, 1:]
            ang = np.arctan2(vec[1], vec[0]); Cr = 0.14 * np.sqrt(d); cc = hexs(oklab_to_rgb(np.array([[0.60, Cr * np.cos(ang), Cr * np.sin(ang)]])))[0]
            tri_svg.append(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in bc @ Pt)}" fill="{cc}" stroke="{cc}" stroke-width="0.5"/>')
bundle = dict(title=title, vor=gj, dor=dor, props=props, nloc=f'{N:,}'.replace(',', '.'), summary='', note=note, legend='', cargos=C,
              tri=''.join(tri_svg), poles=hexs(oklab_to_rgb(E)), partial=partial, n_done=done, n_total=n_total)
json.dump(bundle, open('bundle_2026.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('bundle_2026.json written', partial)
