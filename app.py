"""
Monitor General · Streamlit

Las noticias de los medios de Panorama en un solo lugar, con plantillas de IA para
entender una nota, resumirla, chequearla, profundizar un tema o armar el resumen del día.
Motores de IA: los mismos del Monitor (Gemini, Mistral, Groq, OpenRouter gratis; Claude de respaldo).
"""
import hashlib
import html
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

import importlib

import fuentes
import ia_motores
import lector
import plantillas as P
import traductor


def _recargar_modulos(*mods):
    """Streamlit vuelve a ejecutar app.py en cada cambio, pero puede quedarse con la versión vieja de los
    otros archivos en memoria (pasa al subir una actualización a Streamlit Cloud). Si un archivo cambió
    desde que se cargó, se recarga. El orden importa: primero los que usan los demás."""
    for m in mods:
        try:
            cambio = os.path.getmtime(m.__file__)
        except (OSError, TypeError, AttributeError):
            continue
        if getattr(m, "_CARGADO", 0) < cambio:
            importlib.reload(m)
            m._CARGADO = time.time()


_recargar_modulos(fuentes, ia_motores, lector, traductor, P)
SECCIONES, FUENTE_POR_ID = fuentes.SECCIONES, fuentes.FUENTE_POR_ID

st.set_page_config(page_title="Monitor General", page_icon="📡", layout="wide", initial_sidebar_state="expanded")

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
SECCION_POR_ID = {s["id"]: s for s in SECCIONES}
NOMBRE_SECCION = {s["id"]: s["nombre"] for s in SECCIONES}
VISTAS = ["📰 Noticias", "🧠 Analizar nota", "🗂️ Tema", "🗞️ Resumen del día", "🕘 Historial"]
NOMBRES_IDIOMA = {"es": "español", "en": "inglés", "fr": "francés", "it": "italiano", "de": "alemán", "pt": "portugués"}

