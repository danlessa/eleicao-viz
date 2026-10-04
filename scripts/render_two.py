import sys, json, numpy as np, pandas as pd, geopandas as gpd, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
Y=sys.argv[1]
mu=gpd.read_file('rmsp_municipios.gpkg').to_crs(31983); mu['c']=mu.geometry.representative_point()
RED,BLUE='#b0142a','#2c3e9e'
cmap=LinearSegmentedColormap.from_list('rb',[BLUE,'#7f95d6','#e4e4e4','#e69a86',RED])
if Y=='2022':
    v=gpd.read_file('rmsp_voronoi.gpkg').to_crs(31983); p=gpd.read_file('rmsp_pontos.gpkg').to_crs(31983)
    for d in (v,p):
        d['va'],d['vb'],d['pct']=d.lula,d.bolsonaro,d.lula_pct; d['nmA'],d['sgA'],d['nrA'],d['nmB'],d['sgB'],d['nrB']='Luiz Inácio Lula da Silva','PT',13,'Jair Messias Bolsonaro','PL',22
    title='Eleição presidencial 2022 — 2º turno — RMSP'; out='rmsp_presidente_2022_2T'
    note='Fontes: TSE, votação por seção 2022 (dados abertos); coordenadas dos locais: TSE via fdhidalgo/geocode_br_polling_stations; limites IBGE. Locais no mesmo endereço foram agregados.'
    L,B_=v.va.sum(),v.vb.sum(); summary=f'RMSP: Lula {100*L/(L+B_):.1f}% · Bolsonaro {100*B_/(L+B_):.1f}% dos válidos'; lblA,lblB='Lula','Bolsonaro'
else:
    v=gpd.read_file('rmsp_voronoi_2024_2t.gpkg').to_crs(31983); p=gpd.read_file('rmsp_pontos_2024_2t.gpkg').to_crs(31983)
    title='Eleições municipais 2024 — 2º turno, prefeito — RMSP'; out='rmsp_prefeito_2024_2T'
    note='Sete municípios tiveram 2º turno (São Paulo, Guarulhos, São Bernardo, Diadema, Mauá, Barueri, Taboão da Serra). Vermelho = candidato cuja votação por local se correlaciona positivamente com a de Lula em 2022, azul = o outro (r no hover); cada município tem sua própria dupla (veja no hover). Ajustes manuais: Mauá PT vermelho; Taboão da Serra UNIÃO azul (~Bolsonaro). Fontes: TSE, votação por seção 2024; coordenadas: TSE via fdhidalgo/geocode_br_polling_stations; limites IBGE.'
    summary='7 municípios com 2º turno · '+str(len(v))+' locais'; lblA,lblB='cand. vermelho','cand. azul'
for d in (v,p): d['w']=d.va+d.vb; d['pct']=d.pct.round(1)
# data-driven symmetric range: 95th percentile of |pct-50|, at least ±10
dev=np.percentile(np.abs(v.pct-50),95); half=max(10,round(dev)); lo,hi=50-half,50+half
norm=TwoSlopeNorm(vmin=lo,vcenter=50,vmax=hi)
for d in (v,p): d['color']=[matplotlib.colors.to_hex(cmap(norm(x))) for x in d.pct]
print(Y,'range',lo,hi)
# static
fig,ax=plt.subplots(figsize=(16,12.5),dpi=150); fig.patch.set_facecolor('white')
v.plot(color=v.color,ax=ax,linewidth=0.25,edgecolor='face'); mu.boundary.plot(ax=ax,linewidth=0.6,color='#333'); ax.set_axis_off()
ax.set_title(title+'\nResultado por local de votação (célula de Voronoi de cada local, recortada pelo município)',fontsize=15,loc='left',pad=14)
for _,r in mu.iterrows(): ax.annotate(r['name'],(r.c.x,r.c.y),ha='center',va='center',fontsize=7 if r['name']!='São Paulo' else 11,color='#111',path_effects=[pe.withStroke(linewidth=2.2,foreground='white',alpha=0.9)])
sm=plt.cm.ScalarMappable(cmap=cmap,norm=norm); sm.set_array([])
cb=fig.colorbar(sm,ax=ax,orientation='horizontal',fraction=0.035,pad=0.02,aspect=45,ticks=[lo,50,hi]); cb.set_label(f'% de votos válidos — {lblA} (vermelho) vs. {lblB} (azul); escala ajustada ao percentil 95 dos locais',fontsize=10)
cb.ax.set_xticklabels([f'≤{lo}% {lblA}\n(≥{hi}% {lblB})','50/50',f'≥{hi}% {lblA}\n(≤{lo}% {lblB})'],fontsize=8)
if Y!='2022':
    info=v.drop_duplicates('municipio').sort_values('municipio')
    tc=lambda s:' '.join(str(s).title().split()[:2])
    fig.text(0.01,-0.03,'\n'.join(f"{r.municipio}: {r.sgA} {tc(r.nmA)} (vermelho) vs. {r.sgB} {tc(r.nmB)} (azul)" for r in info.itertuples()),fontsize=7.5,color='#222',va='top')
    fig.text(0.01,-0.03-0.012*len(info)-0.01,note.replace(' Ajustes manuais','\nAjustes manuais'),fontsize=7.5,color='#444',va='top')
