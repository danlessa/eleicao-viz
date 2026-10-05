# 2026 1st round: download the per-section voting-machine reports (boletins de urna, .bu) for the RMSP from the live
# results site. Re-runnable: sections already in bu/ are skipped, so running it again later picks up late reports.
# usage: python scrape_bu2026.py   (cwd needs rmsp_mun.json = {TSE code: name} for the 39 municipalities; writes bu/)
import json, os, sys, time, urllib.request, urllib.error, concurrent.futures as cf
BASE = 'https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3220'
MUN = json.load(open('rmsp_mun.json'))
os.makedirs('bu', exist_ok=True)

def get(url, tries=3):
    for k in range(tries):
        try:
            return urllib.request.urlopen(url, timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code != 404 or k == tries - 1: raise
        except Exception:
            if k == tries - 1: raise
        time.sleep(1 + 2 * k)  # the mirrors are eventually consistent: a fresh file can 404 on one and not another

cs = json.loads(get(f'{BASE}/config/sp/sp-p003220-cs.json'))
when = {(mu['cd'], z['cd'], s['ns']): s['da'][6:] + s['da'][3:5] + s['da'][:2] + s['ha'] for mu in cs['abr'][0]['mu']
        for z in mu['zon'] for s in z['sec'] if 'da' in s}
json.dump(cs, open('sp-cs.json', 'w'))
todo = sorted(((mu['cd'], z['cd'], s['ns']) for mu in cs['abr'][0]['mu'] if mu['cd'] in MUN
               for z in mu['zon'] for s in z['sec'] if 'da' in s), key=lambda t: when[t])
total = sum(len(z['sec']) for mu in cs['abr'][0]['mu'] if mu['cd'] in MUN for z in mu['zon'])
todo = [t for t in todo if not os.path.exists('bu/%s_%s_%s.bu' % t)]
print(f'sections: {total} in RMSP, {len(todo)} reported and not yet downloaded', flush=True)

def fetch(t):
    m, z, s = t
    d = f'{BASE}/dados/sp/{m}/{z}/{s}/'
    try:
        aux = json.loads(get(d + f'p003220-sp-m{m}-z{z}-s{s}-aux.json', tries=1))
        h = aux['hashes'][-1]
        nm = next(a['nm'] for a in h['arq'] if a['tp'] == 'bu')
        b = get(d + h['hash'] + '/' + nm)
    except Exception as e:
        return t, repr(e)[:80]
    open('bu/%s_%s_%s.bu.tmp' % t, 'wb').write(b); os.replace('bu/%s_%s_%s.bu.tmp' % t, 'bu/%s_%s_%s.bu' % t)
    return t, None

# files are not published in receipt order, so every pass tries all missing sections (a 404 costs ~0.5 s)
err = 0
with cf.ThreadPoolExecutor(int(sys.argv[1]) if len(sys.argv) > 1 else 8) as ex:
    for i, (t, e) in enumerate(ex.map(fetch, todo), 1):
        err += bool(e)
        if i % 5000 == 0 or i == len(todo): print(f'{i}/{len(todo)} done, {err} failed', flush=True)
print('have', len(os.listdir('bu')), 'of', total)
