# Applies overrides.py to the published artifacts in place (HTML bundle, CSVs, 2T gpkg), for when the
# raw pipeline inputs (geocoded stations etc.) aren't at hand. Idempotent. Run from the repo root:
#   uv run --no-project --with geopandas --with matplotlib python scripts/apply_overrides.py
import json, re, sys, numpy as np, pandas as pd, geopandas as gpd, pyogrio, matplotlib
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
sys.path.insert(0,'scripts'); from overrides import POLE_OVERRIDES, assign_poles, sort_key_2t
exec(open('scripts/tri2024.py').read().split('# OKLab helpers')[1].split('# endpoints')[0])
def okc(L,C,h): h=np.radians(h); return np.array([L,C*np.cos(h),C*np.sin(h)])
E=np.stack([okc(0.60,0.14,55),okc(0.60,0.14,175),okc(0.60,0.14,295)]); gray=E.mean(0)
RED,BLUE='#b0142a','#2c3e9e'; cmap=LinearSegmentedColormap.from_list('rb',[BLUE,'#7f95d6','#e4e4e4','#e69a86',RED])
MUNS=set(POLE_OVERRIDES)

def color_1t(v,present,triway):  # same formula as tri2024b.py, one location
    V=np.asarray(v,float)*present; tot=V.sum(); w=V/tot if tot>0 else present/present.sum()
    if triway:
        d=np.clip((w.max()-1/3)/(0.6-1/3),0,1); vec=(w-1/3)@E[:,1:]; ang=np.arctan2(vec[1],vec[0]); C=0.14*np.sqrt(d)
        lab=np.array([0.60,C*np.cos(ang),C*np.sin(ang)])
    else:
        pi=int(np.argmax(present)); pj=2-int(np.argmax(present[::-1])); t=np.clip((w[pi]-0.25)/0.5,0,1)
        lab=E[pi]*(2*(t-0.5))+gray*(1-2*(t-0.5)) if t>=0.5 else E[pj]*(1-2*t)+gray*(2*t)
    return hexs(oklab_to_rgb(lab[None]))[0]

def perm_1t(m,nr,r):
    """nr, r: per-pole lists (None where absent). returns perm with perm[new_pole]=old_pole, or None if unchanged."""
    cand=sorted([(r[k],nr[k],k) for k in range(3) if nr[k] is not None and not pd.isna(nr[k])],key=lambda x:-x[0])
    poles=assign_poles(m,[int(float(c[1])) for c in cand]); perm=[None]*3
    for (_,_,k),p in zip(cand,poles): perm[p]=k
    free=[k for k in range(3) if k not in perm]
    perm=[k if k is not None else free.pop(0) for k in perm]
    return None if perm==[0,1,2] else perm

def permute(d,perm,fields):  # fields: list of (prefix) with suffix k
    old={f:[d[f'{f}{k}'] for k in range(3)] for f in fields}
    for f in fields:
        for p in range(3): d[f'{f}{p}']=old[f][perm[p]]

# ---------- HTML ----------
H='rmsp_eleicoes_2022_2024_locais.html'; t=open(H).read(); dec=json.JSONDecoder()
def seg(tag):
    i=t.index(tag)+len(tag); o,e=dec.raw_decode(t,i); return i,e,o
i24,e24,b24=seg(",'2024':"); i2t,e2t,b2t=seg(",'2024_2T':")
dump=lambda o: json.dumps(o,ensure_ascii=False,separators=(',',':'))
assert dump(b24)==t[i24:e24] and dump(b2t)==t[i2t:e2t], 'bundle does not round-trip'
CD={}  # municipality name -> code, from the 2T csv / 1T csv
for f in ['rmsp_prefeito_2024_1T_locais.csv','rmsp_prefeito_2024_2T_locais.csv']:
    CD.update(pd.read_csv(f,usecols=['CD_MUNICIPIO','municipio']).drop_duplicates().set_index('municipio').CD_MUNICIPIO.to_dict())
F1=['s','v','NM_VOTAVEL_','NR_VOTAVEL_','SG_','rank_','r_lula22_']
n1=bad=0
for d in b24['props']+[f['properties'] for f in b24['vor']['features']]:
    m=CD[d['mun']]; present=np.array([d[f'NR_VOTAVEL_{k}'] is not None for k in range(3)])
    if m in MUNS:
        perm=perm_1t(m,[d[f'NR_VOTAVEL_{k}'] for k in range(3)],[d[f'r_lula22_{k}'] for k in range(3)])
        if perm: permute(d,perm,F1); present=present[perm]; d['color']=color_1t([d[f'v{k}'] for k in range(3)],present,d['triway']); n1+=1
    elif color_1t([d[f'v{k}'] for k in range(3)],present,d['triway'])!=d['color']: bad+=1
print('1T: recolored',n1,'| untouched locations whose recomputed color differs:',bad)
lo,hi=map(int,re.search(r'<span>≥(\d+)% cand\. azul</span><span>50/50</span><span>≥(\d+)%',b2t['legend']).groups()); lo=100-lo
norm=TwoSlopeNorm(vmin=lo,vcenter=50,vmax=hi); c2t=lambda pct: matplotlib.colors.to_hex(cmap(norm(pct)))
def swap_2t(d,pct='pct'):
    for a,b in [('va','vb'),('nmA','nmB'),('sgA','sgB'),('nrA','nrB'),('rA','rB')]: d[a],d[b]=d[b],d[a]
    d[pct]=round(100-d[pct],1)
