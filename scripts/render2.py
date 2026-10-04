import sys, json, numpy as np, pandas as pd, geopandas as gpd, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle
Y=sys.argv[1]
PARTY={10:'REPUBLICANOS',11:'PP',12:'PDT',13:'PT',15:'MDB',16:'PSTU',18:'REDE',20:'PODE',21:'PCB',22:'PL',23:'CIDADANIA',25:'PRD',27:'DC',28:'PRTB',29:'PCO',30:'NOVO',33:'MOBILIZA',35:'PMB',36:'AGIR',40:'PSB',43:'PV',44:'UNIÃO',45:'PSDB',50:'PSOL',55:'PSD',65:'PCdoB',70:'AVANTE',77:'SOLIDARIEDADE',80:'UP'}
cmap=LinearSegmentedColormap.from_list('lb',['#009a7b','#7fbfae','#9a9a9a','#d4a06e','#be6517']); norm=TwoSlopeNorm(vmin=25,vcenter=50,vmax=75)
mu=gpd.read_file('rmsp_municipios.gpkg').to_crs(31983); mu['c']=mu.geometry.representative_point()
if Y=='2022':
    v=gpd.read_file('rmsp_voronoi.gpkg').to_crs(31983); p=gpd.read_file('rmsp_pontos.gpkg').to_crs(31983)
    for d in (v,p):
        d['color']=[matplotlib.colors.to_hex(cmap(norm(x))) for x in d.lula_pct]; d['va'],d['vb'],d['pct']=d.lula,d.bolsonaro,d.lula_pct.round(1); d['w']=d.lula+d.bolsonaro
    title='Eleição presidencial 2022 — 2º turno — RMSP'; out='rmsp_presidente_2022_2T'; A,B='Lula','Bolsonaro'
    note='Fontes: TSE, votação por seção 2022 (dados abertos); coordenadas dos locais: TSE via fdhidalgo/geocode_br_polling_stations; limites IBGE. Locais no mesmo endereço foram agregados.'
    L,Bv=v.lula.sum(),v.bolsonaro.sum(); summary=f'RMSP: Lula {100*L/(L+Bv):.1f}% · Bolsonaro {100*Bv/(L+Bv):.1f}% dos válidos'
    legend_html='<div style="font-size:12px;margin-bottom:4px"><span style="color:#be6517;font-weight:600">Lula</span> vs. <span style="color:#009a7b;font-weight:600">Bolsonaro</span></div><div class="bar" style="width:260px"></div><div class="ticks" style="width:260px"><span>≥75% Bolsonaro</span><span>50/50</span><span>≥75% Lula</span></div>'