else: fig.text(0.01,-0.03,summary+'\n'+note,fontsize=7.5,color='#444',va='top')
fig.savefig(out+'_locais.png',dpi=150,bbox_inches='tight',facecolor='white'); plt.close(fig)
# bundle
p4=p.to_crs(4326); r=np.sqrt(p.w.values/p.w.sum()*mu.area.sum()*0.3/np.pi)
dor=[[round(y,5),round(x,5),int(rr)] for x,y,rr in zip(p4.geometry.x,p4.geometry.y,r)]
ren={'NM_LOCAL_VOTACAO':'nome','DS_LOCAL_VOTACAO_ENDERECO':'end','NR_ZONA':'zona','NR_LOCAL_VOTACAO':'nr','ds_bairro':'bairro','municipio':'mun'}
cols=['mun','zona','nr','nome','end','bairro','branco','nulo','validos','n_secoes','n_locais','color','va','vb','pct','nmA','sgA','nrA','nmB','sgB','nrB']+(['rA','rB'] if 'rA' in v else [])
vs=v.copy(); vs['geometry']=vs.geometry.simplify(8); vs=vs.to_crs(4326).rename(columns=ren)
def rnd(o):
    if isinstance(o,list): return [rnd(x) for x in o]
    if isinstance(o,float): return round(o,5)
    if isinstance(o,dict): return {k:rnd(x) for k,x in o.items()}
    return o
gj=rnd(json.loads(vs[cols+['geometry']].to_json(drop_id=True))); props=json.loads(p.rename(columns=ren)[cols].to_json(orient='records'))
mun4=mu.drop(columns='c').copy(); mun4['geometry']=mun4.geometry.simplify(15); gj_m=rnd(json.loads(mun4.to_crs(4326)[['name','geometry']].to_json(drop_id=True)))
legend=f'<div style="font-size:12px;margin-bottom:4px"><span style="color:{RED};font-weight:600">{lblA}</span> vs. <span style="color:{BLUE};font-weight:600">{lblB}</span></div><div class="bar" style="width:260px;background:linear-gradient(90deg,{BLUE},#7f95d6,#e4e4e4,#e69a86,{RED})"></div><div class="ticks" style="width:260px"><span>≥{hi}% {lblB}</span><span>50/50</span><span>≥{hi}% {lblA}</span></div>'
if Y!='2022':
    info=v.drop_duplicates('municipio').sort_values('municipio'); tc=lambda s:' '.join(str(s).title().split()[:2])
    legend+='<div style="font-size:11px;margin-top:6px;line-height:1.35">'+'<br>'.join(f"<b>{r.municipio}</b>: <span style='color:{RED}'>{r.sgA} {tc(r.nmA)}</span> (r={r.rA:+.2f}) vs. <span style='color:{BLUE}'>{r.sgB} {tc(r.nmB)}</span> (r={r.rB:+.2f})" for r in info.itertuples())+'</div>'
json.dump(dict(title=title,vor=gj,mun=gj_m,dor=dor,props=props,nloc=f'{len(v):,}'.replace(',','.'),summary=summary,note=note,legend=legend),open(f'bundle_{Y}.json','w'),ensure_ascii=False,separators=(',',':')); print('done',Y)