def needs_swap(m,d): return sort_key_2t(m,d['nrB'],d['rB'])>sort_key_2t(m,d['nrA'],d['rA'])
n2=bad=0
for d in b2t['props']+[f['properties'] for f in b2t['vor']['features']]:
    m=CD[d['mun']]
    if needs_swap(m,d): swap_2t(d); d['color']=c2t(d['pct']); n2+=1
    elif c2t(d['pct'])!=d['color']: bad+=1
print('2T: swapped',n2,'| untouched locations whose recomputed color differs:',bad)
# per-municipality pair list in the 2T legend
pairs={}
for d in b2t['props']: pairs.setdefault(d['mun'],d)
tc=lambda s:' '.join(str(s).title().split()[:2])
lines='<br>'.join(f"<b>{mn}</b>: <span style='color:{RED}'>{r['sgA']} {tc(r['nmA'])}</span> (r={r['rA']:+.2f}) vs. <span style='color:{BLUE}'>{r['sgB']} {tc(r['nmB'])}</span> (r={r['rB']:+.2f})" for mn,r in sorted(pairs.items()))
b2t['legend']=re.sub(r'(<div style="font-size:11px;margin-top:6px;line-height:1.35">).*?(</div>)$',lambda mm: mm.group(1)+lines+mm.group(2),b2t['legend'])
OV1=' Ajustes manuais (onde a correlação rotula mal o candidato): São Caetano PODE outlier, PL ~Bolsonaro; Itapevi PSB ~Lula, PODE outlier; Taboão da Serra PSDB ~Lula, PODE outlier, UNIÃO ~Bolsonaro; Diadema MDB outlier.'
OV2=' Ajustes manuais: Mauá PT vermelho; Taboão da Serra UNIÃO azul (~Bolsonaro).'
NOTE1=b24['note'].split(' Ajustes manuais')[0].split(' Fontes:'); b24['note']=NOTE1[0]+OV1+' Fontes:'+NOTE1[1]
NOTE2=b2t['note'].split(' Ajustes manuais')[0].split(' Fontes:'); b2t['note']=NOTE2[0]+OV2+' Fontes:'+NOTE2[1]
t=t[:i24]+dump(b24)+t[e24:i2t]+dump(b2t)+t[e2t:]
open(H,'w').write(t)

# ---------- CSVs ----------
F1c=['v','NR_VOTAVEL_','NM_VOTAVEL_','share_','r_lula22_','rank_','s']
for f in ['data/rmsp_prefeito_2024_1T_polos_por_municipio.csv','data/rmsp_prefeito_2024_1T_polos_por_local.csv']:
    df=pd.read_csv(f,float_precision='round_trip',dtype={f'NR_VOTAVEL_{k}':str for k in range(3)})  # keep their text form as-is
    for idx,row in df.iterrows():
        m=row.CD_MUNICIPIO
        if m in MUNS:
            perm=perm_1t(m,[row[f'NR_VOTAVEL_{k}'] if pd.notna(row[f'NR_VOTAVEL_{k}']) else None for k in range(3)],[row[f'r_lula22_{k}'] for k in range(3)])
            if perm:
                d=row.to_dict(); permute(d,[p for p in perm],[c for c in F1c if f'{c}0' in d])
                if 'color' in d: d['color']=color_1t([d[f'v{k}'] for k in range(3)],np.array([pd.notna(d[f'NR_VOTAVEL_{k}']) for k in range(3)]),d['triway'])
                for c,x in d.items(): df.at[idx,c]=x
    df.to_csv(f,index=False)
# 2T csv + gpkg: swap A/B
f='rmsp_prefeito_2024_2T_locais.csv'; df=pd.read_csv(f,float_precision='round_trip')
sw=[needs_swap(m,dict(nrA=a,nrB=b,rA=ra,rB=rb)) for m,a,b,ra,rb in zip(df.CD_MUNICIPIO,df.nrA,df.nrB,df.rA,df.rB)]; sw=np.array(sw)
for a,b in [('va','vb'),('nmA','nmB'),('sgA','sgB'),('nrA','nrB'),('rA','rB')]: df.loc[sw,[a,b]]=df.loc[sw,[b,a]].values
df.loc[sw,'pct']=100-df.loc[sw,'pct']; df.loc[sw,'shareA']=1-df.loc[sw,'shareA']; df.to_csv(f,index=False); print('2T csv swapped',sw.sum())
G='rmsp_prefeito_2024_2T_locais.gpkg'; layers=[l for l,_ in pyogrio.list_layers(G)]; gs={l:gpd.read_file(G,layer=l) for l in layers}
for l in ('locais_voronoi','locais_pontos'):
    g=gs[l]; m=g.municipio.map(CD)
    sw=np.array([needs_swap(mm,dict(nrA=a,nrB=b,rA=ra,rB=rb)) for mm,a,b,ra,rb in zip(m,g.nrA,g.nrB,g.rA,g.rB)])
    for a,b in [('va','vb'),('nmA','nmB'),('sgA','sgB'),('nrA','nrB'),('rA','rB')]: g.loc[sw,[a,b]]=g.loc[sw,[b,a]].values
    g.loc[sw,'pct']=100-g.loc[sw,'pct']; print('2T gpkg',l,'swapped',sw.sum())
import os; tmp=G+'.tmp'
for k,l in enumerate(layers): gs[l].to_file(tmp,layer=l,driver='GPKG',mode='w' if k==0 else 'a')
os.replace(tmp,G)
