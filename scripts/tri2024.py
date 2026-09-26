import pandas as pd, numpy as np, geopandas as gpd, json
exec(open('agg.py').read().split('geo = pd.read_csv')[0])
v=pd.read_csv('prefeito_1t_rmsp_2024.csv.gz',sep=';',encoding='latin1'); v=v[~v.NR_VOTAVEL.isin([95,96])]
key=['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']
# municipality top-3
mt=v.groupby(['CD_MUNICIPIO','NR_VOTAVEL','NM_VOTAVEL']).QT_VOTOS.sum().reset_index()
mt['share']=mt.QT_VOTOS/mt.groupby('CD_MUNICIPIO').QT_VOTOS.transform('sum')
mt=mt.sort_values(['CD_MUNICIPIO','QT_VOTOS'],ascending=[True,False]); mt['rank']=mt.groupby('CD_MUNICIPIO').cumcount()+1
top=mt[mt['rank']<=3]
mode=top[top['rank']<=2].groupby('CD_MUNICIPIO').share.sum().rename('top2'); mode=(mode<0.85).rename('triway').reset_index()
info=top.pivot(index='CD_MUNICIPIO',columns='rank',values=['NR_VOTAVEL','NM_VOTAVEL','share'])
info.columns=[f'{a}{b}' for a,b in info.columns]; info=info.reset_index().merge(mode,on='CD_MUNICIPIO')
print(info[['CD_MUNICIPIO','NM_VOTAVEL1','share1','NM_VOTAVEL2','share2','NM_VOTAVEL3','share3','triway']].round(3).to_string())
# per-locale votes for top3
lv=v.merge(top[['CD_MUNICIPIO','NR_VOTAVEL','rank']],on=['CD_MUNICIPIO','NR_VOTAVEL'],how='inner')
piv=lv.pivot_table(index=key,columns='rank',values='QT_VOTOS',aggfunc='sum',fill_value=0).reset_index(); piv.columns=key+[f'v{c}' for c in piv.columns[3:]]
if 'v3' not in piv: piv['v3']=0
piv=piv.merge(info[['CD_MUNICIPIO','triway','NR_VOTAVEL1','NM_VOTAVEL1','NR_VOTAVEL2','NM_VOTAVEL2','NR_VOTAVEL3','NM_VOTAVEL3']],on='CD_MUNICIPIO')
# OKLab helpers
def srgb_to_lin(c): c=np.asarray(c)/255; return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def lin_to_srgb(c): c=np.clip(c,0,1); return np.where(c<=0.0031308,12.92*c,1.055*c**(1/2.4)-0.055)
def rgb_to_oklab(rgb):
    r,g,b=srgb_to_lin(rgb).T
    l=0.4122214708*r+0.5363325363*g+0.0514459929*b; m=0.2119034982*r+0.6806995451*g+0.1073969566*b; s=0.0883024619*r+0.2817188376*g+0.6299787005*b
    l,m,s=np.cbrt(l),np.cbrt(m),np.cbrt(s)
    return np.c_[0.2104542553*l+0.7936177850*m-0.0040720468*s,1.9779984951*l-2.4285922050*m+0.4505937099*s,0.0259040371*l+0.7827717662*m-0.8086757660*s]
def oklab_to_rgb(lab):
    L,a,b=lab.T
    l=L+0.3963377774*a+0.2158037573*b; m=L-0.1055613458*a-0.0638541728*b; s=L-0.0894841775*a-1.2914855480*b
    l,m,s=l**3,m**3,s**3
    r=4.0767416621*l-3.3077115913*m+0.2309699292*s; g=-1.2684380046*l+2.6097574011*m-0.3413193965*s; b=-0.0041960863*l-0.7034186147*m+1.7076147010*s
    return (lin_to_srgb(np.c_[r,g,b])*255).round().astype(int)
