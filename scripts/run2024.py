import pandas as pd, geopandas as gpd, numpy as np, json
from shapely.ops import voronoi_diagram, unary_union
LEFT={13,50,65,12,40,18,43,16,21,29,80}; RIGHT={22,30,28,10,11,44,55,45,15,20,70,77,36,27,25,33,35,23}
RMSP=json.load(open('rmsp_codes.json')) if False else None
exec(open('agg.py').read().split('geo = pd.read_csv')[0])  # RMSP dict
g=pd.read_csv('geocoded_polling_stations.csv.gz',low_memory=False); g=g[(g.ano==2024)&(g.sg_uf=='SP')&(g.cod_localidade_ibge.isin(RMSP))].copy()
print('geo 2024 RMSP',len(g))
v=pd.read_csv('prefeito_1t_rmsp_2024.csv.gz',sep=';',encoding='latin1')
v['bloc']=np.where(v.NR_VOTAVEL.isin(LEFT),'left',np.where(v.NR_VOTAVEL.isin(RIGHT),'right',np.where(v.NR_VOTAVEL==95,'branco',np.where(v.NR_VOTAVEL==96,'nulo','other'))))
print(v[v.bloc=='other'].groupby(['NM_MUNICIPIO','NR_VOTAVEL']).QT_VOTOS.sum().sort_values(ascending=False).head(10))
key=['CD_MUNICIPIO','NM_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO','NM_LOCAL_VOTACAO','DS_LOCAL_VOTACAO_ENDERECO']
piv=v.pivot_table(index=key,columns='bloc',values='QT_VOTOS',aggfunc='sum',fill_value=0).reset_index()
for c in ['left','right','branco','nulo','other']:
    if c not in piv: piv[c]=0
# top candidate per locale
cand=v[~v.NR_VOTAVEL.isin([95,96])].groupby(key+['NR_VOTAVEL','NM_VOTAVEL']).QT_VOTOS.sum().reset_index()
top=cand.sort_values('QT_VOTOS',ascending=False).drop_duplicates(key)[key+['NR_VOTAVEL','NM_VOTAVEL','QT_VOTOS']].rename(columns={'NR_VOTAVEL':'top_nr','NM_VOTAVEL':'top_nome','QT_VOTOS':'top_votos'})
piv=piv.merge(top,on=key,how='left')
piv['validos']=piv.left+piv.right+piv.other; piv['total']=piv.validos+piv.branco+piv.nulo
piv['left_pct']=100*piv.left/(piv.left+piv.right)
piv['n_secoes']=v.groupby(['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']).NR_SECAO.nunique().reindex(pd.MultiIndex.from_frame(piv[['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']])).values
g2=g[['cd_localidade_tse','cod_localidade_ibge','nr_zona','nr_locvot','long','lat','ds_bairro']].copy(); g2['nr_zona']=g2.nr_zona.astype(int)
m=piv.merge(g2,left_on=['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO'],right_on=['cd_localidade_tse','nr_zona','nr_locvot'],how='left').drop_duplicates(['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO'])
print('locales',len(m),'unmatched',m.long.isna().sum(), 'totals', m[['left','right','other','branco','nulo']].sum().to_dict())
m['municipio']=m.cod_localidade_ibge.map(RMSP)
m.to_csv('rmsp_locais_2024_1t.csv',index=False)
m=m.dropna(subset=['long','lat']); m['lon_r']=m.long.round(5); m['lat_r']=m.lat.round(5)
agg=m.groupby(['cod_localidade_ibge','municipio','lon_r','lat_r'],as_index=False).agg(NR_ZONA=('NR_ZONA',lambda x:'/'.join(sorted(set(map(str,x))))),NR_LOCAL_VOTACAO=('NR_LOCAL_VOTACAO',lambda x:'/'.join(sorted(set(map(str,x))))),NM_LOCAL_VOTACAO=('NM_LOCAL_VOTACAO',lambda x:' | '.join(sorted(set(x)))),DS_LOCAL_VOTACAO_ENDERECO=('DS_LOCAL_VOTACAO_ENDERECO','first'),ds_bairro=('ds_bairro','first'),left=('left','sum'),right=('right','sum'),other=('other','sum'),branco=('branco','sum'),nulo=('nulo','sum'),validos=('validos','sum'),total=('total','sum'),n_secoes=('n_secoes','sum'),n_locais=('left','size'),top_nome=('top_nome','first'),top_nr=('top_nr','first'))
agg['left_pct']=100*agg.left/(agg.left+agg.right)
agg=agg.rename(columns={'lon_r':'long','lat_r':'lat'})
pts=gpd.GeoDataFrame(agg,geometry=gpd.points_from_xy(agg.long,agg.lat),crs=4326).to_crs(31983)
mun=gpd.read_file('rmsp_municipios.gpkg').to_crs(31983); mg=dict(zip(mun.id,mun.geometry))
cells=[]
for mid,grp in pts.groupby('cod_localidade_ibge'):
    poly=mg[int(mid)]; vd=voronoi_diagram(unary_union(grp.geometry.values),envelope=poly.buffer(5000))
    idx=gpd.GeoDataFrame(geometry=list(vd.geoms),crs=31983); j=gpd.sjoin(idx,grp[['geometry']],predicate='contains',how='inner')
    j['geometry']=j.geometry.intersection(poly); j=j[~j.geometry.is_empty]; cells.append(j.set_index('index_right'))
cells=pd.concat(cells); vor=gpd.GeoDataFrame(pts.drop(columns='geometry').join(cells[['geometry']],how='inner'),geometry='geometry',crs=31983)
print('cells',len(vor))
vor.to_file('rmsp_voronoi_2024.gpkg',driver='GPKG'); pts.to_file('rmsp_pontos_2024.gpkg',driver='GPKG')
