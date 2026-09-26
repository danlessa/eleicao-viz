import pandas as pd, unicodedata
RMSP = {3503901:'Arujá',3505708:'Barueri',3506607:'Biritiba Mirim',3509007:'Caieiras',3509205:'Cajamar',3510609:'Carapicuíba',3513009:'Cotia',3513801:'Diadema',3515004:'Embu das Artes',3515103:'Embu-Guaçu',3515707:'Ferraz de Vasconcelos',3516309:'Francisco Morato',3516408:'Franco da Rocha',3518305:'Guararema',3518800:'Guarulhos',3522208:'Itapecerica da Serra',3522505:'Itapevi',3523107:'Itaquaquecetuba',3525003:'Jandira',3526209:'Juquitiba',3528502:'Mairiporã',3529401:'Mauá',3530607:'Mogi das Cruzes',3534401:'Osasco',3539103:'Pirapora do Bom Jesus',3539806:'Poá',3543303:'Ribeirão Pires',3544103:'Rio Grande da Serra',3545001:'Salesópolis',3546801:'Santa Isabel',3547304:'Santana de Parnaíba',3547809:'Santo André',3548708:'São Bernardo do Campo',3548807:'São Caetano do Sul',3549953:'São Lourenço da Serra',3550308:'São Paulo',3552502:'Suzano',3552809:'Taboão da Serra',3556453:'Vargem Grande Paulista'}
geo = pd.read_csv('geo_sp_2022.csv')
geo = geo[geo.cod_localidade_ibge.isin(RMSP)].copy()
print('geo RMSP stations', len(geo), 'munis', geo.cod_localidade_ibge.nunique())
v = pd.read_csv('pres2t_sp.csv', sep=';', encoding='latin1', usecols=['CD_MUNICIPIO','NM_MUNICIPIO','NR_ZONA','NR_SECAO','NR_VOTAVEL','QT_VOTOS','NR_LOCAL_VOTACAO','NM_LOCAL_VOTACAO','DS_LOCAL_VOTACAO_ENDERECO'])
tse_codes = set(geo.cd_localidade_tse)
v = v[v.CD_MUNICIPIO.isin(tse_codes)]
print('vote rows RMSP', len(v), 'munis', v.CD_MUNICIPIO.nunique())
piv = v.pivot_table(index=['CD_MUNICIPIO','NM_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO','NM_LOCAL_VOTACAO','DS_LOCAL_VOTACAO_ENDERECO'], columns='NR_VOTAVEL', values='QT_VOTOS', aggfunc='sum', fill_value=0).reset_index()
piv.columns = [str(c) for c in piv.columns]
piv = piv.rename(columns={'13':'lula','22':'bolsonaro','95':'branco','96':'nulo'})
piv['validos'] = piv.lula + piv.bolsonaro
piv['total'] = piv.validos + piv.branco + piv.nulo
piv['lula_pct'] = 100*piv.lula/piv.validos
piv['n_secoes'] = v.groupby(['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']).NR_SECAO.nunique().reindex(pd.MultiIndex.from_frame(piv[['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']])).values
print('locales', len(piv)); print(piv[['lula','bolsonaro','branco','nulo']].sum())
g = geo[['cd_localidade_tse','cod_localidade_ibge','nr_zona','nr_locvot','long','lat','tse_long','tse_lat','pred_long','pred_lat','ds_bairro']].copy()
g['nr_zona']=g.nr_zona.astype(int)
m = piv.merge(g, left_on=['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO'], right_on=['cd_localidade_tse','nr_zona','nr_locvot'], how='left')
print('unmatched', m.long.isna().sum(), 'dupes', m.duplicated(['CD_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO']).sum())
print(m[m.long.isna()][['NM_MUNICIPIO','NR_ZONA','NR_LOCAL_VOTACAO','NM_LOCAL_VOTACAO','validos']].head(20))
m['municipio'] = m.cod_localidade_ibge.map(RMSP)
m.to_csv('rmsp_locais_2t.csv', index=False)
print(m.describe()[['lula_pct','validos','long','lat']])