else:
    v=gpd.read_file('rmsp_voronoi_2024.gpkg').to_crs(31983); p=gpd.read_file('rmsp_pontos_2024.gpkg').to_crs(31983)
    tri=pd.read_csv('tri_agg_2024.csv'); tri['long']=tri.long.round(5); tri['lat']=tri.lat.round(5)
    keep=['cod_localidade_ibge','long','lat','color','s0','s1','s2','v0','v1','v2','triway','NM_VOTAVEL_0','NM_VOTAVEL_1','NM_VOTAVEL_2','NR_VOTAVEL_0','NR_VOTAVEL_1','NR_VOTAVEL_2','rank_0','rank_1','rank_2','r_lula22_0','r_lula22_1','r_lula22_2']
    def mg(d):
        d=d.copy(); d['long']=d.long.round(5); d['lat']=d.lat.round(5); d=d.merge(tri[keep],on=['cod_localidade_ibge','long','lat'],how='left'); d['w']=d.v0+d.v1+d.v2; return d[d.color.notna()]
    v=mg(v); p=mg(p)
    for d in (v,p):
        for k in range(3): d[f'SG_{k}']=d[f'NR_VOTAVEL_{k}'].map(lambda x: PARTY.get(int(x),'?') if pd.notna(x) else None).astype(object).where(d[f'NR_VOTAVEL_{k}'].notna(),None)
    title='Eleições municipais 2024 — 1º turno, prefeito — RMSP'; out='rmsp_prefeito_2024_1T'; A,B='esquerda','direita'
    note='Polos definidos empiricamente por município: correlação (Pearson, entre locais de votação) entre a fração de votos de cada candidato e a fração de Lula no 2º turno de 2022 no mesmo local. Laranja = candidato mais correlacionado com Lula, verde-azulado = mais correlacionado com Bolsonaro (r mais negativo), roxo = o intermediário (mais próximo de não-correlacionado). O r de cada candidato aparece no hover. Onde os dois primeiros somam ≥85% dos válidos a escala é bipolar (cinza = empate); nos demais, mistura ternária dos três em OKLab (cinza = três iguais). Ajustes manuais (onde a correlação rotula mal o candidato): São Caetano PODE outlier, PL ~Bolsonaro; Itapevi PSB ~Lula, PODE outlier; Taboão da Serra PSDB ~Lula, PODE outlier, UNIÃO ~Bolsonaro; Diadema MDB outlier. Fontes: TSE, votação por seção 2024; coordenadas: TSE via fdhidalgo/geocode_br_polling_stations; limites IBGE.'
    summary='39 disputas municipais; '+str(int(tri.drop_duplicates("cod_localidade_ibge").triway.sum()))+' municípios com disputa de 3 (top-2 < 85%)'
    legend_html='<div style="font-size:12px;margin-bottom:4px"><span style="color:#be6517;font-weight:600">correlato a Lula 2022</span> · <span style="color:#009a7b;font-weight:600">correlato a Bolsonaro 2022</span> · <span style="color:#876cca;font-weight:600">outlier (menos correlato)</span></div><svg width="150" height="130" viewBox="0 0 150 130">__TRI__</svg><div style="font-size:11px;color:var(--muted)">Cada município tem seus próprios candidatos — veja no hover.</div>'
    # ternary triangle preview via python oklab
    exec(open('tri2024.py').read().split('# endpoints')[0].split('# OKLab helpers')[1])
    def okc(Lh,C,h): h=np.radians(h); return np.array([Lh,C*np.cos(h),C*np.sin(h)])
    E=np.stack([okc(0.60,0.14,55),okc(0.60,0.14,175),okc(0.60,0.14,295)])
    P=np.array([[75,8],[8,122],[142,122]]); polys=[]; N=12
    for i in range(N):
        for jj in range(N-i):
            k=N-i-jj
            for tri_ in ([(i,jj,k),(i+1,jj,k-1),(i,jj+1,k-1)],[(i+1,jj,k-1),(i+1,jj+1,k-2),(i,jj+1,k-1)] if k>=2 else []):
                if not tri_: continue
                bc=np.array(tri_)/N; cen=bc.mean(0); d=min(max((cen.max()-1/3)/(0.6-1/3),0),1); vec=(cen-1/3)@E[:,1:]; ang=np.arctan2(vec[1],vec[0]); C=0.14*np.sqrt(d); c=hexs(oklab_to_rgb(np.array([[0.60,C*np.cos(ang),C*np.sin(ang)]])))[0]
                pts_=bc@P; polys.append(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts_)}" fill="{c}" stroke="{c}" stroke-width="0.5"/>')
    legend_html=legend_html.replace('__TRI__',''.join(polys)+'<text x="75" y="6" font-size="9" text-anchor="middle" fill="#be6517">100% ~Lula</text><text x="8" y="129" font-size="9" fill="#009a7b">100% ~Bolsonaro</text><text x="142" y="129" font-size="9" text-anchor="end" fill="#876cca">100% outlier</text>')
