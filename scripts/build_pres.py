# Presidential 2nd round by polling place for any year (2006–2018; 2022 went through agg.py/build_geo.py).
# usage: python build_pres.py YEAR   (cwd needs pres2t_rmsp_YEAR.csv.gz, geocoded_polling_stations.csv.gz, geojs-35-mun.json)
# pres2t_rmsp_YEAR.csv.gz (in data/) = TSE votacao_secao_YEAR_BR.csv filtered to CD_CARGO 1, NR_TURNO 2 and the 39 RMSP
# municipalities. President votes are in the BR file, not the SP one; the 2006–2014 BR files have NR_LOCAL_VOTACAO.
import sys, pandas as pd, geopandas as gpd
from shapely.ops import voronoi_diagram, unary_union
exec(open('agg.py').read().split('geo = pd.read_csv')[0])
Y=int(sys.argv[1])
PRES={2006:(13,45),2010:(13,45),2014:(13,45),2018:(13,17)}  # (red = PT candidate, blue = the other finalist)
PARTY={13:'PT',45:'PSDB',17:'PSL'}
nrA,nrB=PRES[Y]
geo=pd.read_csv('geocoded_polling_stations.csv.gz',low_memory=False)
geo=geo[(geo.ano==Y)&(geo.sg_uf=='SP')&geo.cod_localidade_ibge.isin(RMSP)].copy()
v=pd.read_csv(f'pres2t_rmsp_{Y}.csv.gz',sep=';',encoding='latin1',low_memory=False); v=v[v.NR_TURNO==2]
names=v.groupby('NR_VOTAVEL').NM_VOTAVEL.first()
key=['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']
piv=v.pivot_table(index=key,columns='NR_VOTAVEL',values='QT_VOTOS',aggfunc='sum',fill_value=0).reset_index()
piv=piv.rename(columns={nrA:'va',nrB:'vb',95:'branco',96:'nulo'})[key+['va','vb','branco','nulo']]
piv['validos']=piv.va+piv.vb; piv['total']=piv.validos+piv.branco+piv.nulo
piv['n_secoes']=v.groupby(key).NR_SECAO.nunique().reindex(pd.MultiIndex.from_frame(piv[key])).values
# names/addresses: vote file when it has them (2018+), else the geocoded table
g=geo[['cd_localidade_tse','cod_localidade_ibge','nr_zona','nr_locvot','long','lat','nm_locvot','ds_endereco','ds_bairro']].rename(columns={'nm_locvot':'NM_LOCAL_VOTACAO','ds_endereco':'DS_LOCAL_VOTACAO_ENDERECO'})
if 'NM_LOCAL_VOTACAO' in v:
    nm=v.groupby(key)[['NM_LOCAL_VOTACAO','DS_LOCAL_VOTACAO_ENDERECO']].first().reset_index(); piv=piv.merge(nm,on=key); g=g.drop(columns=['NM_LOCAL_VOTACAO','DS_LOCAL_VOTACAO_ENDERECO'])
m=piv.merge(g,left_on=key,right_on=['cd_localidade_tse','nr_zona','nr_locvot'],how='left')
print(Y,'locais',len(m),'unmatched',m.long.isna().sum(),'(%.2f%% of votes)'%(100*m[m.long.isna()].total.sum()/m.total.sum()),'dupes',m.duplicated(key).sum())
m=m.dropna(subset=['long','lat']); m['municipio']=m.cod_localidade_ibge.map(RMSP)
m['lon_r']=m.long.round(5); m['lat_r']=m.lat.round(5)
agg=m.groupby(['cod_localidade_ibge','municipio','lon_r','lat_r'],as_index=False).agg(
  NR_ZONA=('NR_ZONA',lambda x:'/'.join(sorted(set(map(str,x))))),NR_LOCAL_VOTACAO=('NR_LOCAL_VOTACAO',lambda x:'/'.join(sorted(set(map(str,x))))),
  NM_LOCAL_VOTACAO=('NM_LOCAL_VOTACAO',lambda x:' | '.join(sorted(set(map(str,x))))),DS_LOCAL_VOTACAO_ENDERECO=('DS_LOCAL_VOTACAO_ENDERECO','first'),ds_bairro=('ds_bairro','first'),
  va=('va','sum'),vb=('vb','sum'),branco=('branco','sum'),nulo=('nulo','sum'),validos=('validos','sum'),total=('total','sum'),n_secoes=('n_secoes','sum'),n_locais=('va','size'))
