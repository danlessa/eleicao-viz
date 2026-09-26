import pandas as pd, numpy as np
exec(open('agg.py').read().split('geo = pd.read_csv')[0])
exec(open('tri2024.py').read().split('# OKLab helpers')[1].split('# endpoints')[0])
LEFT={13,50,65,12,40,18,43,16,21,29,80}; RIGHT={22,30,28,10,11,44}
def okc(L,C,h): h=np.radians(h); return np.array([L,C*np.cos(h),C*np.sin(h)])
E=np.stack([okc(0.60,0.14,55),okc(0.60,0.14,175),okc(0.60,0.14,295)]); gray=E.mean(0)  # 0 orange(left) 1 teal(right) 2 purple(other)
HEX=hexs(oklab_to_rgb(E)); print(HEX)
v=pd.read_csv('prefeito_1t_rmsp_2024.csv.gz',sep=';',encoding='latin1'); v=v[~v.NR_VOTAVEL.isin([95,96])]
key=['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']
mt=v.groupby(['CD_MUNICIPIO','NR_VOTAVEL','NM_VOTAVEL']).QT_VOTOS.sum().reset_index()
mt['share']=mt.QT_VOTOS/mt.groupby('CD_MUNICIPIO').QT_VOTOS.transform('sum')
mt=mt.sort_values(['CD_MUNICIPIO','QT_VOTOS'],ascending=[True,False]); mt['rank']=mt.groupby('CD_MUNICIPIO').cumcount()+1
top=mt[mt['rank']<=3].copy()
top2=top[top['rank']<=2].groupby('CD_MUNICIPIO').share.sum()
top['triway']=top.CD_MUNICIPIO.map(top2<0.85)
top=top[(top['rank']<=2)|top.triway]  # only 2 candidates in two-way races
ct=pd.read_csv('corr_2024_1t.csv')[['CD_MUNICIPIO','NR_VOTAVEL','r_lula22']]
top=top.merge(ct,on=['CD_MUNICIPIO','NR_VOTAVEL'],how='left'); top['r_lula22']=top.r_lula22.fillna(0)
rows=[]
for m,g in top.groupby('CD_MUNICIPIO'):
    g=g.sort_values('r_lula22',ascending=False); n=len(g)
    poles=[0,2,1] if n==3 else [0,1]   # most Lula-correlated -> orange(0); most Bolsonaro-correlated -> teal(1); middle -> purple(2)
    for r,p in zip(g.itertuples(),poles): rows.append((m,r.NR_VOTAVEL,p))
pole=pd.DataFrame(rows,columns=['CD_MUNICIPIO','NR_VOTAVEL','pole']); top=top.merge(pole,on=['CD_MUNICIPIO','NR_VOTAVEL'])
info=top.pivot(index='CD_MUNICIPIO',columns='pole',values=['NR_VOTAVEL','NM_VOTAVEL','share','r_lula22']); info.columns=[f'{a}_{b}' for a,b in info.columns]
info=info.reset_index().merge(top.groupby('CD_MUNICIPIO').triway.first().reset_index(),on='CD_MUNICIPIO')
for c in ['NR_VOTAVEL','NM_VOTAVEL','share','r_lula22']:
    for p in range(3):
        if f'{c}_{p}' not in info: info[f'{c}_{p}']=np.nan
print(info[['CD_MUNICIPIO','NM_VOTAVEL_0','NM_VOTAVEL_1','NM_VOTAVEL_2','triway']].to_string())
lv=v.merge(top[['CD_MUNICIPIO','NR_VOTAVEL','pole']],on=['CD_MUNICIPIO','NR_VOTAVEL'],how='inner')
piv=lv.pivot_table(index=key,columns='pole',values='QT_VOTOS',aggfunc='sum',fill_value=0).reset_index()
piv.columns=key+[f'v{c}' for c in piv.columns[3:]]
for p in range(3):
    if f'v{p}' not in piv: piv[f'v{p}']=0
loc=pd.read_csv('rmsp_locais_2024_1t.csv').dropna(subset=['long','lat']); loc['long']=loc.long.round(5); loc['lat']=loc.lat.round(5)
j=loc[key+['cod_localidade_ibge','long','lat']].merge(piv,on=key,how='left').fillna({'v0':0,'v1':0,'v2':0})
agg=j.groupby(['cod_localidade_ibge','long','lat'],as_index=False)[['v0','v1','v2']].sum().merge(j[['cod_localidade_ibge','CD_MUNICIPIO']].drop_duplicates(),on='cod_localidade_ibge').merge(info,on='CD_MUNICIPIO')
present=np.c_[agg.NR_VOTAVEL_0.notna(),agg.NR_VOTAVEL_1.notna(),agg.NR_VOTAVEL_2.notna()]
V=agg[['v0','v1','v2']].values.astype(float)*present; tot=V.sum(1); w=np.where(tot[:,None]>0,V/np.maximum(tot[:,None],1e-9),present/present.sum(1,keepdims=True))
tri=agg.triway.values; lab=np.zeros((len(agg),3))
# three-way
d=np.clip((w.max(1)-1/3)/(0.6-1/3),0,1); vec=(w-1/3)@E[:,1:]; ang=np.arctan2(vec[:,1],vec[:,0]); C=0.14*np.sqrt(d)
lab_tri=np.c_[np.full(len(w),0.60),C*np.cos(ang),C*np.sin(ang)]
# two-way: poles i<j present; t = share of pole i; 25..75 stretched
pi=np.argmax(present,1); pj=2-np.argmax(present[:,::-1],1)
t=np.clip((w[np.arange(len(w)),pi]-0.25)/0.5,0,1)[:,None]
lab_two=np.where(t>=0.5,E[pi]*(2*(t-0.5))+gray*(1-2*(t-0.5)),E[pj]*(1-2*t)+gray*(2*t))
lab=np.where(tri[:,None],lab_tri,lab_two)
sh=agg[['share_0','share_1','share_2']].fillna(-1).values; rk=(-sh).argsort(1).argsort(1)+1
for k in range(3): agg[f'rank_{k}']=np.where(sh[:,k]>=0,rk[:,k],np.nan)
agg['color']=hexs(oklab_to_rgb(lab)); agg['s0'],agg['s1'],agg['s2']=(100*w).T.round(1)
agg.to_csv('tri_agg_2024.csv',index=False); info.to_csv('tri_2024_munis.csv',index=False); print('agg',len(agg),'tri',int(tri.sum()))