def hexs(rgb): return ['#%02x%02x%02x'%tuple(c) for c in rgb]
# endpoints: equal OKLab lightness/chroma, hues red/green/blue
def okc(L,C,h): h=np.radians(h); return np.array([L,C*np.cos(h),C*np.sin(h)])
E=np.stack([okc(0.60,0.14,55),okc(0.60,0.14,295),okc(0.60,0.14,175)])  # 1º orange, 2º purple, 3º teal
print('endpoints',hexs(oklab_to_rgb(E)))
tot=piv[['v1','v2','v3']].sum(axis=1).replace(0,np.nan)
w=piv[['v1','v2','v3']].div(tot,axis=0).fillna(1/3).values
# two-way: blend red/blue only with diverging (25..75 clamp) mapping; three-way: full barycentric with gray center (mean of endpoints)
lab=np.zeros((len(piv),3))
tri=piv.triway.values
w2=w[:,:2]/np.maximum(w[:,:2].sum(1,keepdims=True),1e-9)
# two-way: t in [0,1] = share1 among top2, stretched so 25%..75% spans full ramp
t=np.clip((w2[:,0]-0.25)/0.5,0,1)
gray=E.mean(0)

def tri_color(w):
    # w: (n,3) shares of 1st/2nd/3rd. hue = direction of OKLab mix (centered), chroma = leader dominance (saturates at 60%)
    d=(w.max(1)-1/3)/(0.6-1/3); d=np.clip(d,0,1)
    vec=(w-1/3)@E[:,1:]  # a,b direction
    ang=np.arctan2(vec[:,1],vec[:,0]); C=0.14*np.sqrt(d)
    return np.c_[np.full(len(w),0.55), C*np.cos(ang), C*np.sin(ang)]
lab[~tri]= (np.where(t[~tri,None]>=0.5, E[0]*(2*(t[~tri,None]-0.5))+gray*(1-2*(t[~tri,None]-0.5)), E[2]*(1-2*t[~tri,None])+gray*(2*t[~tri,None])))
# three-way: sharpen weights so a plurality shows: exponent 1.6, then barycentric in OKLab
lab[tri]=tri_color(w[tri])
piv['color']=hexs(oklab_to_rgb(lab))
piv['s1'],piv['s2'],piv['s3']=(100*w).T.round(1)
piv.to_csv('tri_2024_locais.csv',index=False)
info.to_csv('tri_2024_munis.csv',index=False)
print(piv.color.head(), tri.sum(), len(piv))

# aggregate to the co-located-point level used by the Voronoi/points layers
loc=pd.read_csv('rmsp_locais_2024_1t.csv').dropna(subset=['long','lat'])
loc['lon_r']=loc.long.round(5); loc['lat_r']=loc.lat.round(5)
j=loc[['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO','cod_localidade_ibge','lon_r','lat_r']].merge(piv[key+['v1','v2','v3']],on=key,how='left').fillna({'v1':0,'v2':0,'v3':0})
agg=j.groupby(['cod_localidade_ibge','lon_r','lat_r'],as_index=False)[['v1','v2','v3']].sum().merge(j[['cod_localidade_ibge','CD_MUNICIPIO']].drop_duplicates(),on='cod_localidade_ibge').merge(info,on='CD_MUNICIPIO')
tot=agg[['v1','v2','v3']].sum(axis=1).replace(0,np.nan); w=agg[['v1','v2','v3']].div(tot,axis=0).fillna(1/3).values; tri=agg.triway.values
lab=np.zeros((len(agg),3)); w2=w[:,:2]/np.maximum(w[:,:2].sum(1,keepdims=True),1e-9); t=np.clip((w2[:,0]-0.25)/0.5,0,1)
tt=t[~tri,None]; lab[~tri]=np.where(tt>=0.5,E[0]*(2*(tt-0.5))+gray*(1-2*(tt-0.5)),E[2]*(1-2*tt)+gray*(2*tt))
lab[tri]=tri_color(w[tri])
agg['color']=hexs(oklab_to_rgb(lab)); agg['s1'],agg['s2'],agg['s3']=(100*w).T.round(1)
agg.rename(columns={'lon_r':'long','lat_r':'lat'}).to_csv('tri_agg_2024.csv',index=False)
print('agg',len(agg))
