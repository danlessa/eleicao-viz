import json
YEARS=[('2006','Presidente 2006 (2º turno)'),('2010','Presidente 2010 (2º turno)'),('2014','Presidente 2014 (2º turno)'),('2018','Presidente 2018 (2º turno)'),
       ('2022','Presidente 2022 (2º turno)'),('2024','Prefeito 2024 (1º turno)'),('2024_2T','Prefeito 2024 (2º turno)'),
       ('2026','Eleições gerais 2026 (1º turno)')]
B={y:json.load(open(f'bundle_{y}.json')) for y,_ in YEARS}
mun=B['2022'].pop('mun')
for b in B.values(): b.pop('mun',None)
t=open('tpl3.html').read()
# year toggle in title panel
t=t.replace('<h1>__TITLE__</h1>\n<p>Resultado por local de votação (__NLOC__ locais em 39 municípios). Passe o mouse / toque para ver os números.</p>',
 '<h1 id="h1"></h1>\n<p id="sub"></p>\n<div style="margin-top:6px;font-size:12px"><label style="display:inline">Eleição: <select id="year">'+''.join(f'<option value="{y}"{" selected" if y=="2026" else ""}>{lbl}</option>' for y,lbl in YEARS)+'</select></label></div>')
t=t.replace('<div id="legend" class="panel">__LEGEND__<div style="font-size:11px;color:var(--muted);margin-top:6px">__SUMMARY__</div></div>\n<div id="src" class="panel">__NOTE__</div>',
 '<div id="legend" class="panel"></div>\n<div id="src" class="panel"></div>')
t=t.replace("<title>__TITLE__ — por local de votação</title>","<title>RMSP — eleições 2006 a 2026 por local de votação</title>")
t=t.replace("const YEAR='__YEAR__', VOR=__VOR__, MUN=__MUN__, DOR=__DOR__, PROPS=__PROPS__;",
 "const DATA={__DATA__}; const MUN=__MUN__; let YEAR='2026'; let VOR=DATA[YEAR].vor, DOR=DATA[YEAR].dor, PROPS=DATA[YEAR].props;")
# make layer construction a function of year
old_vor="const vor=L.geoJSON(VOR,{style:f=>st(f.properties.color),onEachFeature:(f,l)=>hook(l,f.properties,st(f.properties.color))}).addTo(map);\nconst circles=DOR.map(([lat,lng,r],i)=>{const p=PROPS[i];const c=L.circle([lat,lng],{radius:r,...st(p.color)});c._r0=r;c._ll0=[lat,lng];c._p=p;hook(c,p,st(p.color));return c});const dor=L.layerGroup(circles);"
new_vor="""let vor,circles,dor,P0,P; const layers={};
function build(y){if(layers[y])return layers[y];const D=DATA[y];const pf=f=>D.cargos?D.props[f.properties.i]:f.properties;const v=L.geoJSON(D.vor,{style:f=>st(colorFor(pf(f))),onEachFeature:(f,l)=>hook(l,pf(f),st(colorFor(pf(f))))});
 const cs=D.dor.map(([lat,lng,r],i)=>{const p=D.props[i];const c=L.circle([lat,lng],{radius:r,...st(colorFor(p))});c._r0=r;c._ll0=[lat,lng];c._p=p;hook(c,p,st(colorFor(p)));return c});
 return layers[y]={vor:v,circles:cs,dor:L.layerGroup(cs),P0:cs.map(c=>{const q=crs.project(L.latLng(c._ll0));return [q.x,q.y]})}}
const crs=L.CRS.EPSG3857;
function setYear(y){const wasDor=document.querySelector('input[name=mode]:checked').value==='dor';if(vor){map.removeLayer(vor);map.removeLayer(dor)}YEAR=y;if(y==='2026'&&!layers[y])setCargo(cargo);const Ly=build(y);vor=Ly.vor;circles=Ly.circles;dor=Ly.dor;P0=Ly.P0;P=P0.map(a=>a.slice());
 const D=DATA[y];document.getElementById('h1').textContent=D.title;document.getElementById('sub').textContent=`Resultado por local de votação (${D.nloc} locais em ${D.nmun||39} municípios). Passe o mouse / toque para ver os números.`;
 document.getElementById('src').textContent=D.note;document.getElementById('candctl').style.display=y==='2024'?'block':'none';document.getElementById('c26ctl').style.display=y==='2026'?'block':'none';
 applyView();if(wasDor){dor.addTo(map);mun.setStyle({color:'#999',weight:0.8});if(forceOn)runForce()}else{vor.addTo(map);mun.setStyle({color:'#222',weight:1.1})};mun.bringToFront();info.style.display='none';sel=null}"""
assert old_vor in t; t=t.replace(old_vor,new_vor)
t=t.replace("const crs=L.CRS.EPSG3857; const lat0=-23.6;","const lat0=-23.6;")
t=t.replace("const P0=circles.map(c=>{const q=crs.project(L.latLng(c._ll0));return [q.x,q.y]});\nlet P=P0.map(a=>a.slice());\n","")
t=t.replace("const mun=L.geoJSON(MUN,{style:{fill:false,color:'#222',weight:1.1,opacity:0.8},interactive:false}).addTo(map);",
 "const mun=L.geoJSON(MUN,{style:{fill:false,color:'#222',weight:1.1,opacity:0.8},interactive:false}).addTo(map);\ndocument.getElementById('year').onchange=ev=>setYear(ev.target.value);")
t=t.replace("map.fitBounds(mun.getBounds());","map.fitBounds(mun.getBounds()); setYear('2026');")
# show() uses YEAR global - keep. mode switch uses vor/dor globals - fine.
t=t.replace('__LEAFLET_CSS__',open('package/dist/leaflet.css').read()).replace('__LEAFLET_JS__',open('package/dist/leaflet.js').read())
t=t.replace('__DATA__',','.join(f"'{y}':"+json.dumps(B[y],ensure_ascii=False,separators=(',',':')) for y,_ in YEARS)).replace('__MUN__',json.dumps(mun,separators=(',',':')))
open('rmsp_eleicoes_2022_2024_locais.html','w').write(t)
import os; print(os.path.getsize('rmsp_eleicoes_2022_2024_locais.html')/1e6)