st.markdown("""
<style>
.block-container {padding-top: 3.2rem; max-width: 1200px;}
.mg-medio {display:flex; align-items:center; gap:.5rem; font-weight:700; font-size:1.05rem; margin:.2rem 0 .1rem;}
.mg-dot {width:.8rem; height:.8rem; border-radius:50%; display:inline-block; flex:none;}
.mg-meta {color: var(--mg-muted, #6b7280); font-size:.8rem;}
.mg-bajada {color: var(--mg-muted, #6b7280); font-size:.88rem; margin-top:.1rem;}
.mg-tit a {color: inherit !important; text-decoration: none; font-weight:600;}
.mg-tit a:hover {text-decoration: underline;}
.mg-chip {display:inline-block; padding:.05rem .45rem; border-radius:999px; font-size:.72rem; font-weight:600;
          background: rgba(127,127,127,.14); margin-right:.25rem;}
.mg-desc {font-size:.85rem; color: var(--mg-muted, #6b7280); margin:-.3rem 0 .6rem;}
div[data-testid="stExpander"] details summary p {font-weight:600;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════ secretos y motores ═══════════════════════
# Otros nombres con que se suelen guardar las mismas claves
_ALIAS = {
    "GEMINI_API_KEY": ["GOOGLE_API_KEY", "GOOGLE_AI_API_KEY", "GEMINI_KEY", "GEMINI"],
    "MISTRAL_API_KEY": ["MISTRAL_KEY", "MISTRAL"],
    "GROQ_API_KEY": ["GROQ_KEY", "GROQ"],
    "OPENROUTER_API_KEY": ["OPENROUTER_KEY", "OPENROUTER"],
    "ANTHROPIC_API_KEY": ["CLAUDE_API_KEY", "ANTHROPIC_KEY", "CLAUDE_KEY", "ANTHROPIC", "CLAUDE"],
}


def _leer_secrets():
    """Todos los secrets en un diccionario plano, sin importar mayúsculas ni si están dentro de una sección
    ([api_keys], [ia], etc.). Devuelve (secrets, error al leer el archivo o None)."""
    plano = {}

    def recorrer(d):
        for k, v in d.items():
            if hasattr(v, "items") and not isinstance(v, str):
                recorrer(v)
            elif isinstance(v, (str, int, float)):
                plano.setdefault(str(k).strip().upper(), str(v))
    try:
        recorrer(st.secrets)
        return plano, None
    except FileNotFoundError:
        return plano, None
    except Exception as e:
        # Solo el tipo de error y la ubicación: nunca el contenido de los secrets
        donde = re.search(r"line \d+(, column \d+)?|línea \d+", str(e))
        return plano, f"{type(e).__name__}{' en ' + donde.group(0) if donde else ''}"


_SECRETS, _ERROR_SECRETS = _leer_secrets()


def _secreto(nombre):
    for n in [nombre] + _ALIAS.get(nombre, []):
        v = _SECRETS.get(n.upper()) or os.environ.get(n, "")
        if str(v).strip():
            return str(v).strip().strip('"').strip("'")
    return ""


# Las variables opcionales (IA_ORDEN, modelos, etc.) se leen de os.environ en ia_motores
for _var in ["IA_ORDEN", "IA_RESPALDO_CLAUDE", "GEMINI_MODELO", "GEMINI_MODELO_RAPIDO", "MISTRAL_MODELO",
             "MISTRAL_MODELO_RAPIDO", "GROQ_MODELO", "GROQ_MODELO_RAPIDO", "OPENROUTER_MODELO",
             "OPENROUTER_MODELO_RAPIDO", "CLAUDE_MODELO", "CLAUDE_MODELO_RAPIDO"]:
    _v = _secreto(_var)
    if _v:
        os.environ[_var] = _v

ss = st.session_state
ss.setdefault("vista", VISTAS[0])
ss.setdefault("nota_sel", None)          # nota elegida en Noticias para analizar
ss.setdefault("resultados", [])          # todo lo que generó la IA en la sesión
ss.setdefault("chats", {})               # preguntas sobre cada nota
ss.setdefault("tema", {"titulo": "", "notas": []})
ss.setdefault("tit_tema", "")


# Streamlit borra el valor de un widget cuando no se dibuja (por ejemplo, al cambiar de vista).
# Se reasignan para que cada vista recuerde lo que el usuario eligió.
_PERSISTIR = ("modo_noticias", "q_tema", "alc_tema", "secs_dia", "origen_nota", "link_manual", "txt_tit", "txt_med",
              "txt_cuerpo", "n_leer", "tit_tema")
_PREFIJOS = ("pl_", "libre_", "q_", "sel_tema_")
for _key in list(ss.keys()):
    if _key in _PERSISTIR or (isinstance(_key, str) and _key.startswith(_PREFIJOS)):
        ss[_key] = ss[_key]


def nombre_motor(m):
    return {"auto": "Automático · gratis primero", "claude": "Claude primero · pago"}.get(
        m, f"{ia_motores.NOMBRES.get(m, m)} · gratis")


def _k(*partes):
    return hashlib.md5("|".join(str(p) for p in partes).encode()).hexdigest()[:10]


# ═══════════════════════ lectura con caché ═══════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def cargar_seccion(sid, limite):
    ids = [f["id"] for f in SECCION_POR_ID[sid]["fuentes"]]
    return lector.leer_varias(ids, limite)


@st.cache_resource(show_spinner=False)
def _almacen_notas():
    """Notas completas ya leídas (por link), compartidas entre recargas."""
    return {}


def _leer(url, almacen):
    if url in almacen:
        return almacen[url]
    try:
        a = lector.leer_articulo(url)
    except Exception as e:
        return {"error": str(e)[:200]}
    if a.get("parrafos"):
        almacen[url] = a
        if len(almacen) > 400:
            almacen.pop(next(iter(almacen)))
    return a


def articulo_de(url):
    return _leer(url, _almacen_notas())


def cargar_articulos(notas):
    """Lee varias notas completas en paralelo. Si una no se puede leer, va con título y bajada."""
    almacen = _almacen_notas()

    def uno(n):
        url = n.get("url") or ""
        a = _leer(url, almacen) if url and "news.google.com" not in url else {"error": "Google News"}
        if a.get("error") or not a.get("parrafos"):
            return {"titulo": n["titulo"], "bajada": n.get("bajada", ""), "parrafos": [], "medio": n.get("medio", ""),
                    "url": url, "incompleta": True}
        return {**a, "titulo": a.get("titulo") or n["titulo"], "medio": n.get("medio") or a.get("medio", "")}
    with ThreadPoolExecutor(max_workers=6) as ex:
        return list(ex.map(uno, notas))


def silenciada(n, palabras):
    if not palabras:
        return False
    t = lector.norm(n["titulo"] + " " + (n.get("bajada") or ""))
    return any(p in t for p in palabras)


def notas_de(resultado, medios_ok=None, palabras=()):
    out = []
    for r in resultado:
        if medios_ok is not None and r["id"] not in medios_ok:
            continue
        out += [n for n in r["items"] if not silenciada(n, palabras)]
    return out


# ═══════════════════════ IA ═══════════════════════
def hay_ia():
    return ia_motores.hay_motor()


def correr(plantilla, material, ambito, clave, titulo):
    """Corre una plantilla y guarda el resultado en la sesión."""
    if not hay_ia():
        st.error("Configurá un motor de IA en el panel izquierdo (🤖 Motores de IA), o usá **📋 Pedido para copiar**.")
        return None
    max_tok = plantilla["max_tokens"]
    cadena = ia_motores.cadena()
    if cadena and cadena[0] == "groq":            # el plan gratuito de Groq acepta pedidos cortos
        material = material[:14000]
    primero = ia_motores.NOMBRES.get(cadena[0], "") if cadena else ""
    with st.spinner(f"{plantilla['icono']} {plantilla['nombre']} con {primero}… (puede tardar un minuto)"):
        try:
            texto = ia_motores.generar(material, max_tokens=max_tok, nivel=plantilla["nivel"], system=plantilla["system"])
        except Exception as e:
            st.error(str(e))
            return None
    res = {"id": _k(clave, plantilla["id"], datetime.now().timestamp()), "ambito": ambito, "clave": clave,
           "titulo": titulo, "plantilla": plantilla["nombre"], "icono": plantilla["icono"], "pid": plantilla["id"],
           "texto": texto, "motor": ia_motores.ULTIMO.get("nombre", ""), "modelo": ia_motores.ULTIMO.get("modelo", ""),
           "hora": datetime.now(TZ).strftime("%d/%m %H:%M")}
    ss.resultados.insert(0, res)
    return res


def _iframe(contenido, alto):
    """HTML con JavaScript propio (voz del navegador, diagramas). st.iframe en Streamlit nuevo, components.html en el viejo."""
    if hasattr(st, "iframe"):
        st.iframe(contenido, height=alto)
    else:
        components.html(contenido, height=alto, scrolling=True)


def _js(texto):
    """Texto como literal de JavaScript, seguro dentro de <script>."""
    return json.dumps(texto).replace("</", "<\\/").replace("<!--", "<\\!--")


_IAS = [("ChatGPT", "https://chatgpt.com/"), ("Claude", "https://claude.ai/new"), ("Gemini", "https://gemini.google.com/app")]


def boton_copiar(texto, key, etiqueta="📋 Copiar", abrir=False):
    """Copia el texto al portapapeles con un clic (sin descargar nada).
    Con abrir=True suma botones que copian y abren ChatGPT, Claude o Gemini en otra pestaña: ahí solo hay que pegar."""
    botones = f'<button class="b p" data-u="">{html.escape(etiqueta)}</button>'
    if abrir:
        botones += "".join(f'<button class="b" data-u="{u}">Copiar y abrir {n} ↗</button>' for n, u in _IAS)
    _iframe(f"""
<style>
 body{{margin:0;font-family:"Source Sans Pro",system-ui,sans-serif}}
 .w{{display:flex;gap:.4rem;flex-wrap:wrap;align-items:center}}
 .b{{padding:.42rem .85rem;border-radius:8px;border:1px solid #ccc;background:#fff;cursor:pointer;font-size:.9rem;color:#222}}
 .b:hover{{border-color:#e34535;color:#e34535}}
 .p{{background:#e34535;border-color:#e34535;color:#fff;font-weight:600}} .p:hover{{color:#fff;filter:brightness(.95)}}
 .ok{{font-size:.85rem;color:#1a7f37}}
 @media (prefers-color-scheme: dark){{.b{{background:#262730;color:#fafafa;border-color:#555}}}}
</style>
<div class="w">{botones}<span class="ok" id="ok"></span></div>
<script>
const T={_js(texto)};
async function copiar(){{
  try {{ await navigator.clipboard.writeText(T); return true; }} catch(e) {{
    const a=document.createElement('textarea'); a.value=T; a.style.position='fixed'; a.style.opacity='0';
    document.body.appendChild(a); a.focus(); a.select(); let ok=false;
    try {{ ok=document.execCommand('copy'); }} catch(_) {{}} a.remove(); return ok; }}
}}
document.querySelectorAll('.b').forEach(b=>b.onclick=async()=>{{
  const ok=await copiar(); const u=b.dataset.u;
  document.getElementById('ok').textContent = ok ? (u ? '✔ Copiado: en la otra pestaña, pegalo con Ctrl+V' : '✔ Copiado') : '✖ No se pudo copiar: usá el recuadro de abajo';
  if(u) window.open(u,'_blank','noopener');
  setTimeout(()=>document.getElementById('ok').textContent='', 6000);
}});
</script>""", 80 if abrir else 46)


def _limpiar_para_voz(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.DOTALL)
    t = re.sub(r"\|.*\|", " ", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"[#*_>`~]+", "", t)
    t = re.sub(r"^\s*[-•]\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def boton_escuchar(texto, key):
    """Lee el texto en voz alta con la voz del navegador (gratis, no usa la IA)."""
    t = _js(_limpiar_para_voz(texto))
    _iframe(f"""
<div style="font-family:system-ui,sans-serif;display:flex;gap:.4rem;align-items:center;flex-wrap:wrap">
 <button id="p" style="padding:.35rem .8rem;border-radius:8px;border:1px solid #bbb;background:#fff;cursor:pointer">🔊 Escuchar</button>
 <button id="s" style="padding:.35rem .8rem;border-radius:8px;border:1px solid #bbb;background:#fff;cursor:pointer">⏹</button>
 <label style="font-size:.8rem;color:#666">Velocidad
  <select id="v"><option>0.9</option><option selected>1</option><option>1.15</option><option>1.3</option><option>1.5</option></select></label>
 <span id="e" style="font-size:.8rem;color:#666"></span>
</div>
<script>
const T={t};const S=window.speechSynthesis;let parr=T.split(/\\n\\s*\\n/).filter(x=>x.trim());let i=0,on=false,pausa=false;
function voz(){{const vs=S.getVoices();return vs.find(v=>/es-AR/i.test(v.lang)&&/natural|online/i.test(v.name))||vs.find(v=>/es-AR/i.test(v.lang))||vs.find(v=>/es-(419|US|MX)/i.test(v.lang))||vs.find(v=>/^es/i.test(v.lang));}}
function leer(){{if(i>=parr.length){{on=false;document.getElementById('p').textContent='🔊 Escuchar';document.getElementById('e').textContent='';return;}}
 const u=new SpeechSynthesisUtterance(parr[i]);const vv=voz();if(vv)u.voice=vv;u.lang=vv?vv.lang:'es-AR';u.rate=parseFloat(document.getElementById('v').value);
 u.onend=()=>{{if(on&&!pausa){{i++;leer();}}}};document.getElementById('e').textContent='párrafo '+(i+1)+' de '+parr.length;S.speak(u);}}
document.getElementById('p').onclick=()=>{{const b=document.getElementById('p');
 if(!on){{S.cancel();on=true;pausa=false;b.textContent='⏸ Pausa';leer();}}
 else if(!pausa){{pausa=true;S.pause();b.textContent='▶ Seguir';}}
 else{{pausa=false;S.resume();b.textContent='⏸ Pausa';}}}};
document.getElementById('s').onclick=()=>{{on=false;pausa=false;S.cancel();i=0;document.getElementById('p').textContent='🔊 Escuchar';document.getElementById('e').textContent='';}};
</script>""", 50)


def mermaid(code, key):
    alto = 140 + 42 * min(14, code.count("\n"))
    _iframe(f"""
<div class="mermaid" style="font-family:system-ui,sans-serif">{html.escape(code)}</div>
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({{startOnLoad:false, theme:'neutral', securityLevel:'strict'}});
try {{ await mermaid.run({{querySelector:'.mermaid'}}); }} catch(e) {{
  document.querySelector('.mermaid').outerHTML = '<pre style="white-space:pre-wrap">'+{_js(code)}.replace(/</g,'&lt;')+'</pre>'; }}
</script>""", alto)


_RE_P = re.compile(r"^\s*(?:[-*]\s*)?\*\*P:?\*\*:?\s*(.+)$")
_RE_R = re.compile(r"^\s*(?:[-*]\s*)?\*\*R:?\*\*:?\s*(.+)$")
_RE_RESP = re.compile(r"^\s*(?:[-*]\s*)?\*\*Respuesta:?\*\*:?\s*(.+)$")


def _html_simple(t):
    t = html.escape(t)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


def _desplegable(titulo, cuerpo, tarjeta=False):
    """Un desplegable en HTML (los expanders de Streamlit no se pueden anidar y el resultado ya está en uno)."""
    borde = "border:1px solid rgba(127,127,127,.35);border-radius:10px;padding:.55rem .8rem;margin:.35rem 0;" if tarjeta \
        else "margin:.1rem 0 .6rem 1.2rem;"
    st.markdown(f"<details style='{borde}'><summary style='cursor:pointer;font-weight:{600 if tarjeta else 500}'>"
                f"{_html_simple(titulo)}</summary><div style='margin-top:.45rem'>{_html_simple(cuerpo)}</div></details>",
                unsafe_allow_html=True)


def _markdown_con_repaso(texto, key):
    """Markdown normal, pero las tarjetas (**P:** / **R:**) se muestran para dar vuelta
    y las líneas **Respuesta:** quedan ocultas hasta tocarlas: primero se intenta recordar."""
    texto = re.sub(r"^#{1,3}\s", "#### ", texto, flags=re.MULTILINE)   # títulos a tamaño de lectura
    texto = re.sub(r"\n(\s*[a-dA-D]\)\s)", r"  \n\1", texto)              # opciones a) b) c) d) en líneas separadas
    buf, lineas, i, n_tarj = [], texto.split("\n"), 0, 0

    def volcar():
        if "".join(buf).strip():
            st.markdown("\n".join(buf))
        buf.clear()
    while i < len(lineas):
        lin = lineas[i]
        mp, mr = _RE_P.match(lin), _RE_RESP.match(lin)
        if mp:
            j = i + 1
            while j < len(lineas) and not lineas[j].strip():
                j += 1
            mrr = _RE_R.match(lineas[j]) if j < len(lineas) else None
            if mrr:
                volcar()
                n_tarj += 1
                _desplegable(f"🃏 {n_tarj}. {mp.group(1).strip()}", mrr.group(1).strip(), tarjeta=True)
                i = j + 1
                continue
        if mr:
            volcar()
            _desplegable("👀 Ver respuesta", mr.group(1).strip())
            i += 1
            continue
        buf.append(lin)
        i += 1
    volcar()
    if n_tarj:
        st.caption("Tratá de responder cada tarjeta antes de abrirla: recordar activamente es lo que fija la memoria.")


def mostrar_texto_ia(texto, key):
    """Markdown con soporte para diagramas Mermaid."""
    partes = re.split(r"```mermaid\s*\n(.*?)```", texto, flags=re.DOTALL)
    for i, parte in enumerate(partes):
        if i % 2 == 1:
            mermaid(parte.strip(), f"{key}_{i}")
            with st.expander("Código del diagrama"):
                st.code(parte.strip(), language="text")
        elif parte.strip():
            _markdown_con_repaso(parte, f"{key}_{i}")


def mostrar_resultado(res, expandido=True):
    with st.expander(f"{res['icono']} {res['plantilla']} · {res['hora']}", expanded=expandido):
        mostrar_texto_ia(res["texto"], res["id"])
        st.caption(f"Escrito por {res['motor']} ({res['modelo']})")
        c1, c2 = st.columns([1, 3])
        nombre = re.sub(r"[^\w]+", "_", f"{res['plantilla']}_{res['titulo']}")[:60].strip("_")
        c1.download_button("📥 Descargar .md", f"# {res['titulo']}\n\n_{res['plantilla']} · {res['hora']}_\n\n{res['texto']}",
                           file_name=f"{nombre}.md", mime="text/markdown", key=f"dl_{res['id']}")
        with c2:
            boton_escuchar(res["texto"], res["id"])
        boton_copiar(res["texto"], f"cp_{res['id']}", "📋 Copiar el resultado")


def selector_plantilla(ambito, key):
    """Pastillas con las plantillas del ámbito. Devuelve la plantilla elegida (o la libre)."""
    lista = P.PLANTILLAS[ambito]
    opciones = [p["id"] for p in lista] + ["libre"]
    etiquetas = {p["id"]: f"{p['icono']} {p['nombre']}" for p in lista}
    etiquetas["libre"] = "✍️ Mi propio pedido"
    ss.setdefault(f"pl_{key}", opciones[0])
    pid = st.pills("Plantilla", opciones, format_func=lambda x: etiquetas[x], key=f"pl_{key}",
                   selection_mode="single") or opciones[0]
    if pid == "libre":
        pedido = st.text_area("¿Qué querés que haga la IA?", key=f"libre_{key}",
                              placeholder="Ej.: armame 5 preguntas para una entrevista al protagonista / "
                                          "compará con lo que pasó en 2001 / explicame el impacto en mi bolsillo")
        return P.plantilla_libre(ambito, pedido) if pedido.strip() else None
    p = P.por_id(ambito, pid)
    st.markdown(f"<div class='mg-desc'>{p['desc']}</div>", unsafe_allow_html=True)
    return p


def bloque_pedido(plantilla, material, key, nombre_archivo):
    """El pedido completo para pegar en ChatGPT / Claude / Gemini, sin API key."""
    pedido = P.pedido_para_copiar(plantilla, material)
    largo = f"{len(pedido):,}".replace(",", ".")
    st.caption(f"Sin API key: copiá el pedido completo (instrucciones + material, {largo} caracteres) "
               "y pegalo en la IA que quieras.")
    boton_copiar(pedido, f"cpp_{key}", "📋 Copiar pedido", abrir=True)
    with st.expander("Ver el pedido"):
        st.code(pedido, language="text", wrap_lines=True)
        st.download_button("📥 Descargar .txt (si es muy largo para pegar)", pedido,
                           file_name=f"{nombre_archivo}.txt", key=f"dlp_{key}")


# ═══════════════════════ barra lateral ═══════════════════════
with st.sidebar:
    st.markdown("## 📡 Monitor General")
    st.caption("Los medios de Panorama, con IA para entender y resumir.")

    sid = st.selectbox("Sección", [s["id"] for s in SECCIONES], format_func=lambda x: NOMBRE_SECCION[x], key="seccion")
    seccion = SECCION_POR_ID[sid]
    fuentes_sec = seccion["fuentes"]
    langs = sorted({f["lang"] for f in fuentes_sec})
    if len(langs) > 1:
        idiomas = st.multiselect("Idiomas", langs, default=langs, format_func=lambda l: NOMBRES_IDIOMA.get(l, l),
                                 key=f"idiomas_{sid}")
    else:
        idiomas = langs
    medios_disp = [f["id"] for f in fuentes_sec if f["lang"] in idiomas]
    with st.expander(f"Medios ({len(medios_disp)})"):
        medios = st.multiselect("Medios", medios_disp, default=medios_disp, key=f"medios_{sid}_{'-'.join(idiomas)}",
                                format_func=lambda x: FUENTE_POR_ID[x]["nombre"], label_visibility="collapsed")
    limite = st.select_slider("Notas por medio", [8, 14, 20, 30], value=14, key="limite")
    silencio_txt = st.text_input("🔇 Silenciar palabras", placeholder="horóscopo, quiniela", key="silenciar",
                                 help="Separadas por coma. Las notas que las mencionan no se muestran.")
    silencio = tuple(lector.norm(x).strip() for x in silencio_txt.split(",") if lector.norm(x).strip())
    if st.button("🔄 Actualizar noticias", use_container_width=True):
        cargar_seccion.clear()
        st.rerun()

    st.divider()
    st.markdown("**🤖 Motores de IA**")
    claves_ia = {m: (ss.get(f"clave_{m}") or _secreto(ia_motores.ENV[m])) for m in ia_motores.ENV}
    ia_motores.configurar(claves=claves_ia)
    disp = ia_motores.disponibles()
    ops = (["auto"] if len([m for m in disp if m != "claude"]) else []) + (["claude"] if "claude" in disp else []) \
        + [m for m in disp if m != "claude"]
    ops = list(dict.fromkeys(ops)) or ["auto"]
    if ss.get("motor_ia") not in ops:
        ss["motor_ia"] = ops[0]
    motor = st.selectbox("Motor", ops, format_func=nombre_motor, key="motor_ia",
                         help="Automático prueba los gratuitos en orden y usa Claude solo si fallan todos.")
    ia_motores.configurar(motor=motor)
    if disp:
        st.caption(f"Orden: {ia_motores.descripcion_cadena()}")
    else:
        st.warning("No hay ninguna clave cargada. Podés pegar una abajo, o usar **📋 Pedido para copiar** "
                   "en ChatGPT/Claude sin clave.")
    with st.expander("🔍 ¿Qué claves encuentra la app?", expanded=not disp):
        if _ERROR_SECRETS:
            st.error(f"No se pudieron leer los Secrets: el texto tiene un error de formato ({_ERROR_SECRETS}). "
                     "Revisá comillas y que cada clave esté en su propia línea, por ejemplo: GEMINI_API_KEY = \"AIza...\"")
        for m in ia_motores.GRATIS + ["claude"]:
            nombre = ia_motores.ENV[m]
            if ss.get(f"clave_{m}"):
                st.markdown(f"✅ {ia_motores.NOMBRES[m]}: pegada en esta sesión")
            elif _secreto(nombre):
                st.markdown(f"✅ {ia_motores.NOMBRES[m]}: en Secrets")
            else:
                st.markdown(f"⬜ {ia_motores.NOMBRES[m]}: falta `{nombre}`")
        nombres = sorted(k for k in _SECRETS if any(x in k for x in ("KEY", "API", "TOKEN", "GEMINI", "GROQ", "MISTRAL",
                                                                       "OPENROUTER", "CLAUDE", "ANTHROPIC")))
        st.caption("Nombres que la app ve en Secrets (sin mostrar los valores): "
                   + (", ".join(f"`{n}`" for n in nombres) if nombres else "ninguno.")
                   + " Después de cambiar los Secrets puede hacer falta **Reboot app**.")
    with st.expander("🔑 Claves (para esta sesión)"):
        st.caption("Lo mejor es dejarlas en los Secrets de Streamlit. Las que pegues acá duran lo que dura la sesión.")
        for m in ia_motores.GRATIS + ["claude"]:
            st.text_input(f"{ia_motores.NOMBRES[m]}{' (pago)' if m == 'claude' else ' (gratis)'}", type="password",
                          key=f"clave_{m}", help=f"Secret: {ia_motores.ENV[m]}")
    ss.setdefault("traducir_tit", True)
    st.toggle("🌐 Traducir títulos de otros idiomas", key="traducir_tit", disabled=not disp,
              help="Los títulos en inglés, francés, italiano, alemán o portugués se muestran en español. "
                   "Usa el modelo rápido (gratis primero) y cada título se traduce una sola vez.")


# ═══════════════════════ carga de la sección ═══════════════════════
with st.spinner(f"Leyendo {len(fuentes_sec)} medios de {seccion['nombre']}…"):
    resultado = cargar_seccion(sid, limite)


@st.cache_resource(show_spinner=False)
def _memoria_traducciones():
    """Títulos ya traducidos (original → español), compartidos entre recargas y sesiones."""
    return {}


def preparar(notas):
    """Traduce los títulos en otros idiomas (si está activado) y los deja en n['titulo_es']."""
    memoria = _memoria_traducciones()
    if ss.get("traducir_tit") and hay_ia():
        ajenas = [n["titulo"] for n in notas if n.get("lang", "es") != "es"]
        nuevas = len({t for t in ajenas if t not in memoria and time.time() - traductor._FALLOS.get(t, 0) > traductor.REINTENTO_SEG})
        if nuevas:
            with st.spinner(f"🌐 Traduciendo {nuevas} títulos…"):
                hechas, error = traductor.traducir_titulos(ajenas, memoria)
            if error:
                st.toast(f"No se pudieron traducir algunos títulos: {error[:150]}", icon="🌐")
    if ss.get("traducir_tit"):
        traductor.aplicar(notas, memoria)
    return notas


notas_sec = preparar(notas_de(resultado, set(medios), silencio))

st.radio("Vista", VISTAS, key="vista", horizontal=True, label_visibility="collapsed")
vista = ss.vista


def ir_a(v):
    ss.vista = v


def elegir_nota(n):
    ss.nota_sel = n
    ss.origen_nota = "Nota elegida"
    ss.vista = "🧠 Analizar nota"


def sumar_a_tema(n):
    if not any(x.get("url") == n.get("url") for x in ss.tema["notas"]):
        ss.tema["notas"].append(n)
    if not ss.tema["titulo"]:
        ss.tema["titulo"] = ss.tit_tema = n["titulo"]


def mandar_tema(titulo, notas):
    ss.tema = {"titulo": titulo, "notas": list(notas)}
    ss.tit_tema = titulo
    ss.vista = "🗂️ Tema"


def _hora(n):
    if not n.get("fecha"):
        return ""
    try:
        d = datetime.fromisoformat(n["fecha"])
        mins = int((datetime.now(timezone.utc) - d).total_seconds() // 60)
        if mins < 60:
            return f"hace {max(mins, 1)} min"
        if mins < 24 * 60:
            return f"hace {mins // 60} h"
        return d.astimezone(TZ).strftime("%d/%m %H:%M")
    except Exception:
        return ""


def fila_nota(n, pref, con_medio=False):
    c1, c2, c3 = st.columns([14, 1, 1], vertical_alignment="center")
    meta = []
    if con_medio:
        meta.append(f"<span class='mg-dot' style='background:{n.get('color', '#888')};width:.55rem;height:.55rem'></span> {html.escape(n.get('medio', ''))}")
    if _hora(n):
        meta.append(_hora(n))
    if n.get("via") == "google":
        meta.append("vía Google News")
    titulo, original = n["titulo"], ""
    if n.get("lang", "es") != "es":
        idioma = NOMBRES_IDIOMA.get(n["lang"], n["lang"])
        if n.get("titulo_es"):
            titulo = n["titulo_es"]
            meta.append(f"🌐 traducido del {idioma}")
            original = f"<div class='mg-bajada' style='font-style:italic'>{html.escape(n['titulo'])}</div>"
        else:
            meta.append(idioma)
    bajada = f"<div class='mg-bajada'>{html.escape(n['bajada'][:220])}</div>" if n.get("bajada") else ""
    c1.markdown(f"<div class='mg-tit'><a href='{html.escape(n.get('url') or '#')}' target='_blank'>{html.escape(titulo)}</a></div>{original}"
                f"<div class='mg-meta'>{' · '.join(meta)}</div>{bajada}", unsafe_allow_html=True)
    k = _k(pref, n.get("url"), n["titulo"])
    c2.button("🧠", key=f"an_{k}", help="Analizar con IA", on_click=elegir_nota, args=(n,))
    c3.button("➕", key=f"te_{k}", help="Sumar al tema", on_click=sumar_a_tema, args=(n,))


# ═══════════════════════ 📰 NOTICIAS ═══════════════════════
if vista == "📰 Noticias":
    ok = [r for r in resultado if r["id"] in medios]
    n_ok = sum(1 for r in ok if r["estado"] == "ok")
    st.markdown(f"### {seccion['nombre']}")
    st.caption(f"{seccion.get('desc', '')} · {n_ok} de {len(ok)} medios respondieron · {len(notas_sec)} notas · "
               f"actualizado {datetime.now(TZ).strftime('%H:%M')}")
    if ss.tema["notas"]:
        st.info(f"🗂️ Tema en armado: **{len(ss.tema['notas'])} notas**.", icon="➕")
        st.button("Ir al tema →", on_click=ir_a, args=("🗂️ Tema",))

    c1, c2 = st.columns([2, 1])
    q = c1.text_input("🔎 Buscar en la sección", placeholder="Palabras, separadas por coma", key=f"q_{sid}")
    modo = c2.radio("Ver", ["Por medio", "Intercalado", "Por tema"], horizontal=True, key="modo_noticias")

    if q.strip():
        encontradas = lector.buscar(notas_sec, q)
        st.markdown(f"**{len(encontradas)} notas** con *{q}*")
        if encontradas:
            st.button("🗂️ Analizar estas notas como un tema", on_click=mandar_tema,
                      args=(q, lector.una_por_medio(encontradas, 30)))
        for n in encontradas:
            fila_nota(n, "q", con_medio=True)
    elif modo == "Por medio":
        for i, r in enumerate(ok):
            f = FUENTE_POR_ID[r["id"]]
            items = [n for n in r["items"] if not silenciada(n, silencio)]
            extra = " · vía Google News" if r.get("via") == "google" else ""
            estado = f"{len(items)} notas{extra}" if r["estado"] == "ok" else "⚠️ sin respuesta"
            with st.expander(f"{f['nombre']} — {estado}", expanded=i < 3):
                if r["estado"] != "ok":
                    st.caption(f"No se pudo leer: {r.get('error') or 'sin notas'}")
                for n in items:
                    fila_nota(n, r["id"])
    elif modo == "Intercalado":
        por_puesto = sorted(notas_sec, key=lambda n: (n.get("puesto", 0), medios.index(n["medio_id"]) if n["medio_id"] in medios else 99))
        for n in por_puesto[:150]:
            fila_nota(n, "int", con_medio=True)
    else:
        grupos = lector.curar(notas_sec)
        st.caption("Titulares agrupados por historia, ordenados por cuántos medios los tienen y si van en tapa. Sin IA.")
        for g in grupos[:40]:
            chips = f"<span class='mg-chip'>{len(g['medios'])} medios</span>" + ("<span class='mg-chip'>en tapa</span>" if g["rmin"] == 0 else "")
            st.markdown(f"{chips} **{html.escape(g['titulo'])}**", unsafe_allow_html=True)
            cc = st.columns([3, 1, 1])
            cc[0].caption(" · ".join(g["medios"][:8]) + (" …" if len(g["medios"]) > 8 else ""))
            cc[1].button("🗂️ Tema", key=f"gt_{_k(g['titulo'])}", on_click=mandar_tema, args=(g["titulo"], g["notas"]),
                         help="Analizar todas las notas de esta historia")
            cc[2].button("🧠 Nota", key=f"gn_{_k(g['titulo'])}", on_click=elegir_nota, args=(g["notas"][0],),
                         help="Analizar la nota principal")
            if len(g["notas"]) > 1:
                with st.expander(f"Ver las {len(g['notas'])} notas"):
                    for n in g["notas"]:
                        fila_nota(n, "g" + _k(g["titulo"]), con_medio=True)
            st.divider()


# ═══════════════════════ 🧠 ANALIZAR NOTA ═══════════════════════
elif vista == "🧠 Analizar nota":
    st.markdown("### 🧠 Analizar una nota")
    ss.setdefault("origen_nota", "Nota elegida" if ss.nota_sel else "Pegar un link")
    origen = st.radio("Origen", ["Nota elegida", "Pegar un link", "Pegar un texto"], horizontal=True,
                      key="origen_nota", label_visibility="collapsed")
    art, clave_nota = None, None

    if origen == "Nota elegida":
        n = ss.nota_sel
        if not n:
            st.info("Elegí una nota en **📰 Noticias** con el botón 🧠, o pegá un link o un texto.")
        else:
            clave_nota = n.get("url") or n["titulo"]
            with st.spinner("Leyendo la nota…"):
                a = articulo_de(n["url"]) if n.get("url") and "news.google.com" not in n["url"] else {"error": "Google News"}
            if a.get("error") or not a.get("parrafos"):
                st.warning("No se pudo leer el texto completo (muro de pago, Google News o el sitio no responde): "
                           "la IA va a trabajar con el título y la bajada.")
                art = {"titulo": n["titulo"], "bajada": n.get("bajada", ""), "parrafos": [], "medio": n.get("medio", ""),
                       "url": n.get("url", "")}
            else:
                art = {**a, "medio": n.get("medio") or a.get("medio", "")}
            art["lang"] = n.get("lang", "es")
    elif origen == "Pegar un link":
        url = st.text_input("Link de la nota", key="link_manual", placeholder="https://…")
        if url.strip().startswith("http"):
            clave_nota = url.strip()
            with st.spinner("Leyendo la nota…"):
                a = articulo_de(url.strip())
            if a.get("error"):
                st.error(f"No se pudo leer la nota: {a['error']}")
            elif not a.get("parrafos"):
                st.warning("La página no tiene texto legible (puede tener muro de pago). Probá pegando el texto.")
                art = {**a, "lang": "es"}
            else:
                art = {**a, "lang": "es"}
    else:
        c1, c2 = st.columns([3, 1])
        tit = c1.text_input("Título (opcional)", key="txt_tit")
        med = c2.text_input("Medio (opcional)", key="txt_med")
        cuerpo = st.text_area("Texto de la nota", height=220, key="txt_cuerpo",
                              placeholder="Pegá acá el texto completo de la nota, un comunicado, un informe…")
        if len(cuerpo.strip()) > 80:
            clave_nota = "texto-" + _k(cuerpo)
            art = {"titulo": tit or cuerpo.strip().split("\n")[0][:120], "bajada": "", "medio": med or "texto pegado",
                   "parrafos": [p for p in re.split(r"\n\s*\n|\n", cuerpo) if p.strip()], "url": "", "lang": "es"}

    if art:
        col_a, col_b = st.columns([3, 2], gap="large")
        with col_a:
            st.markdown(f"#### {art['titulo']}")
            meta = " · ".join(x for x in [art.get("medio"), f"{sum(len(p.split()) for p in art.get('parrafos') or [])} palabras"
                                          if art.get("parrafos") else "solo título"] if x)
            st.caption(meta + (f" · [abrir en el medio]({art['url']})" if art.get("url") else ""))
            if art.get("bajada"):
                st.markdown(f"*{art['bajada']}*")
            if art.get("parrafos"):
                with st.expander("Leer la nota"):
                    if art.get("imagen"):
                        st.image(art["imagen"], use_container_width=True)
                    for p in art["parrafos"]:
                        st.markdown(p)
        with col_b:
            if art.get("imagen"):
                st.image(art["imagen"], use_container_width=True)

        st.markdown("##### ¿Qué querés hacer con la nota?")
        if art.get("lang", "es") != "es":
            st.caption(f"🌐 Esta nota está en {NOMBRES_IDIOMA.get(art['lang'], art['lang'])}: las plantillas responden en "
                       "español, y **🌐 Traducir al español** la traduce completa.")
        plantilla = selector_plantilla("nota", "nota")
        material = P.material_nota(art)
        if plantilla:
            if st.button("✦ Generar con IA", type="primary", key="gen_nota"):
                correr(plantilla, material, "nota", clave_nota, art["titulo"])
            bloque_pedido(plantilla, material, "nota", "pedido_nota")

        previos = [r for r in ss.resultados if r["ambito"] == "nota" and r["clave"] == clave_nota]
        for i, r in enumerate(previos):
            mostrar_resultado(r, expandido=i == 0)

        # Preguntas sobre la nota
        st.markdown("##### 💬 Preguntale a la nota")
        chat = ss.chats.setdefault(clave_nota, [])
        for m in chat:
            with st.chat_message("user" if m["rol"] == "usuario" else "assistant"):
                st.markdown(m["texto"])
        with st.form(f"preg_{_k(clave_nota)}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1], vertical_alignment="bottom")
            preg = c1.text_input("Pregunta", placeholder="¿Qué significa…? ¿Quién es…? ¿Qué cambia para…?",
                                 label_visibility="collapsed")
            enviar = c2.form_submit_button("Preguntar", use_container_width=True)
        if enviar and preg.strip():
            if not hay_ia():
                st.error("Configurá un motor de IA en el panel izquierdo para preguntar.")
            else:
                hist = "\n".join(f"{'Lector' if m['rol'] == 'usuario' else 'Vos'}: {m['texto']}" for m in chat[-6:])
                pedido = (f"Esta es la nota:\n\n{P.material_nota(art, 16000)}\n\n"
                          + (f"Conversación hasta ahora:\n{hist}\n\n" if hist else "") + f"Pregunta del lector: {preg.strip()}")
                sistema = ("Respondés preguntas sobre una nota periodística, en español rioplatense claro y breve "
                           "(hasta 150 palabras salvo que pidan más detalle).\n- Si la respuesta está en la nota, respondé con eso.\n"
                           "- Si no está en la nota, podés usar conocimiento general estable, aclarando que no sale de la nota. "
                           "Si puede estar desactualizado (cargos, resultados, cifras recientes), avisalo.\n- Si no sabés, decilo. No inventes.")
                with st.spinner("Pensando…"):
                    try:
                        resp = ia_motores.generar(pedido, max_tokens=1500, system=sistema)
                        chat += [{"rol": "usuario", "texto": preg.strip()}, {"rol": "ia", "texto": resp}]
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


# ═══════════════════════ 🗂️ TEMA ═══════════════════════
elif vista == "🗂️ Tema":
    st.markdown("### 🗂️ Un tema en todos los medios")
    st.caption("Juntá las notas de distintos medios sobre una misma historia y analizalas juntas.")

    with st.expander("🔎 Buscar notas por palabra clave", expanded=not ss.tema["notas"]):
        c1, c2 = st.columns([2, 1])
        q = c1.text_input("Palabras (separadas por coma)", key="q_tema", placeholder="inflación, FMI")
        alcance = c2.radio("Dónde", ["Esta sección", "Todas las secciones"], key="alc_tema", horizontal=True)
        if q.strip():
            if alcance == "Todas las secciones":
                universo, barra = [], st.progress(0.0, text="Leyendo todas las secciones…")
                for i, s in enumerate(SECCIONES):
                    universo += notas_de(cargar_seccion(s["id"], limite), palabras=silencio)
                    barra.progress((i + 1) / len(SECCIONES), text=f"Leyendo {s['nombre']}…")
                barra.empty()
            else:
                universo = notas_sec
            universo = preparar(universo)
            enc = lector.buscar(universo, q)
            vistos, unicas = set(), []
            for n in enc:
                if n.get("url") not in vistos:
                    vistos.add(n.get("url"))
                    unicas.append(n)
            st.caption(f"{len(unicas)} notas encontradas")
            if unicas:
                sugeridas = lector.una_por_medio(unicas, 8)
                idx = st.multiselect("Notas para el tema", list(range(len(unicas))),
                                     default=[unicas.index(n) for n in sugeridas],
                                     format_func=lambda i: f"[{unicas[i]['medio']}] {(unicas[i].get('titulo_es') or unicas[i]['titulo'])[:110]}",
                                     key=f"sel_tema_{_k(q, alcance)}")
                c = st.columns(2)
                c[0].button("✔ Usar estas notas", type="primary", on_click=mandar_tema, args=(q, [unicas[i] for i in idx]),
                            disabled=not idx)
                c[1].button("➕ Sumarlas a las que ya tengo",
                            on_click=lambda: [sumar_a_tema(unicas[i]) for i in idx], disabled=not idx)

    tema = ss.tema
    if not tema["notas"]:
        st.info("Todavía no hay notas en el tema. Buscá arriba, o en **📰 Noticias** tocá ➕ en cada nota, "
                "o **🗂️ Tema** en la vista *Por tema*.")
    else:
        tema["titulo"] = st.text_input("Nombre del tema", key="tit_tema")
        st.markdown(f"**{len(tema['notas'])} notas** de {len({n.get('medio') for n in tema['notas']})} medios")
        for i, n in enumerate(list(tema["notas"])):
            c1, c2 = st.columns([15, 1], vertical_alignment="center")
            c1.markdown(f"<span class='mg-chip'>{html.escape(n.get('medio', ''))}</span> "
                        f"<a href='{html.escape(n.get('url') or '#')}' target='_blank'>{html.escape(n.get('titulo_es') or n['titulo'])}</a>",
                        unsafe_allow_html=True)
            if c2.button("✕", key=f"qt_{i}_{_k(n.get('url'))}", help="Sacar del tema"):
                tema["notas"].pop(i)
                st.rerun()
        c1, c2 = st.columns([2, 1])
        ss.setdefault("n_leer", 5)
        n_leer = c1.slider("Notas a leer completas (una por medio primero)", 0, 8, key="n_leer",
                           help="Del resto se usan el título y la bajada. Más notas = análisis más rico, pero pedido más largo.")
        c2.button("🗑️ Vaciar tema", on_click=lambda: ss.update(tema={"titulo": "", "notas": []}, tit_tema=""))

        plantilla = selector_plantilla("tema", "tema")
        a_leer = lector.una_por_medio(tema["notas"], n_leer) if n_leer else []
        clave_tema = "tema-" + _k(tema["titulo"], *[n.get("url") for n in tema["notas"]])
        if plantilla:
            b1, b2 = st.columns([1, 3])
            gen = b1.button("✦ Generar con IA", type="primary", key="gen_tema", use_container_width=True)
            armar = b2.button("📋 Armar el pedido para ChatGPT, Claude o Gemini", key="armar_tema")
            if gen or armar or ss.get("pedido_tema_clave") == (clave_tema, plantilla["id"], n_leer):
                with st.spinner(f"Leyendo {len(a_leer)} notas completas…"):
                    arts = cargar_articulos(a_leer)
                inc = sum(1 for a in arts if a.get("incompleta"))
                if inc:
                    st.caption(f"⚠️ {inc} de {len(arts)} notas no se pudieron leer completas (muro de pago o Google News): "
                               "van con título y bajada.")
                material = P.material_tema(tema["titulo"], tema["notas"], arts)
                ss.pedido_tema_clave = (clave_tema, plantilla["id"], n_leer)
                if gen:
                    correr(plantilla, material, "tema", clave_tema, tema["titulo"])
                bloque_pedido(plantilla, material, "tema", "pedido_tema")

        for i, r in enumerate([r for r in ss.resultados if r["ambito"] == "tema" and r["clave"] == clave_tema]):
            mostrar_resultado(r, expandido=i == 0)


# ═══════════════════════ 🗞️ RESUMEN DEL DÍA ═══════════════════════
elif vista == "🗞️ Resumen del día":
    st.markdown("### 🗞️ Resumen del día")
    st.caption("Panorama agrupa los titulares que cuentan la misma historia y los ordena por cuántos medios los tienen "
               "y si van en tapa. La IA recibe esas historias ya curadas.")
    ss.setdefault("secs_dia", ["argentina", "economia", "mundo"])
    secs = st.multiselect("Secciones", [s["id"] for s in SECCIONES], format_func=lambda x: NOMBRE_SECCION[x], key="secs_dia")
    if secs:
        todas, por_seccion, barra = [], [], st.progress(0.0, text="Leyendo los medios…")
        for i, s in enumerate(secs):
            barra.progress(i / len(secs), text=f"Leyendo {NOMBRE_SECCION[s]}…")
            notas_s, tapas = [], {}
            for r in cargar_seccion(s, limite):
                items = [n for n in r["items"] if not silenciada(n, silencio)]
                notas_s += items
                if items:
                    tapas[r["nombre"]] = items[0]["titulo"]
            preparar(notas_s)
            tapas = {m: next((n.get("titulo_es") or n["titulo"] for n in notas_s if n["medio"] == m), t)
                     for m, t in tapas.items()}
            por_seccion.append((s, lector.curar(notas_s), tapas))
            todas += notas_s
        barra.empty()
        destacadas = lector.curar(todas) if len(secs) > 1 else []
        st.markdown(f"**{len(todas)} notas** de {len(secs)} secciones · cada sección se resume por separado, "
                    "así ninguna tapa a las otras.")

        with st.expander("Las historias más fuertes de cada sección (sin IA)"):
            pestañas = st.tabs([NOMBRE_SECCION[s] for s, _, _ in por_seccion])
            for tab, (s, grupos_s, tapas) in zip(pestañas, por_seccion):
                with tab:
                    st.caption(f"{len(tapas)} medios respondieron · {len(grupos_s)} historias")
                    for g in grupos_s[:12]:
                        st.markdown(f"<span class='mg-chip'>{len(g['medios'])} medios</span>"
                                    + ("<span class='mg-chip'>tapa</span>" if g["rmin"] == 0 else "")
                                    + f" {html.escape(g['titulo'])}", unsafe_allow_html=True)

        plantilla = selector_plantilla("dia", "dia")
        cad = ia_motores.cadena()
        maximo = 90 if cad and cad[0] == "groq" else 200
        alcance_txt = ", ".join(NOMBRE_SECCION[s] for s in secs)
        material = P.material_dia(por_seccion, destacadas, alcance_txt, datetime.now(TZ).strftime("%d/%m/%Y %H:%M"),
                                  NOMBRE_SECCION, maximo)
        clave_dia = "dia-" + "-".join(secs)
        if plantilla:
            if st.button("✦ Generar con IA", type="primary", key="gen_dia"):
                correr(plantilla, material, "dia", clave_dia, f"Resumen · {alcance_txt}")
            bloque_pedido(plantilla, material, "dia", "pedido_resumen_dia")
        for i, r in enumerate([r for r in ss.resultados if r["ambito"] == "dia" and r["clave"] == clave_dia]):
            mostrar_resultado(r, expandido=i == 0)


# ═══════════════════════ 🕘 HISTORIAL ═══════════════════════
else:
    st.markdown("### 🕘 Lo que generó la IA en esta sesión")
    if not ss.resultados:
        st.info("Todavía no hay nada. Los análisis y resúmenes que pidas aparecen acá.")
    else:
        todo = "\n\n---\n\n".join(f"# {r['titulo']}\n\n_{r['plantilla']} · {r['hora']} · {r['motor']}_\n\n{r['texto']}"
                                  for r in ss.resultados)
        c = st.columns([1, 1, 3])
        c[0].download_button("📥 Descargar todo (.md)", todo, file_name="monitor_general.md", mime="text/markdown")
        c[1].button("🗑️ Borrar historial", on_click=lambda: ss.update(resultados=[]))
        for r in ss.resultados:
            st.markdown(f"**{r['titulo'][:120]}**")
            mostrar_resultado(r, expandido=False)

st.caption(f"🤖 IA: {nombre_motor(ss.get('motor_ia', 'auto'))} — {ia_motores.descripcion_cadena()}")