def deco(fig,ax,sub):
    ax.set_axis_off(); ax.set_title(title+'\n'+sub,fontsize=15,loc='left',pad=14)
    for _,r in mu.iterrows(): ax.annotate(r['name'],(r.c.x,r.c.y),ha='center',va='center',fontsize=7 if r['name']!='São Paulo' else 11,color='#111',path_effects=[pe.withStroke(linewidth=2.2,foreground='white',alpha=0.9)])
    if Y=='2022':
        sm=plt.cm.ScalarMappable(cmap=cmap,norm=norm); sm.set_array([])
        cb=fig.colorbar(sm,ax=ax,orientation='horizontal',fraction=0.035,pad=0.02,aspect=45,ticks=[25,35,45,50,55,65,75]); cb.set_label('% de votos válidos — Lula (laranja) vs. Bolsonaro (verde-azulado)',fontsize=10)
        cb.ax.set_xticklabels(['≤25% Lula','35','45','50','55','65','≥75% Lula'],fontsize=8)
    else:
        info=tri.drop_duplicates('cod_localidade_ibge').merge(mu[['id','name']],left_on='cod_localidade_ibge',right_on='id').sort_values('name')
        lines=[]
        for rr in info.itertuples():
            f=lambda s: ' '.join(str(s).title().split()[:2])
            parts=[]
            for p,tag in ((0,'~Lula'),(1,'~Bolsonaro'),(2,'outlier')):
                nm=getattr(rr,f'NM_VOTAVEL_{p}'); sh=getattr(rr,f'share_{p}')
                if isinstance(nm,str): parts.append(f"{PARTY.get(int(getattr(rr,f'NR_VOTAVEL_{p}')),'?')} {f(nm)} [{tag}, r={getattr(rr,f'r_lula22_{p}'):+.2f}] {100*sh:.0f}%")
            lines.append(f"{rr.name}{' (3)' if rr.triway else ''}: "+' / '.join(parts))
        half=(len(lines)+1)//2
        fig.text(0.10,0.265,'\n'.join(lines[:half]),fontsize=6.5,va='top',color='#222')
        fig.text(0.52,0.265,'\n'.join(lines[half:]),fontsize=6.5,va='top',color='#222')
        fig.text(0.10,0.285,'Legenda por município — laranja = esquerda, verde-azulado = direita, roxo = outlier; "(3)" = disputa de três (top-2 < 85%), cor = mistura ternária.',fontsize=7.5,color='#444',va='top')
    fig.text(0.01,-0.03,summary+'\n'+note.replace(' Ajustes manuais','\nAjustes manuais'),fontsize=7.5,color='#444',va='bottom')
fig,ax=plt.subplots(figsize=(16,15 if Y=='2024' else 12.5),dpi=150); fig.patch.set_facecolor('white')
v.plot(color=v.color,ax=ax,linewidth=0.25,edgecolor='face'); mu.boundary.plot(ax=ax,linewidth=0.6,color='#333')
if Y=='2024': ax.set_position([0.03,0.30,0.94,0.66])
deco(fig,ax,'Resultado por local de votação (célula de Voronoi de cada local, recortada pelo município)')
fig.savefig(out+'_locais.png',dpi=150,bbox_inches='tight',facecolor='white'); plt.close(fig)
# html
p4=p.to_crs(4326); r=np.sqrt(p.w.values/p.w.sum()*mu.area.sum()*0.3/np.pi)
dor=[[round(y,5),round(x,5),int(rr)] for x,y,rr in zip(p4.geometry.x,p4.geometry.y,r)]
ren={'NM_LOCAL_VOTACAO':'nome','DS_LOCAL_VOTACAO_ENDERECO':'end','NR_ZONA':'zona','NR_LOCAL_VOTACAO':'nr','ds_bairro':'bairro','municipio':'mun'}
cols=['mun','zona','nr','nome','end','bairro','branco','nulo','validos','n_secoes','n_locais','color']+(['va','vb','pct'] if Y=='2022' else ['s0','s1','s2','v0','v1','v2','triway','NM_VOTAVEL_0','NM_VOTAVEL_1','NM_VOTAVEL_2','NR_VOTAVEL_0','NR_VOTAVEL_1','NR_VOTAVEL_2','SG_0','SG_1','SG_2','rank_0','rank_1','rank_2','r_lula22_0','r_lula22_1','r_lula22_2'])
vs=v.copy(); vs['geometry']=vs.geometry.simplify(8); vs=vs.to_crs(4326).rename(columns=ren)
def rnd(o):
    if isinstance(o,list): return [rnd(x) for x in o]
    if isinstance(o,float): return round(o,5)
    if isinstance(o,dict): return {k:rnd(x) for k,x in o.items()}
    return o
gj=rnd(json.loads(vs[cols+['geometry']].to_json(drop_id=True)))
props=json.loads(p.rename(columns=ren)[cols].to_json(orient='records'))
mun4=mu.drop(columns='c').copy(); mun4['geometry']=mun4.geometry.simplify(15); gj_m=rnd(json.loads(mun4.to_crs(4326)[['name','geometry']].to_json(drop_id=True)))
json.dump(dict(title=title,vor=gj,mun=gj_m,dor=dor,props=props,nloc=f'{len(v):,}'.replace(',','.'),summary=summary,note=note,legend=legend_html),open(f'bundle_{Y}.json','w'),ensure_ascii=False,separators=(',',':')); print('done',Y)
