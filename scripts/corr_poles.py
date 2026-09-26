import pandas as pd, numpy as np, geopandas as gpd
from scipy.spatial import cKDTree
exec(open('agg.py').read().split('geo = pd.read_csv')[0])
# 2022 reference: Lula share per (co-located) point
ref=gpd.read_file('rmsp_pontos.gpkg').to_crs(31983); ref['lp']=ref.lula_pct
rx=np.c_[ref.geometry.x,ref.geometry.y]; tree=cKDTree(rx)
def attach_lula(df_xy):
    d,i=tree.query(df_xy,distance_upper_bound=150); ok=np.isfinite(d)
    out=np.full(len(df_xy),np.nan); out[ok]=ref.lp.values[i[ok]]; return out
def corr_table(v, key, turno):
    """v: section rows (candidates only). returns per-municipality candidate correlation with Lula 2022"""
    loc=pd.read_csv('rmsp_locais_2024_1t.csv' if turno==1 else 'rmsp_locais_2024_2t.csv').dropna(subset=['long','lat'])
    loc=loc[['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO','long','lat']]
    g=v.groupby(['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO','NR_VOTAVEL','NM_VOTAVEL']).QT_VOTOS.sum().reset_index()
    tot=g.groupby(['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']).QT_VOTOS.transform('sum'); g['share']=100*g.QT_VOTOS/tot
    g=g.merge(loc,on=['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO'])
    pts=gpd.GeoSeries(gpd.points_from_xy(g.long,g.lat),crs=4326).to_crs(31983)
    g['lula22']=attach_lula(np.c_[pts.x,pts.y]); g=g.dropna(subset=['lula22'])
    rows=[]
    for (m,nr,nm),gg in g.groupby(['CD_MUNICIPIO','NR_VOTAVEL','NM_VOTAVEL']):
        if len(gg)<5: r=np.nan
        else: r=np.corrcoef(gg.share,gg.lula22)[0,1]
        rows.append(dict(CD_MUNICIPIO=m,NR_VOTAVEL=nr,NM_VOTAVEL=nm,votos=gg.QT_VOTOS.sum(),n_locais=len(gg),r_lula22=r))
    return pd.DataFrame(rows)
if __name__=='__main__':
    v=pd.read_csv('prefeito_1t_rmsp_2024.csv.gz',sep=';',encoding='latin1'); v=v[~v.NR_VOTAVEL.isin([95,96])]
    ct=corr_table(v,None,1); ct.to_csv('corr_2024_1t.csv',index=False)
    v2=pd.read_csv('prefeito_2t_rmsp_2024.csv.gz',sep=';',encoding='latin1'); v2=v2[~v2.NR_VOTAVEL.isin([95,96])]
    ct2=corr_table(v2,None,2); ct2.to_csv('corr_2024_2t.csv',index=False)
    for m in [71072,64777,70750,66893,63770]:
        print(ct[ct.CD_MUNICIPIO==m].sort_values('votos',ascending=False).head(4)[['NM_VOTAVEL','NR_VOTAVEL','votos','r_lula22']].round(2).to_string(index=False)); print()
    print(ct2[['CD_MUNICIPIO','NM_VOTAVEL','r_lula22']].round(2).to_string(index=False))
