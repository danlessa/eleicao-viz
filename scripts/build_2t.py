import pandas as pd, geopandas as gpd, numpy as np
from shapely.ops import voronoi_diagram, unary_union
from overrides import sort_key_2t
exec(open('agg.py').read().split('geo = pd.read_csv')[0])
PARTY={10:'REPUBLICANOS',11:'PP',12:'PDT',13:'PT',15:'MDB',16:'PSTU',18:'REDE',20:'PODE',21:'PCB',22:'PL',23:'CIDADANIA',25:'PRD',27:'DC',28:'PRTB',29:'PCO',30:'NOVO',33:'MOBILIZA',35:'PMB',36:'AGIR',40:'PSB',43:'PV',44:'UNIÃO',45:'PSDB',50:'PSOL',55:'PSD',65:'PCdoB',70:'AVANTE',77:'SOLIDARIEDADE',80:'UP'}
LEFT={13,50,65,12,40,18,43,16,21,29,80}; RIGHT={22,30,28,10,11,44}
ct2=pd.read_csv('corr_2024_2t.csv')[['CD_MUNICIPIO','NR_VOTAVEL','r_lula22']]
v=pd.read_csv('prefeito_2t_rmsp_2024.csv.gz',sep=';',encoding='latin1')
key=['CD_MUNICIPIO','NM_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO','NM_LOCAL_VOTACAO','DS_LOCAL_VOTACAO_ENDERECO']
c=v[~v.NR_VOTAVEL.isin([95,96])].groupby(['CD_MUNICIPIO','NR_VOTAVEL','NM_VOTAVEL']).QT_VOTOS.sum().reset_index().sort_values(['CD_MUNICIPIO','QT_VOTOS'],ascending=[True,False])
# pole A (red) = more progressive of the pair (manual overrides in overrides.py); tie -> municipal winner
rows=[]
for m,g in c.groupby('CD_MUNICIPIO'):
    g=g.merge(ct2,on=['CD_MUNICIPIO','NR_VOTAVEL'],how='left').fillna({'r_lula22':0}); g['k']=[sort_key_2t(m,nr,r) for nr,r in zip(g.NR_VOTAVEL,g.r_lula22)]; g=g.sort_values(['k','QT_VOTOS'],ascending=[False,False]); a,b=g.iloc[0],g.iloc[1]
    rows.append(dict(CD_MUNICIPIO=m,nrA=a.NR_VOTAVEL,nmA=a.NM_VOTAVEL,sgA=PARTY.get(a.NR_VOTAVEL,'?'),nrB=b.NR_VOTAVEL,nmB=b.NM_VOTAVEL,sgB=PARTY.get(b.NR_VOTAVEL,'?'),rA=round(a.r_lula22,2),rB=round(b.r_lula22,2),shareA=a.QT_VOTOS/(a.QT_VOTOS+b.QT_VOTOS)))
info=pd.DataFrame(rows); print(info[['nmA','sgA','rA','nmB','sgB','rB','shareA']].round(3).to_string())
v=v.merge(info[['CD_MUNICIPIO','nrA','nrB']],on='CD_MUNICIPIO')
v['k']=np.select([v.NR_VOTAVEL==v.nrA,v.NR_VOTAVEL==v.nrB,v.NR_VOTAVEL==95,v.NR_VOTAVEL==96],['va','vb','branco','nulo'],'x')
piv=v.pivot_table(index=key,columns='k',values='QT_VOTOS',aggfunc='sum',fill_value=0).reset_index()
piv['validos']=piv.va+piv.vb; piv['total']=piv.validos+piv.branco+piv.nulo; piv['pct']=100*piv.va/piv.validos
piv['n_secoes']=v.groupby(['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']).NR_SECAO.nunique().reindex(pd.MultiIndex.from_frame(piv[['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']])).values
g=pd.read_csv('geo_sp_2022.csv') if False else pd.read_csv('geocoded_polling_stations.csv.gz',low_memory=False)
g=g[(g.ano==2024)&(g.sg_uf=='SP')&(g.cod_localidade_ibge.isin(RMSP))][['cd_localidade_tse','cod_localidade_ibge','nr_zona','nr_locvot','long','lat','ds_bairro']].copy(); g['nr_zona']=g.nr_zona.astype(int)
m=piv.merge(g,left_on=['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO'],right_on=['cd_localidade_tse','nr_zona','nr_locvot'],how='left').drop_duplicates(['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO'])
print('locales',len(m),'unmatched',m.long.isna().sum(),'totals',m[['va','vb']].sum().to_dict())
m['municipio']=m.cod_localidade_ibge.map(RMSP); m=m.merge(info,on='CD_MUNICIPIO')
m.to_csv('rmsp_locais_2024_2t.csv',index=False)
m=m.dropna(subset=['long','lat']); m['lon_r']=m.long.round(5); m['lat_r']=m.lat.round(5)
agg=m.groupby(['cod_localidade_ibge','municipio','lon_r','lat_r'],as_index=False).agg(NR_ZONA=('NR_ZONA',lambda x:'/'.join(sorted(set(map(str,x))))),NR_LOCAL_VOTACAO=('NR_LOCAL_VOTACAO',lambda x:'/'.join(sorted(set(map(str,x))))),NM_LOCAL_VOTACAO=('NM_LOCAL_VOTACAO',lambda x:' | '.join(sorted(set(x)))),DS_LOCAL_VOTACAO_ENDERECO=('DS_LOCAL_VOTACAO_ENDERECO','first'),ds_bairro=('ds_bairro','first'),va=('va','sum'),vb=('vb','sum'),branco=('branco','sum'),nulo=('nulo','sum'),validos=('validos','sum'),total=('total','sum'),n_secoes=('n_secoes','sum'),n_locais=('va','size'),nrA=('nrA','first'),nmA=('nmA','first'),sgA=('sgA','first'),nrB=('nrB','first'),nmB=('nmB','first'),sgB=('sgB','first'),rA=('rA','first'),rB=('rB','first'))
agg['pct']=100*agg.va/agg.validos; agg=agg.rename(columns={'lon_r':'long','lat_r':'lat'})
pts=gpd.GeoDataFrame(agg,geometry=gpd.points_from_xy(agg.long,agg.lat),crs=4326).to_crs(31983)
mun=gpd.read_file('rmsp_municipios.gpkg').to_crs(31983); mg=dict(zip(mun.id,mun.geometry)); cells=[]
for mid,grp in pts.groupby('cod_localidade_ibge'):
    poly=mg[int(mid)]; vd=voronoi_diagram(unary_union(grp.geometry.values),envelope=poly.buffer(5000))
    idx=gpd.GeoDataFrame(geometry=list(vd.geoms),crs=31983); j=gpd.sjoin(idx,grp[['geometry']],predicate='contains',how='inner')
    j['geometry']=j.geometry.intersection(poly); j=j[~j.geometry.is_empty]; cells.append(j.set_index('index_right'))
cells=pd.concat(cells); vor=gpd.GeoDataFrame(pts.drop(columns='geometry').join(cells[['geometry']],how='inner'),geometry='geometry',crs=31983)
print('cells',len(vor)); vor.to_file('rmsp_voronoi_2024_2t.gpkg',driver='GPKG'); pts.to_file('rmsp_pontos_2024_2t.gpkg',driver='GPKG')
