import pandas as pd, geopandas as gpd, json, numpy as np
from shapely.geometry import Point
from shapely.ops import voronoi_diagram, unary_union
m = pd.read_csv('rmsp_locais_2t.csv').drop_duplicates(['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO'])
m = m.dropna(subset=['long','lat'])
m['lon_r']=m.long.round(5); m['lat_r']=m.lat.round(5)
agg = m.groupby(['cod_localidade_ibge','municipio','lon_r','lat_r'], as_index=False).agg(
  NR_ZONA=('NR_ZONA', lambda x: '/'.join(sorted(set(map(str,x))))),
  NR_LOCAL_VOTACAO=('NR_LOCAL_VOTACAO', lambda x: '/'.join(sorted(set(map(str,x))))),
  NM_LOCAL_VOTACAO=('NM_LOCAL_VOTACAO', lambda x: ' | '.join(sorted(set(x)))),
  DS_LOCAL_VOTACAO_ENDERECO=('DS_LOCAL_VOTACAO_ENDERECO','first'), ds_bairro=('ds_bairro','first'),
  lula=('lula','sum'), bolsonaro=('bolsonaro','sum'), branco=('branco','sum'), nulo=('nulo','sum'),
  validos=('validos','sum'), total=('total','sum'), n_secoes=('n_secoes','sum'), n_locais=('lula','size'))
agg['lula_pct']=100*agg.lula/agg.validos
print('merged co-located', len(m), '->', len(agg))
m = agg.rename(columns={'lon_r':'long','lat_r':'lat'})
RMSP = set(m.cod_localidade_ibge.astype(int))
mun = gpd.read_file('geojs-35-mun.json'); mun['id']=mun.id.astype(int)
mun = mun[mun.id.isin(RMSP)].set_crs(4326)
print(len(mun))
pts = gpd.GeoDataFrame(m, geometry=gpd.points_from_xy(m.long, m.lat), crs=4326)
# projected CRS for voronoi
crs = 31983  # SIRGAS 2000 / UTM 23S
pts_p = pts.to_crs(crs); mun_p = mun.to_crs(crs)
region = unary_union(mun_p.geometry)
# points outside RMSP polygon (bad geocodes)?
inside = pts_p.within(region.buffer(200))
print('outside region', (~inside).sum()); print(pts_p[~inside][['municipio','NM_LOCAL_VOTACAO','validos']].head(15))
# For voronoi, clip each cell to its own municipality (so cells don't cross muni borders)
mun_geom = dict(zip(mun_p.id, mun_p.geometry))
cells = []
for mid, grp in pts_p.groupby('cod_localidade_ibge'):
    mid=int(mid); poly = mun_geom[mid]
    mp = unary_union(grp.geometry.values)
    vd = voronoi_diagram(mp, envelope=poly.buffer(5000))
    # map each voronoi cell to its point
    idx = gpd.GeoDataFrame(geometry=list(vd.geoms), crs=crs)
    j = gpd.sjoin(idx, grp[['geometry']], predicate='contains', how='inner')
    j['geometry'] = j.geometry.intersection(poly)
    j = j[~j.geometry.is_empty]
    cells.append(j.set_index('index_right'))
cells = pd.concat(cells)
print('cells', len(cells), 'pts', len(pts_p))
vor = pts_p.drop(columns='geometry').join(cells[['geometry']], how='inner')
vor = gpd.GeoDataFrame(vor, geometry='geometry', crs=crs)
keep = ['n_locais','municipio','NR_ZONA','NR_LOCAL_VOTACAO','NM_LOCAL_VOTACAO','DS_LOCAL_VOTACAO_ENDERECO','ds_bairro','lula','bolsonaro','branco','nulo','validos','total','lula_pct','n_secoes','geometry']
vor = vor[keep]
vor.to_file('rmsp_voronoi.gpkg', driver='GPKG')
pts[keep[:-1]+['geometry']].to_file('rmsp_pontos.gpkg', driver='GPKG')
mun.to_file('rmsp_municipios.gpkg', driver='GPKG')
print(vor.geometry.area.sum()/1e6, mun_p.area.sum()/1e6)
