"""
Modo auto: lee las noticias en voz alta, una tras otra, con la voz del navegador (gratis, no usa la IA).

Qué lee de cada nota (modo):
  "titulos"   el medio y el título
  "bajadas"   el título y la bajada
  "completa"  el título y después la nota entera, párrafo por párrafo (con ⏪ / ⏩ para saltar párrafos)

- pasa sola a la nota siguiente; anterior, pausa, siguiente y próximo medio;
- en orden "medio por medio" anuncia cada medio ("Ahora, Clarín");
- velocidad y elección de voz (prefiere voces argentinas);
- recuerda las notas ya escuchadas y dónde quedaste (en el navegador);
- teclado: espacio pausa, ← → nota, ↑ ↓ medio, [ ] párrafo.

No depende de Streamlit: devuelve el HTML y la app lo muestra.
"""
import json

NOMBRES_IDIOMA = {"en": "inglés", "fr": "francés", "it": "italiano", "de": "alemán", "pt": "portugués"}
MAX_PARRAFOS = 40


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


def html_reproductor(notas, clave, orden="intercalado", modo="titulos", textos=None):
    """textos: {url: [párrafos]} para el modo "completa" (las notas que no se pudieron leer van sin texto)."""
    textos = textos or {}
    datos = []
    for n in notas:
        traducido = bool(n.get("titulo_es"))
        lang_nota = n.get("lang", "es")
        datos.append({
            "m": n.get("medio", ""), "c": n.get("color", "#888"),
            "t": n.get("titulo_es") or n["titulo"],
            "l": "es" if (traducido or lang_nota == "es") else lang_nota,
            "lp": lang_nota,                                   # el idioma del texto completo (no se traduce)
            "tr": NOMBRES_IDIOMA.get(lang_nota, "") if traducido else "",
            "b": (n.get("bajada") or "")[:400], "u": n.get("url") or "",
            "p": [p for p in textos.get(n.get("url") or "", []) if p.strip()][:MAX_PARRAFOS],
        })
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{--bg:#fff;--fg:#1f2328;--mu:#6b7280;--bd:#d0d7de;--ac:#e34535;--card:#f6f7f9}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0e1117;--fg:#fafafa;--mu:#9aa3ad;--bd:#3b3f47;--card:#1a1d24}}}}
*{{box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
html,body{{margin:0;background:var(--bg);color:var(--fg);font-family:"Source Sans Pro",system-ui,sans-serif}}
.w{{border:1px solid var(--bd);border-radius:16px;padding:16px;background:var(--card);touch-action:pan-y}}
.top{{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:.9rem;color:var(--mu)}}
.medio{{display:flex;align-items:center;gap:8px;font-weight:700;font-size:1.05rem;margin-top:8px}}
.dot{{width:12px;height:12px;border-radius:50%;flex:none}}
.tit{{font-size:clamp(1.2rem,4.8vw,1.5rem);line-height:1.25;font-weight:700;margin:8px 0 6px}}
.baj{{color:var(--mu);font-size:1rem;line-height:1.35}}
.tr{{font-size:.8rem;color:var(--mu)}}
.par{{margin-top:10px;padding:10px 12px;border-left:3px solid var(--ac);background:var(--bg);border-radius:8px;font-size:1.05rem;line-height:1.45;max-height:9em;overflow:auto;display:none}}
.pinfo{{font-size:.85rem;color:var(--mu);margin-top:6px;display:none}}
.bar{{height:6px;background:var(--bd);border-radius:3px;margin:14px 0;overflow:hidden}} .bar i{{display:block;height:100%;background:var(--ac);width:0}}
/* Controles grandes para usar con el pulgar */
.fila{{display:grid;gap:10px;margin-top:10px}}
.f1{{grid-template-columns:1fr 1.6fr 1fr}} .f2,.f3{{grid-template-columns:1fr 1fr}}
button{{font:inherit;font-size:1.05rem;min-height:56px;padding:8px 10px;border:1px solid var(--bd);background:var(--bg);color:var(--fg);
 border-radius:14px;cursor:pointer;touch-action:manipulation;user-select:none;display:flex;align-items:center;justify-content:center;gap:6px}}
button:active{{transform:scale(.97)}} button:disabled{{opacity:.35}}
@media (hover:hover){{button:hover{{border-color:var(--ac)}}}}
.play{{background:var(--ac);border-color:var(--ac);color:#fff;font-weight:700;font-size:1.25rem;min-height:64px}}
.ic{{font-size:1.3rem}}
details{{margin-top:12px;font-size:.95rem;color:var(--mu)}} summary{{cursor:pointer;padding:6px 0}}
.opt{{display:grid;gap:10px;margin-top:8px}}
.opt label{{display:flex;align-items:center;justify-content:space-between;gap:10px}}
select{{font:inherit;font-size:1rem;background:var(--bg);color:var(--fg);border:1px solid var(--bd);border-radius:10px;padding:8px;max-width:70%}}
input[type=checkbox]{{width:22px;height:22px}}
@media (max-width:420px){{.w{{padding:12px}} .lbl{{display:none}}}}
</style></head><body>
<div class="w" id="w">
 <div class="top"><span id="cont"></span><span id="aviso"></span></div>
 <div class="medio"><span class="dot" id="dot"></span><span id="med"></span></div>
 <div class="tit" id="tit">Tocá ▶ para empezar</div>
 <div class="tr" id="tr"></div>
 <div class="baj" id="baj"></div>
 <div class="par" id="par"></div>
 <div class="pinfo" id="pinfo"></div>
 <div class="bar"><i id="prog"></i></div>
 <div class="fila f1">
  <button id="ant" title="Nota anterior (←)"><span class="ic">⏮</span><span class="lbl">Anterior</span></button>
  <button id="play" class="play" title="Reproducir / pausa (espacio)">▶ Escuchar</button>
  <button id="sig" title="Nota siguiente (→)"><span class="lbl">Siguiente</span><span class="ic">⏭</span></button>
 </div>
 <div class="fila f2" id="filaPar">
  <button id="pant" title="Párrafo anterior ([)"><span class="ic">⏪</span> Párrafo</button>
  <button id="psig" title="Párrafo siguiente (])">Párrafo <span class="ic">⏩</span></button>
 </div>
 <div class="fila f3">
  <button id="pmed" title="Próximo medio (↓)">Próximo medio</button>
  <button id="abrir" title="Abrir la nota en el medio">🔗 Abrir nota</button>
 </div>
 <details>
  <summary>⚙️ Voz, velocidad y opciones</summary>
  <div class="opt">
   <label>Saltear las ya escuchadas <input type="checkbox" id="sk" checked></label>
   <label>Velocidad <select id="vel"><option>0.9</option><option selected>1</option><option>1.1</option><option>1.25</option><option>1.4</option><option>1.6</option></select></label>
   <label>Voz <select id="voz"></select></label>
  </div>
 </details>
</div>
<script>
const N={_js(datos)}, CLAVE={_js(clave)}, ORDEN={_js(orden)}, MODO={_js(modo)};
const COMPLETA = MODO==='completa';
const S=window.speechSynthesis; let i=0, j=-1, on=false, gen=0, lock=null;   // j = -1: título; j >= 0: párrafo
const $=id=>document.getElementById(id);
function ls(k,v){{try{{if(v===undefined)return JSON.parse(localStorage.getItem(k)||'null');localStorage.setItem(k,JSON.stringify(v));}}catch(e){{return null;}}}}
let oidas=new Set(ls('mg_escuchadas')||[]);
function marcar(u){{if(!u)return;oidas.add(u);ls('mg_escuchadas',[...oidas].slice(-3000));}}
function voces(){{return S.getVoices();}}
function llenarVoces(){{const vs=voces().filter(v=>/^es/i.test(v.lang));const sel=$('voz');const prev=ls('mg_voz');
 const rank=v=>(/es-AR/i.test(v.lang)?0:/es-(419|US|MX|CL|CO|UY)/i.test(v.lang)?1:2)*10+(/natural|online|neural/i.test(v.name)?0:5);
 vs.sort((a,b)=>rank(a)-rank(b));sel.innerHTML=vs.map(v=>`<option value="${{v.name}}">${{v.name.replace(/Microsoft |Google /,'')}} (${{v.lang}})</option>`).join('');
 if(prev&&vs.some(v=>v.name===prev))sel.value=prev;}}
llenarVoces(); if(S.onvoiceschanged!==undefined)S.onvoiceschanged=llenarVoces;
$('voz').onchange=()=>ls('mg_voz',$('voz').value);
function vozPara(l){{const vs=voces();if(l==='es')return vs.find(v=>v.name===$('voz').value)||vs.find(v=>/^es/i.test(v.lang));
 return vs.find(v=>v.lang.toLowerCase().startsWith(l)&&/natural|online/i.test(v.name))||vs.find(v=>v.lang.toLowerCase().startsWith(l));}}
if(!COMPLETA){{$('filaPar').style.display='none';}}
function mostrar(){{const n=N[i];if(!n)return;$('cont').textContent=`${{i+1}} de ${{N.length}}`;$('med').textContent=n.m;$('dot').style.background=n.c;
 $('tit').textContent=n.t;$('baj').textContent=MODO==='titulos'?'':n.b;$('tr').textContent=n.tr?`🌐 título traducido del ${{n.tr}}`:'';
 if(COMPLETA){{const tiene=n.p.length>0;$('par').style.display=(j>=0&&tiene)?'block':'none';$('par').textContent=j>=0?(n.p[j]||''):'';
  $('pinfo').style.display='block';
  $('pinfo').textContent=!tiene?'Esta nota no se pudo leer completa (muro de pago o Google News): solo título y bajada.'
   :(j<0?`Título · después, ${{n.p.length}} párrafos`:`párrafo ${{j+1}} de ${{n.p.length}}`);
  $('pant').disabled=j<0;$('psig').disabled=!tiene||j>=n.p.length-1;}}
 $('prog').style.width=((i+1)/N.length*100)+'%';$('abrir').disabled=!n.u;ls('mg_pos_'+CLAVE,n.u||i);}}
function frase(){{const n=N[i];
 if(j>=0)return {{txt:n.p[j],l:n.lp}};
 const nuevo=i===0||N[i-1].m!==n.m;let s=(ORDEN==='medio'&&nuevo)?`Ahora, ${{n.m}}. `:`${{n.m}}. `;
 s+=n.t.replace(/[“”"«»]/g,'');
 if(MODO!=='titulos'&&n.b)s+='. '+n.b;          // en "completa" la bajada va antes del cuerpo
 return {{txt:s,l:n.l}};}}
function siguienteValido(k){{while(k<N.length&&$('sk').checked&&N[k].u&&oidas.has(N[k].u))k++;return k;}}
async function despierto(){{try{{if(on&&!lock&&navigator.wakeLock)lock=await navigator.wakeLock.request('screen');}}catch(e){{}}}}
function avanzar(g){{const n=N[i];
 if(COMPLETA&&j<n.p.length-1){{j++;hablar();return;}}
 marcar(n.u);const k=siguienteValido(i+1);
 if(k<N.length){{setTimeout(()=>{{if(g===gen&&on){{i=k;j=-1;hablar();}}}},COMPLETA?1100:650);}}else fin();}}
function hablar(){{S.cancel();const g=++gen;mostrar();despierto();const f=frase();
 const u=new SpeechSynthesisUtterance(f.txt);const v=vozPara(f.l);if(v){{u.voice=v;u.lang=v.lang;}}else u.lang=f.l==='es'?'es-AR':f.l;
 u.rate=parseFloat($('vel').value);
 u.onend=()=>{{if(g===gen&&on)avanzar(g);}};
 u.onerror=e=>{{if(g===gen&&on&&e.error!=='interrupted'&&e.error!=='canceled'){{$('aviso').textContent='La voz se cortó: tocá ▶';parar();}}}};
 S.speak(u);}}
function fin(){{parar();$('tit').textContent='✔ Terminaste esta lista';$('baj').textContent='';$('med').textContent='';$('aviso').textContent='';
 $('par').style.display='none';$('pinfo').style.display='none';}}
function parar(){{on=false;gen++;S.cancel();$('play').textContent='▶ Escuchar';try{{lock&&lock.release();}}catch(e){{}}lock=null;}}
function empezar(){{on=true;$('play').textContent='⏸ Pausa';$('aviso').textContent='';
 if(j<0){{const k=siguienteValido(i);if(k<N.length)i=k;}} hablar();}}
function ir(k){{i=Math.max(0,Math.min(N.length-1,k));j=-1;if(on)hablar();else mostrar();}}
function irParrafo(d){{const n=N[i];if(!COMPLETA||!n.p.length)return;j=Math.max(-1,Math.min(n.p.length-1,j+d));if(on)hablar();else mostrar();}}
$('play').onclick=()=>on?parar():empezar();
$('sig').onclick=()=>{{const k=siguienteValido(i+1);ir(k<N.length?k:i+1);}};
$('ant').onclick=()=>ir(j>0&&COMPLETA?i:i-1);
$('psig').onclick=()=>irParrafo(1); $('pant').onclick=()=>irParrafo(-1);
function proxMedio(){{const m=N[i].m;let k=i+1;while(k<N.length&&N[k].m===m)k++;ir(k<N.length?k:i);}}
function medioAnterior(){{let k=i-1;const m=N[i].m;while(k>0&&N[k].m===m)k--;const m2=N[k]?N[k].m:'';while(k>0&&N[k-1].m===m2)k--;ir(Math.max(0,k));}}
$('pmed').onclick=proxMedio;
if(new Set(N.map(n=>n.m)).size<2){{$('pmed').style.display='none';document.querySelector('.f3').style.gridTemplateColumns='1fr';}}
$('abrir').onclick=()=>{{const u=N[i]&&N[i].u;if(u)window.open(u,'_blank','noopener');}};
$('vel').onchange=()=>ls('mg_vel',$('vel').value); if(ls('mg_vel'))$('vel').value=ls('mg_vel');
document.addEventListener('keydown',e=>{{if(e.target.tagName==='SELECT')return;
 if(e.code==='Space'){{e.preventDefault();$('play').click();}} else if(e.key==='ArrowRight')$('sig').click();
 else if(e.key==='ArrowLeft')$('ant').click(); else if(e.key==='ArrowDown'){{e.preventDefault();proxMedio();}}
 else if(e.key==='ArrowUp'){{e.preventDefault();medioAnterior();}} else if(e.key===']')irParrafo(1); else if(e.key==='[')irParrafo(-1);}});
let x0=null;$('w').addEventListener('touchstart',e=>x0=e.touches[0].clientX,{{passive:true}});
$('w').addEventListener('touchend',e=>{{if(x0===null)return;const dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>60)(dx<0?$('sig'):$('ant')).click();x0=null;}});
const pos=ls('mg_pos_'+CLAVE); if(pos!==null){{const k=typeof pos==='number'?pos:N.findIndex(n=>n.u===pos);if(k>0&&k<N.length){{i=k;$('aviso').textContent='▶ sigue donde quedaste';}}}}
if(!N.length){{$('tit').textContent='No hay notas para escuchar';}} else mostrar();
if(!('speechSynthesis' in window)){{$('tit').textContent='Este navegador no puede leer en voz alta';}}
</script></body></html>"""
