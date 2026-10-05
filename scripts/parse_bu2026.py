# Decode the .bu files fetched by scrape_bu2026.py into a votacao_secao-like long table.
# usage: python parse_bu2026.py   (cwd needs bu/; writes votos_secao_rmsp_2026.csv.gz)
# A .bu is BER: an envelope whose 5th field is an OCTET STRING holding the EntidadeBoletimUrna. Only the fields used
# here are decoded, by position (TSE spec "bu.asn1"): identificacaoSecao {{municipio, zona}, local, secao} and
# resultadosVotacaoPorEleicao -> {idEleicao, qtdEleitoresAptos, .., resultadosVotacao -> {tipoCargo,
# qtdComparecimento, totaisVotosCargo -> {[1] cargo, ordem, votosVotaveis -> {[1] tipoVoto, [2] qtd,
# [3] {partido, codigo}?, ..}}}}.
import os, csv, gzip

def tlv(b, i=0, end=None):
    end = len(b) if end is None else end
    out = []
    while i < end:
        t = b[i]; i += 1
        num = t & 31
        if num == 31:
            num = 0
            while True:
                x = b[i]; i += 1; num = (num << 7) | (x & 127)
                if not x & 128: break
        L = b[i]; i += 1
        if L & 128:
            n = L & 127; L = int.from_bytes(b[i:i+n], 'big'); i += n
        out.append((t >> 6, num, tlv(b, i, i+L) if t & 32 else b[i:i+L]))
        i += L
    return out

num = lambda v: int.from_bytes(v, 'big', signed=True)
seqs = lambda node: [c for c in node if c[0] == 0 and c[1] == 16]
TIPO = {1: 'nominal', 2: 'branco', 3: 'nulo', 4: 'legenda'}

def parse(b):
    env = tlv(b)[0][2]
    bu = tlv(env[4][2])[0][2]
    ids = next(c[2] for c in seqs(bu) if len(c[2]) == 3 and c[2][0][1] == 16)  # identificacaoSecao
    (mun, zona), local, secao = [num(x[2]) for x in ids[0][2]], num(ids[1][2]), num(ids[2][2])
    res = bu[8][2]  # resultadosVotacaoPorEleicao (9th field)
    for _, _, ele in res:
        id_ele, aptos = num(ele[0][2]), num(ele[1][2])
        for _, _, rv in seqs(ele)[0][2]:
            comp = num(rv[1][2])
            for _, _, tc in rv[2][2]:
                cargo = num(tc[0][2])
                for _, _, vv in tc[2][2]:
                    f = {c[1]: c[2] for c in vv if c[0] == 2}
                    tipo = num(f[1]); q = num(f[2]); part = cod = ''
                    if 3 in f: part, cod = num(f[3][0][2]), num(f[3][1][2])
                    if tipo == 2: cod = 95
                    if tipo == 3: cod = 96
                    yield dict(CD_MUNICIPIO=mun, NR_ZONA=zona, NR_SECAO=secao, NR_LOCAL_VOTACAO=local, CD_ELEICAO=id_ele,
                               QT_APTOS=aptos, QT_COMPARECIMENTO=comp, CD_CARGO=cargo, TP_VOTO=TIPO.get(tipo, tipo),
                               NR_PARTIDO=part, NR_VOTAVEL=cod, QT_VOTOS=q)

if __name__ == '__main__':
    cols = ['CD_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'NR_LOCAL_VOTACAO', 'CD_ELEICAO', 'QT_APTOS', 'QT_COMPARECIMENTO',
            'CD_CARGO', 'TP_VOTO', 'NR_PARTIDO', 'NR_VOTAVEL', 'QT_VOTOS']
    files = sorted(f for f in os.listdir('bu') if f.endswith('.bu'))
    bad = 0
    with gzip.open('votos_secao_rmsp_2026.csv.gz', 'wt', newline='') as fo:
        w = csv.DictWriter(fo, cols, delimiter=';'); w.writeheader()
        for f in files:
            try:
                rows = list(parse(open('bu/' + f, 'rb').read()))
            except Exception as e:
                bad += 1; print('bad', f, repr(e)[:80]); continue
            w.writerows(rows)
    print(len(files), 'files,', bad, 'unreadable')