agg=agg[agg.validos>0].rename(columns={'lon_r':'long','lat_r':'lat'})
agg['pct']=100*agg.va/agg.validos
agg['nrA'],agg['nmA'],agg['sgA'],agg['nrB'],agg['nmB'],agg['sgB']=nrA,names[nrA],PARTY[nrA],nrB,names[nrB],PARTY[nrB]
print('co-located merged ->',len(agg)); print(agg[['va','vb','branco','nulo']].sum().to_dict())
mun=gpd.read_file('geojs-35-mun.json'); mun['id']=mun.id.astype(int); mun=mun[mun.id.isin(RMSP)].set_crs(4326)
crs=31983; pts=gpd.GeoDataFrame(agg,geometry=gpd.points_from_xy(agg.long,agg.lat),crs=4326).to_crs(crs); mun_p=mun.to_crs(crs)
mun_geom=dict(zip(mun_p.id,mun_p.geometry)); cells=[]
for mid,grp in pts.groupby('cod_localidade_ibge'):
    poly=mun_geom[int(mid)]; vd=voronoi_diagram(unary_union(grp.geometry.values),envelope=poly.buffer(5000))
    idx=gpd.GeoDataFrame(geometry=list(vd.geoms),crs=crs); j=gpd.sjoin(idx,grp[['geometry']],predicate='contains',how='inner')
    j['geometry']=j.geometry.intersection(poly); j=j[~j.geometry.is_empty]; cells.append(j.set_index('index_right'))
cells=pd.concat(cells); vor=gpd.GeoDataFrame(pts.drop(columns='geometry').join(cells[['geometry']],how='inner'),geometry='geometry',crs=crs)
print('cells',len(vor),'pts',len(pts))
vor.to_file(f'rmsp_voronoi_{Y}.gpkg',driver='GPKG'); pts.to_file(f'rmsp_pontos_{Y}.gpkg',driver='GPKG')
mun.to_file('rmsp_municipios.gpkg',driver='GPKG')
# published deliverables, 2022-style: vote columns named after the candidates
SHORT={13:{2006:'lula',2010:'dilma',2014:'dilma',2018:'haddad'}[Y],45:{2006:'alckmin',2010:'serra',2014:'aecio'}.get(Y),17:'bolsonaro'}
a,b=SHORT[nrA],SHORT[nrB]; out=f'rmsp_presidente_{Y}_2T_locais'
cols=['n_locais','municipio','NR_ZONA','NR_LOCAL_VOTACAO','NM_LOCAL_VOTACAO','DS_LOCAL_VOTACAO_ENDERECO','ds_bairro',a,b,'branco','nulo','validos','total',f'{a}_pct','n_secoes']
ren={'va':a,'vb':b,'pct':f'{a}_pct'}
vor.rename(columns=ren)[cols+['geometry']].to_file(out+'.gpkg',layer='locais_voronoi',driver='GPKG')
pts.rename(columns=ren)[cols+['geometry']].to_file(out+'.gpkg',layer='locais_pontos',driver='GPKG',mode='a')
mun.to_file(out+'.gpkg',layer='municipios',driver='GPKG',mode='a')
agg.rename(columns=ren)[['municipio','cod_localidade_ibge']+cols[2:]+['long','lat']].to_csv(out+'.csv',index=False)
