"""
Modo auto: lee los títulos en voz alta, uno tras otro, con la voz del navegador (gratis, no usa la IA).

Arma una página con JavaScript (speechSynthesis) que se muestra dentro de la app:
- pasa sola a la nota siguiente; anterior, pausa, siguiente y próximo medio;
- en orden "medio por medio" anuncia cada medio ("Ahora, Clarín");
- puede leer también la bajada; velocidad y elección de voz (prefiere voces argentinas);
- recuerda las notas ya escuchadas y dónde quedaste (en el navegador), para seguir después;
- teclado: espacio pausa, ← → nota, ↑ ↓ medio.

No depende de Streamlit: devuelve el HTML y la app lo muestra.
"""
import html
import json

NOMBRES_IDIOMA = {"en": "inglés", "fr": "francés", "it": "italiano", "de": "alemán", "pt": "portugués"}


def _js(dato):
    return json.dumps(dato, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def ordenar(notas, orden, por_medio):
    """notas: lista de dicts (medio, titulo, puesto…). orden: "intercalado" o "medio"."""
    por = {}
    for n in notas:
        por.setdefault(n.get("medio", ""), []).append(n)
    for m in por:
        por[m] = sorted(por[m], key=lambda n: n.get("puesto", 0))[:por_medio]
    if orden == "medio":
        return [n for m in por for n in por[m]]
    out, k = [], 0
    while any(k < len(v) for v in por.values()):
        out += [v[k] for v in por.values() if k < len(v)]
        k += 1
    return out


def html_reproductor(notas, clave, orden="intercalado", titulo=""):
    datos = [{"m": n.get("medio", ""), "c": n.get("color", "#888"),
              "t": n.get("titulo_es") or n["titulo"],
              "l": "es" if (n.get("titulo_es") or n.get("lang", "es") == "es") else n.get("lang", "es"),
              "tr": NOMBRES_IDIOMA.get(n.get("lang"), "") if n.get("titulo_es") else "",
              "b": (n.get("bajada") or "")[:300], "u": n.get("url") or ""} for n in notas]
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{--bg:#fff;--fg:#1f2328;--mu:#6b7280;--bd:#d0d7de;--ac:#e34535;--card:#f6f7f9}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0e1117;--fg:#fafafa;--mu:#9aa3ad;--bd:#3b3f47;--card:#1a1d24}}}}
*{{box-sizing:border-box}} body{{margin:0;font-family:"Source Sans Pro",system-ui,sans-serif;background:var(--bg);color:var(--fg)}}
.w{{border:1px solid var(--bd);border-radius:14px;padding:16px;background:var(--card)}}
.top{{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:.85rem;color:var(--mu)}}
.medio{{display:flex;align-items:center;gap:8px;font-weight:700;font-size:1rem;margin-top:10px}}
.dot{{width:12px;height:12px;border-radius:50%;flex:none}}
.tit{{font-size:1.45rem;line-height:1.25;font-weight:700;margin:8px 0 6px;min-height:3.6rem}}
.baj{{color:var(--mu);font-size:.95rem;min-height:1.2rem}}
.tr{{font-size:.78rem;color:var(--mu)}}
.bar{{height:5px;background:var(--bd);border-radius:3px;margin:12px 0;overflow:hidden}} .bar i{{display:block;height:100%;background:var(--ac);width:0}}
.ctr{{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}}
button{{font:inherit;border:1px solid var(--bd);background:var(--bg);color:var(--fg);border-radius:12px;padding:10px 14px;font-size:1.05rem;cursor:pointer;min-width:58px}}
button:hover{{border-color:var(--ac)}} .play{{background:var(--ac);border-color:var(--ac);color:#fff;font-weight:700;min-width:120px}}
.opt{{display:flex;gap:12px;flex-wrap:wrap;align-items:center;justify-content:center;margin-top:12px;font-size:.85rem;color:var(--mu)}}
select{{font:inherit;font-size:.85rem;background:var(--bg);color:var(--fg);border:1px solid var(--bd);border-radius:8px;padding:3px}}
a{{color:var(--ac)}}
</style></head><body>
<div class="w" id="w">
 <div class="top"><span id="cont"></span><span id="aviso"></span></div>
 <div class="medio"><span class="dot" id="dot"></span><span id="med"></span></div>
 <div class="tit" id="tit">Tocá ▶ para empezar</div>
 <div class="tr" id="tr"></div>
 <div class="baj" id="baj"></div>
 <div class="bar"><i id="prog"></i></div>
 <div class="ctr">
  <button id="ant" title="Anterior (←)">⏮</button>
  <button id="play" class="play" title="Reproducir / pausa (espacio)">▶ Escuchar</button>
  <button id="sig" title="Siguiente (→)">⏭</button>
  <button id="pmed" title="Próximo medio (↓)">⏩ Medio</button>
  <button id="abrir" title="Abrir la nota en el medio">🔗</button>
 </div>
 <div class="opt">
  <label><input type="checkbox" id="cb"> Leer también la bajada</label>
  <label><input type="checkbox" id="sk" checked> Saltear las ya escuchadas</label>
  <label>Velocidad <select id="vel"><option>0.9</option><option selected>1</option><option>1.1</option><option>1.25</option><option>1.4</option><option>1.6</option></select></label>
  <label>Voz <select id="voz"></select></label>
 </div>
</div>
<script>
const N={_js(datos)}, CLAVE={_js(clave)}, ORDEN={_js(orden)};
const S=window.speechSynthesis; let i=0, on=false, gen=0, lock=null;
const $=id=>document.getElementById(id);
function ls(k,v){{try{{if(v===undefined)return JSON.parse(localStorage.getItem(k)||'null');localStorage.setItem(k,JSON.stringify(v));}}catch(e){{return null;}}}}
let oidas=new Set(ls('mg_escuchadas')||[]);
function marcar(u){{if(!u)return;oidas.add(u);const a=[...oidas].slice(-3000);ls('mg_escuchadas',a);}}
function voces(){{return S.getVoices();}}
function llenarVoces(){{const vs=voces().filter(v=>/^es/i.test(v.lang));const sel=$('voz');const prev=ls('mg_voz');
 const rank=v=>(/es-AR/i.test(v.lang)?0:/es-(419|US|MX|CL|CO|UY)/i.test(v.lang)?1:2)*10+(/natural|online|neural/i.test(v.name)?0:5);
 vs.sort((a,b)=>rank(a)-rank(b));sel.innerHTML=vs.map(v=>`<option value="${{v.name}}">${{v.name.replace(/Microsoft |Google /,'')}} (${{v.lang}})</option>`).join('');
 if(prev&&vs.some(v=>v.name===prev))sel.value=prev;}}
llenarVoces(); if(S.onvoiceschanged!==undefined)S.onvoiceschanged=llenarVoces;
$('voz').onchange=()=>ls('mg_voz',$('voz').value);
function vozPara(l){{const vs=voces();if(l==='es')return vs.find(v=>v.name===$('voz').value)||vs.find(v=>/^es/i.test(v.lang));
 return vs.find(v=>v.lang.toLowerCase().startsWith(l)&&/natural|online/i.test(v.name))||vs.find(v=>v.lang.toLowerCase().startsWith(l));}}
function mostrar(){{const n=N[i];if(!n)return;$('cont').textContent=`${{i+1}} de ${{N.length}}`;$('med').textContent=n.m;$('dot').style.background=n.c;
 $('tit').textContent=n.t;$('baj').textContent=$('cb').checked?n.b:'';$('tr').textContent=n.tr?`🌐 traducido del ${{n.tr}}`:'';
 $('prog').style.width=((i+1)/N.length*100)+'%';$('abrir').disabled=!n.u;ls('mg_pos_'+CLAVE,n.u||i);}}
function frase(k){{const n=N[k];let s='';const nuevo=k===0||N[k-1].m!==n.m;
 s+=(ORDEN==='medio'&&nuevo)?`Ahora, ${{n.m}}. `:`${{n.m}}. `;s+=n.t.replace(/[“”"«»]/g,'');if($('cb').checked&&n.b)s+='. '+n.b;return s;}}
function siguienteValido(k,paso){{let j=k;while(j>=0&&j<N.length&&$('sk').checked&&oidas.has(N[j].u)&&N[j].u)j+=paso;return j;}}
async function despierto(){{try{{if(on&&!lock&&navigator.wakeLock)lock=await navigator.wakeLock.request('screen');}}catch(e){{}}}}
function hablar(){{S.cancel();const g=++gen;const n=N[i];mostrar();despierto();
 const u=new SpeechSynthesisUtterance(frase(i));const v=vozPara(n.l);if(v){{u.voice=v;u.lang=v.lang;}}else u.lang=n.l==='es'?'es-AR':n.l;
 u.rate=parseFloat($('vel').value);
 u.onend=()=>{{if(g!==gen||!on)return;marcar(n.u);const j=siguienteValido(i+1,1);
  if(j<N.length){{setTimeout(()=>{{if(g===gen&&on){{i=j;hablar();}}}},650);}}else fin();}};
 u.onerror=e=>{{if(g===gen&&on&&e.error!=='interrupted'&&e.error!=='canceled'){{$('aviso').textContent='La voz se cortó: tocá ▶';parar();}}}};
 S.speak(u);}}
function fin(){{parar();$('tit').textContent='✔ Terminaste esta lista';$('baj').textContent='';$('med').textContent='';$('aviso').textContent='';}}
function parar(){{on=false;gen++;S.cancel();$('play').textContent='▶ Escuchar';try{{lock&&lock.release();}}catch(e){{}}lock=null;}}
function empezar(){{on=true;$('play').textContent='⏸ Pausa';$('aviso').textContent='';if(siguienteValido(i,1)<N.length)i=siguienteValido(i,1);hablar();}}
function ir(k){{i=Math.max(0,Math.min(N.length-1,k));if(on)hablar();else mostrar();}}
$('play').onclick=()=>on?parar():empezar();
$('sig').onclick=()=>ir(siguienteValido(i+1,1)<N.length?siguienteValido(i+1,1):i+1);
$('ant').onclick=()=>ir(i-1);
function proxMedio(){{let j=i+1;while(j<N.length&&N[j].m===N[i].m)j++;if(ORDEN!=='medio'){{const m=N[i].m;j=i+1;while(j<N.length&&N[j].m===m)j++;}}ir(j<N.length?j:i);}}
function medioAnterior(){{let j=i-1;const m=N[i].m;while(j>0&&N[j].m===m)j--;const m2=N[j]?N[j].m:'';while(j>0&&N[j-1].m===m2)j--;ir(Math.max(0,j));}}
$('pmed').onclick=proxMedio;
$('abrir').onclick=()=>{{const u=N[i]&&N[i].u;if(u)window.open(u,'_blank','noopener');}};
$('cb').onchange=()=>{{ls('mg_bajada',$('cb').checked);mostrar();}}; $('cb').checked=!!ls('mg_bajada');
$('vel').onchange=()=>ls('mg_vel',$('vel').value); if(ls('mg_vel'))$('vel').value=ls('mg_vel');
document.addEventListener('keydown',e=>{{if(e.target.tagName==='SELECT')return;
 if(e.code==='Space'){{e.preventDefault();$('play').click();}} else if(e.key==='ArrowRight')$('sig').click();
 else if(e.key==='ArrowLeft')$('ant').click(); else if(e.key==='ArrowDown'){{e.preventDefault();proxMedio();}}
 else if(e.key==='ArrowUp'){{e.preventDefault();medioAnterior();}}}});
let x0=null;$('w').addEventListener('touchstart',e=>x0=e.touches[0].clientX,{{passive:true}});
$('w').addEventListener('touchend',e=>{{if(x0===null)return;const dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>60)(dx<0?$('sig'):$('ant')).click();x0=null;}});
// seguir donde quedaste
const pos=ls('mg_pos_'+CLAVE); if(pos!==null){{const k=typeof pos==='number'?pos:N.findIndex(n=>n.u===pos);if(k>0&&k<N.length){{i=k;$('aviso').textContent='▶ sigue donde quedaste';}}}}
if(!N.length){{$('tit').textContent='No hay notas para escuchar';}} else mostrar();
if(!('speechSynthesis' in window)){{$('tit').textContent='Este navegador no puede leer en voz alta';}}
</script></body></html>"""
