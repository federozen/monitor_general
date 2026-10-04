"""
Lectura de medios y notas (el mismo motor de lectura de Panorama, sin FastAPI).

- leer_fuente(f, limite): portada o feed RSS de un medio, con Google News de respaldo.
- leer_seccion(ids, limite): varias fuentes en paralelo.
- leer_articulo(url): título, bajada y párrafos de una nota.
- curar(items): agrupa titulares que cuentan la misma historia y los ordena por importancia.

No depende de Streamlit: la app le pone la caché encima.
"""
import re
import time
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from fuentes import FUENTE_POR_ID

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}
MAX_POR_MEDIO = 14
MAX_ANTIGUEDAD_HORAS = 72

# ─────────────────────────── imágenes ───────────────────────────
_GENERIC_PATS = ["logo", "brand", "favicon", "default", "placeholder", "og-default", "og_default",
                 "share-default", "icon", "sprite", "1x1", "pixel", "tracking", "blank.gif"]
_AUTOR_PATS = ["author", "autor", "firma", "byline", "avatar", "perfil", "profile", "journalist",
               "periodista", "columnist", "writer", "reporter", "signature", "bio", "headshot"]


def _generic(url):
    return not url or any(p in url.lower() for p in _GENERIC_PATS)


def _es_img_autor(tag):
    for parent in tag.parents:
        cls = " ".join(parent.get("class", [])).lower()
        pid = (parent.get("id") or "").lower()
        if any(p in cls or p in pid for p in _AUTOR_PATS):
            return True
        if parent.name in ("article", "section", "main"):
            break
    return False


def _img_score(tag, src):
    score = 0
    try:
        score += int(tag.get("width") or 0) + int(tag.get("height") or 0)
    except (ValueError, TypeError):
        pass
    cls = " ".join(tag.get("class", [])).lower()
    for g in ["featured", "hero", "portada", "principal", "cover", "thumb", "card-img", "wp-post-image", "size-large"]:
        if g in cls:
            score += 500
    if any(b in cls for b in _AUTOR_PATS) or _es_img_autor(tag):
        score -= 9999
    if tag.get("srcset") or tag.get("data-srcset"):
        score += 200
    m = re.search(r'[-/](\d{3,4})x(\d{3,4})[-/.]', src)
    if m:
        score += int(m.group(1)) + int(m.group(2))
    return score


def get_imagen(el):
    cands = []
    for tag in el.find_all("img"):
        if _es_img_autor(tag):
            continue
        best = ""
        ss = tag.get("srcset", "") or tag.get("data-srcset", "")
        if ss:
            sized = []
            for s in ss.split(","):
                p = s.strip().split(" ")
                try:
                    w = int(p[1].rstrip("w")) if len(p) > 1 and p[1].endswith("w") else 0
                except ValueError:
                    w = 0
                sized.append((w, p[0]))
            for _, u in sorted(sized, reverse=True):
                if u.startswith("http") and not _generic(u):
                    best = u
                    break
        if not best:
            for a in ["src", "data-src", "data-lazy-src", "data-original", "data-url", "data-image"]:
                s = tag.get(a, "")
                if s and s.startswith("http") and not s.endswith(".gif") and not _generic(s):
                    best = s
                    break
        if best:
            cands.append((_img_score(tag, best), best))
    if not cands:
        return ""
    cands.sort(reverse=True)
    return cands[0][1] if cands[0][0] > -100 else ""


# ─────────────────────────── RSS ───────────────────────────
def _rss_img(raw):
    for pat in [r'<media:content[^>]+url=["\']([^"\']+)["\']', r'<media:thumbnail[^>]+url=["\']([^"\']+)["\']',
                r'<enclosure[^>]+url=["\']([^"\']+\.(?:jpe?g|png|webp)[^"\']*)["\']']:
        m = re.search(pat, raw, re.IGNORECASE)
        if m and m.group(1).startswith("http") and not _generic(m.group(1)):
            return m.group(1).replace("&amp;", "&")
    for tag in ["content:encoded", "description", "content", "summary"]:
        m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', raw, re.DOTALL)
        if m:
            ct = m.group(1)
            cd = re.search(r'<!\[CDATA\[(.*?)\]\]>', ct, re.DOTALL)
            if cd:
                ct = cd.group(1)
            ct = ct.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&")
            im = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', ct)
            if im and im.group(1).startswith("http") and not _generic(im.group(1)):
                return im.group(1)
    return ""


def _fecha_item(item):
    for tag in ("pubDate", "published", "updated", "dc:date", "date"):
        t = item.find(tag)
        if t and t.get_text(strip=True):
            txt = t.get_text(strip=True)
            for parse in (parsedate_to_datetime, lambda x: datetime.fromisoformat(x.replace("Z", "+00:00"))):
                try:
                    d = parse(txt)
                    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
                except Exception:
                    pass
    return None


def _limpiar_titulo_gnews(t):
    """Google News agrega ' - Nombre del medio' al final."""
    if " - " in t:
        base = t.rsplit(" - ", 1)[0].strip()
        if len(base) >= 15:
            return base
    return t


def _texto(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&#8217;", "’"),
                 ("&#8216;", "‘"), ("&#8220;", "“"), ("&#8221;", "”"), ("&nbsp;", " ")):
        s = s.replace(a, b)
    return " ".join(s.split())


def extraer_rss(xml, limite):
    noticias, vistos = [], set()
    try:
        soup = BeautifulSoup(xml, "xml")
        items = soup.find_all(["item", "entry"])
        raws = re.findall(r'<(?:item|entry)[\s>].*?</(?:item|entry)>', xml, re.DOTALL | re.IGNORECASE)
        ahora = datetime.now(timezone.utc)
        for i, item in enumerate(items[:limite * 3]):
            if len(noticias) >= limite:
                break
            tt = item.find("title")
            if not tt:
                continue
            f = _fecha_item(item)
            if f and (ahora - f).total_seconds() > MAX_ANTIGUEDAD_HORAS * 3600:
                continue
            t = _texto(tt.get_text())
            if len(t) < 15 or len(t) > 300 or t in vistos:
                continue
            vistos.add(t)
            lk = item.find("link")
            url = (lk.get_text(strip=True) or lk.get("href")) if lk else None
            if not url or not url.startswith("http"):
                g = item.find("guid")
                gu = g.get_text(strip=True) if g else ""
                url = gu if gu.startswith("http") else url
            desc = item.find("description") or item.find("summary")
            bajada = _texto(desc.get_text())[:280] if desc else ""
            noticias.append({"titulo": t, "url": url, "imagen": _rss_img(raws[i]) if i < len(raws) else "",
                             "fecha": f.isoformat() if f else None, "bajada": bajada if len(bajada) > 40 else ""})
    except Exception:
        pass
    return noticias


# ─────────────────────────── portadas HTML ───────────────────────────
CARD_SELS = ["article", "[class*=card]", "[class*=story]", "[class*=nota]", "[class*=item]", "[class*=news]"]
TITLE_SELS = ["h1", "h2", "h3", "h4", "[class*=title]", "[class*=headline]", "[class*=titular]"]
_NO_NOTA = ["/autor/", "/author/", "/autores/", "tag=", "/tag/", "/tags/", "/tema/", "/temas/", "/columnistas/",
            "/seccion/", "/secciones/", "/categoria/", "/category/", "/newsletters", "/suscrip", "/login",
            "mailto:", "whatsapp:", "/videos/?$", "/podcasts/?$"]


def _parece_nota(url, base):
    """Descarta links a secciones, autores y etiquetas: una nota tiene un camino largo."""
    if not url or not url.startswith("http"):
        return False
    ul = url.lower()
    if any(re.search(p, ul) for p in _NO_NOTA):
        return False
    path = re.sub(r"^https?://[^/]+", "", url).split("?")[0].strip("/")
    return len(path) >= 22 and ("-" in path or re.search(r"\d{4,}", path) is not None)


def extraer_html(html, fuente, limite):
    soup = BeautifulSoup(html, "html.parser")
    bm = re.match(r"https?://[^/]+", fuente["url"])
    base = bm.group(0) if bm else ""

    def resolve(href):
        if not href or href.startswith("javascript") or href == "#":
            return None
        if href.startswith("//"):
            return "https:" + href
        if href.startswith("/"):
            return base.rstrip("/") + href
        if href.startswith("http"):
            return href
        return None

    def mejor_link(card, tel):
        cands = []
        if tel.name == "a":
            cands.append(tel)
        p = tel.find_parent("a")
        if p:
            cands.append(p)
        cands += tel.find_all("a")
        if card.name == "a":
            cands.append(card)
        cands += card.find_all("a")
        urls = []
        for a in cands:
            u = resolve(a.get("href", "").strip())
            if u and _parece_nota(u, base) and u not in urls:
                urls.append(u)
        return urls[0] if urls else None

    noticias, vistos, urls_vistas = [], set(), set()
    for sel in CARD_SELS:
        for card in soup.select(sel)[:limite * 4]:
            if len(noticias) >= limite:
                break
            tel = None
            for ts in TITLE_SELS:
                tel = card.select_one(ts)
                if tel:
                    break
            if not tel:
                continue
            t = " ".join(tel.get_text(" ", strip=True).split())
            if len(t) < 25 or len(t) > 300 or t in vistos:
                continue
            url = mejor_link(card, tel)
            if not url or url in urls_vistas:
                continue
            vistos.add(t)
            urls_vistas.add(url)
            noticias.append({"titulo": t, "url": url, "imagen": get_imagen(card), "fecha": None, "bajada": ""})
        if len(noticias) >= limite:
            break
    if len(noticias) < limite:
        # Completa con todos los links a notas del mismo sitio, en el orden en que aparecen en la portada
        dominio = _dominio(base)
        for a in soup.find_all("a", href=True):
            if len(noticias) >= limite:
                break
            u = resolve(a.get("href", "").strip())
            if not u or u in urls_vistas or _dominio(u) != dominio or not _parece_nota(u, base):
                continue
            t = ""
            for h in a.find_all(["h1", "h2", "h3", "h4"]):
                t = " ".join(h.get_text(" ", strip=True).split())
                if len(t) >= 25:
                    break
            if len(t) < 25:
                t = " ".join(a.get_text(" ", strip=True).split()) or " ".join((a.get("title") or "").split())
            if not (25 <= len(t) <= 300) or t in vistos:
                continue
            vistos.add(t)
            urls_vistas.add(u)
            noticias.append({"titulo": t, "url": u, "imagen": get_imagen(a), "fecha": None, "bajada": ""})
    if len(noticias) < 6:
        for el in soup.select("h2 a[href], h3 a[href], a h2, a h3"):
            if len(noticias) >= limite:
                break
            a = el if el.name == "a" else el.find_parent("a")
            t = " ".join(el.get_text(" ", strip=True).split())
            u = resolve(a.get("href", "")) if a else None
            if u and _parece_nota(u, base) and 25 <= len(t) <= 300 and t not in vistos and u not in urls_vistas:
                vistos.add(t)
                urls_vistas.add(u)
                noticias.append({"titulo": t, "url": u, "imagen": "", "fecha": None, "bajada": ""})
    return noticias[:limite]


# ─────────────────────────── filtro de inteligencia artificial ───────────────────────────
_IA_RE = re.compile(
    r"\b(IA|AI|A\.I\.|inteligencia artificial|artificial intelligence|machine learning|aprendizaje autom[aá]tico|"
    r"deep learning|LLMs?|chatbots?|ChatGPT|GPT-?\d|OpenAI|Anthropic|Claude|Gemini|DeepMind|Copilot|Grok|xAI|"
    r"DeepSeek|Mistral|Llama|Nvidia|neural|generative|generativa|superinteligencia|AGI|Sam Altman|Hugging Face|"
    r"modelos? de lenguaje|agentes? de IA|AI agents?)\b", re.IGNORECASE)


def es_de_ia(n):
    return bool(_IA_RE.search(n["titulo"] + " " + (n.get("bajada") or "")))


# ─────────────────────────── lectura de una fuente ───────────────────────────
def _get(url, timeout=12):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    if "charset=" not in r.headers.get("content-type", "").lower():
        sniff = r.content[:4096].decode("ascii", errors="ignore").lower()
        r.encoding = "utf-8" if "utf-8" in sniff else (r.apparent_encoding or "utf-8")
    return r


def _dominio(url):
    m = re.search(r"https?://(?:www\.)?([^/]+)", url or "")
    return m.group(1) if m else ""


_GNEWS_LOC = {"es": "hl=es-419&gl=AR&ceid=AR:es-419", "en": "hl=en-US&gl=US&ceid=US:en",
              "fr": "hl=fr&gl=FR&ceid=FR:fr", "it": "hl=it&gl=IT&ceid=IT:it",
              "de": "hl=de&gl=DE&ceid=DE:de", "pt": "hl=pt-BR&gl=BR&ceid=BR:pt-419"}


def _gnews(q, lang):
    return f"https://news.google.com/rss/search?q={q}&{_GNEWS_LOC.get(lang, _GNEWS_LOC['es'])}"


def _leer_rss(url, limite):
    r = _get(url)
    notas = extraer_rss(r.text, limite)
    if "news.google.com" in url:
        for n in notas:
            n["titulo"] = _limpiar_titulo_gnews(n["titulo"])
    return notas


def _leer_varios_rss(f, cant):
    """Feed principal + feeds extra del mismo medio, sin repetir."""
    principal = _leer_rss(f["url"], cant)
    extras = f.get("rss_extra") or []
    if not extras:
        return principal
    resto = []
    with ThreadPoolExecutor(max_workers=min(8, len(extras))) as ex:
        for fut in as_completed([ex.submit(_leer_rss, u, cant) for u in extras]):
            try:
                resto += fut.result()
            except Exception:
                pass
    vistos = {n.get("url") for n in principal} | {n["titulo"].lower() for n in principal}
    unicos = []
    for n in resto:
        if n.get("url") in vistos or n["titulo"].lower() in vistos:
            continue
        vistos.add(n.get("url"))
        vistos.add(n["titulo"].lower())
        unicos.append(n)
    unicos.sort(key=lambda n: n.get("fecha") or "", reverse=True)
    return principal + unicos


# ─────────────────────────── Olé (lectores del Monitor deportivo) ───────────────────────────
_OLE = "https://www.ole.com.ar"
_OLE_SKIP = ["/autor/", "/autores/", "/firma/", "/columnistas/", "/tag/", "/tags/", "/categoria/", "/seccion/",
             "/author/", "tag=", "/tema/", "mailto:", "javascript:", "#"]


def _ole_url(href):
    if not href or any(s in href for s in _OLE_SKIP):
        return None
    if href.startswith("//"):
        href = "https:" + href
    elif href.startswith("/"):
        href = _OLE + href
    if not href.startswith("http"):
        return None
    return href


def _ole_es_nota(u):
    return bool(u) and "ole.com.ar" in u and (u.split("?")[0].endswith(".html") or _parece_nota(u, _OLE))


def extraer_ole_home(html, limite):
    """Portada de Olé en el orden en que aparece (el puesto 0 es la nota principal).
    Busca el link de cada título escalando por el HTML y prioriza los que terminan en .html."""
    soup = BeautifulSoup(html, "html.parser")
    notas, vistos, urls = [], set(), set()

    def mejor_link(tel, card):
        cands = []
        p = tel.find_parent("a")
        if p:
            cands.append(p.get("href", ""))
        hijo = tel.find("a")
        if hijo:
            cands.append(hijo.get("href", ""))
        cands += [a.get("href", "") for a in card.find_all("a", href=True)]
        padre = card.parent
        for _ in range(4):
            if not padre or padre.name in ("body", "html", "[document]"):
                break
            if padre.name == "a":
                cands.append(padre.get("href", ""))
            padre = padre.parent
        cands = [u for u in (_ole_url(c) for c in cands) if _ole_es_nota(u)]
        html_ = [u for u in cands if u.split("?")[0].endswith(".html")]
        return (html_ or cands or [None])[0]

    tarjetas = soup.select("article, [class*=card], [class*=nota], [class*=story], [class*=article], [class*=item]")
    for card in tarjetas:
        if len(notas) >= limite:
            break
        tel = None
        for ts in ("h1", "h2", "h3", "h4", "[class*=title]", "[class*=titular]", "[class*=headline]"):
            tel = card.select_one(ts)
            if tel:
                break
        if not tel:
            continue
        t = " ".join(tel.get_text(" ", strip=True).split())
        if len(t) < 20 or len(t) > 300 or t in vistos:
            continue
        u = mejor_link(tel, card)
        if not u or u in urls:
            continue
        vistos.add(t)
        urls.add(u)
        notas.append({"titulo": t, "url": u, "imagen": get_imagen(card), "fecha": None, "bajada": ""})
    if len(notas) < 8:
        for el in soup.select("h2 a[href], h3 a[href], a h2, a h3"):
            if len(notas) >= limite:
                break
            a = el if el.name == "a" else el.find_parent("a")
            t = " ".join(el.get_text(" ", strip=True).split())
            u = _ole_url(a.get("href", "")) if a else None
            if _ole_es_nota(u) and 20 <= len(t) <= 300 and t not in vistos and u not in urls:
                vistos.add(t)
                urls.add(u)
                notas.append({"titulo": t, "url": u, "imagen": "", "fecha": None, "bajada": ""})
    return notas[:limite]


def _titulo_de_link(a, u):
    """El título de una nota a partir de uno de sus links, con una nota de calidad:
    3 = título dentro del link, 2 = texto o atributos del link, 1 = título cercano, 0 = nada.
    El título cercano solo se usa si el bloque es de esta nota (todos sus links van a la misma nota)."""
    for h in a.find_all(["h1", "h2", "h3", "h4"]):
        t = " ".join(h.get_text(" ", strip=True).split())
        if 20 <= len(t) <= 300:
            return t, 3
    t = " ".join(a.get_text(" ", strip=True).split())
    if 20 <= len(t) <= 300:
        return t, 2
    for attr in ("title", "aria-label"):
        t = " ".join((a.get(attr) or "").split())
        if 20 <= len(t) <= 300:
            return t, 2
    p = a.parent
    for _ in range(2):
        if not p or p.name in ("body", "html", "[document]"):
            break
        destinos = {(_ole_url(x.get("href", "")) or "").split("?")[0] for x in p.find_all("a", href=True)}
        destinos = {d for d in destinos if d.endswith(".html")}
        if destinos and destinos != {u}:
            break                                   # el bloque tiene otras notas: su título no es de esta
        for h in p.find_all(["h1", "h2", "h3", "h4", "[class*=title]"]):
            t = " ".join(h.get_text(" ", strip=True).split())
            if 20 <= len(t) <= 300:
                return t, 1
        p = p.parent
    return "", 0


def _titulo_de_slug(u):
    slug = u.split("?")[0].rstrip("/").split("/")[-1].replace(".html", "")
    slug = re.sub(r"_0_[A-Za-z0-9]+$", "", slug)
    slug = re.sub(r"^\d+-|-\d+$", "", slug)
    return slug.replace("-", " ").strip().capitalize()


def extraer_ole_links(html, limite):
    """Portada de Olé sin depender de su diseño: todos los links a notas (.html) en el orden en que aparecen.
    Si una nota tiene varios links (foto y título), se queda con el primer lugar y el mejor título."""
    soup = BeautifulSoup(html, "html.parser")
    orden, titulos, imagenes, calidad = [], {}, {}, {}
    for a in soup.find_all("a", href=True):
        u = _ole_url(a["href"])
        if not u or "ole.com.ar" not in u:
            continue
        u = u.split("?")[0].split("#")[0]
        if not u.endswith(".html") or u.count("/") < 4:
            continue
        if u not in titulos:
            orden.append(u)
            titulos[u], imagenes[u], calidad[u] = "", "", 0
        if calidad[u] < 3:
            t, c = _titulo_de_link(a, u)
            if c > calidad[u]:
                titulos[u], calidad[u] = t, c
        if not imagenes[u]:
            imagenes[u] = get_imagen(a)
    # Datos estructurados (JSON-LD): a veces la portada lista ahí las notas con su título
    for sc in soup.find_all("script", type="application/ld+json"):
        for m in re.finditer(r'"(?:url|@id)"\s*:\s*"(https?://www\.ole\.com\.ar/[^"]+?\.html)"[^{}]*?"(?:headline|name)"\s*:\s*"([^"]{20,300})"',
                             sc.string or ""):
            u, t = m.group(1), m.group(2)
            if u not in titulos:
                orden.append(u)
                titulos[u], imagenes[u], calidad[u] = t, "", 2
            elif calidad[u] < 2:
                titulos[u], calidad[u] = t, 2
    notas = []
    for u in orden:
        t = titulos[u] or _titulo_de_slug(u)
        if len(t) < 16:
            continue
        notas.append({"titulo": t, "url": u, "imagen": imagenes.get(u, ""), "fecha": None, "bajada": "",
                      "_calidad": calidad.get(u, 0)})
        if len(notas) >= limite:
            break
    return notas


def extraer_ole(html, limite):
    """Combina los dos métodos: el de tarjetas (el del Monitor deportivo) y el de links.
    Usa el orden del que encuentre más notas y suma las que encuentre solo el otro."""
    por_tarjetas = extraer_ole_home(html, limite)
    por_links = extraer_ole_links(html, limite)
    base, otro = (por_links, por_tarjetas) if len(por_links) > len(por_tarjetas) else (por_tarjetas, por_links)
    titulo_por_url = {n["url"]: n["titulo"] for n in por_tarjetas}
    vistas = {n["url"] for n in base}
    for n in base:                                   # si el link no tenía un buen título, se usa el de la tarjeta
        if n.get("_calidad", 3) < 2 and n["url"] in titulo_por_url:
            n["titulo"] = titulo_por_url[n["url"]]
    base += [n for n in otro if n["url"] not in vistas]
    for n in base:
        n.pop("_calidad", None)
    return base[:limite]


def extraer_ole_ultimas(html, limite):
    """https://www.ole.com.ar/ultimas-noticias: todo lo publicado, también lo que nunca pisa la portada.
    Usa el atributo data-noteid de cada nota (estable) y, si no está, las clases del listado."""
    soup = BeautifulSoup(html, "html.parser")
    conts = soup.select("div[data-noteid]") or soup.select("li[class*='listado'], [class*='listado'] article")
    notas, urls = [], set()
    for c in conts:
        if len(notas) >= limite:
            break
        a = c.find("a", href=True)
        u = _ole_url(a["href"]) if a else None
        if not u or u in urls:
            continue
        tel = c.find(["h1", "h2", "h3", "h4"])
        t = " ".join((tel.get_text(" ", strip=True) if tel else a.get_text(" ", strip=True)).split())
        if len(t) < 16:   # último recurso: el título sale del link
            t = re.sub(r"^\d+-", "", u.rstrip("/").split("/")[-1].replace(".html", "")).replace("-", " ").capitalize()
            if len(t) < 16:
                continue
        bajada = c.find("p")
        urls.add(u)
        notas.append({"titulo": t[:250], "url": u, "imagen": get_imagen(c), "fecha": None,
                      "bajada": bajada.get_text(" ", strip=True)[:280] if bajada else ""})
    return notas


def _leer_directo(f, limite):
    if f.get("tipo") == "ole_home":
        return extraer_ole(_get(f["url"]).text, limite)
    if f.get("tipo") == "ole_ultimas":
        notas = []
        try:
            pagina = _get(f["url"]).text
            notas = extraer_ole_ultimas(pagina, limite)
            if len(notas) < 8:
                extra = extraer_ole_links(pagina, limite)
                if len(extra) > len(notas):
                    notas = extra
        except Exception:
            pass
        if len(notas) < 5 and f.get("rss_respaldo"):
            try:
                notas = _leer_rss(f["rss_respaldo"], limite) or notas
            except Exception:
                pass
        return notas
    if f.get("rss"):
        return _leer_varios_rss(f, limite * (3 if f.get("filtro_ia") else 1))
    if f.get("wp"):
        try:
            notas = _leer_rss(f["url"].rstrip("/") + "/feed/", limite)
            if notas:
                return notas
        except Exception:
            pass
    r = _get(f["url"])
    return extraer_html(r.text, f, limite)


def leer_fuente(f, limite=MAX_POR_MEDIO):
    """Lee un medio. Si falla o no trae notas, usa Google News como respaldo."""
    limite = max(limite, f.get("minimo", 0))       # Olé trae más notas que el resto
    t0, via, error, notas = time.time(), "directo", None, []
    try:
        notas = _leer_directo(f, limite)
        if f.get("filtro_ia"):
            notas = [n for n in notas if es_de_ia(n)]
    except Exception as e:
        error = str(e)[:160]
    if not notas:
        q = f.get("q") or (f"site:{quote(_dominio(f['url']))}" if "news.google.com" not in f["url"] else None)
        if q:
            try:
                notas = _leer_rss(_gnews(q, f.get("lang", "es")), limite)
                if notas:
                    via, error = "google", None
            except Exception as e:
                error = error or str(e)[:160]
        if not notas and not error:
            error = "No se encontraron notas"
    elif ((f.get("minimo") and len(notas) < 10) or (limite >= 20 and len(notas) < limite // 2)) \
            and not f.get("filtro_ia") and "news.google.com" not in f["url"]:
        # Si el sitio devolvió pocas notas (por ejemplo, un feed corto), se completa con lo último en Google News
        q = f.get("q") or f"site:{quote(_dominio(f['url']))}"
        try:
            urls = {n.get("url") for n in notas}
            extra = [n for n in _leer_rss(_gnews(q, f.get("lang", "es")), limite) if n.get("url") not in urls]
            for n in extra:
                n["via"] = "google"
            notas += extra
        except Exception:
            pass
    if "news.google.com" in f["url"] and notas:
        via = "google"
    for i, n in enumerate(notas):
        n.update(medio=f["nombre"], medio_id=f["id"], color=f["color"], lang=f.get("lang", "es"),
                 seccion=f.get("seccion", ""), puesto=i, via=n.get("via") or via)
    return {"id": f["id"], "nombre": f["nombre"], "color": f["color"], "lang": f.get("lang", "es"),
            "estado": "ok" if notas else "error", "via": via if notas else None, "error": error,
            "ms": int((time.time() - t0) * 1000), "items": notas[:limite]}


def leer_varias(ids, limite=MAX_POR_MEDIO, leer=None):
    """Lee varias fuentes en paralelo y las devuelve en el orden pedido.
    `leer` permite pasar una versión con caché de leer_fuente."""
    leer = leer or (lambda fid, lim: leer_fuente(FUENTE_POR_ID[fid], lim))
    ids = [i for i in ids if i in FUENTE_POR_ID]
    out = {}
    with ThreadPoolExecutor(max_workers=min(16, max(1, len(ids)))) as ex:
        futs = {ex.submit(leer, i, limite): i for i in ids}
        for fut in as_completed(futs):
            i = futs[fut]
            f = FUENTE_POR_ID[i]
            try:
                out[i] = fut.result()
            except Exception as e:
                out[i] = {"id": i, "nombre": f["nombre"], "color": f["color"], "lang": f.get("lang", "es"),
                          "estado": "error", "via": None, "error": str(e)[:160], "ms": 0, "items": []}
    return [out[i] for i in ids]


# ─────────────────────────── una nota completa ───────────────────────────
_SELS_CUERPO = ["article .article-body", "article .entry-content", "article .article-content", "[class*=article-body]",
                "[class*=article__body]", "[class*=nota-cuerpo]", "[class*=body-nota]", "[class*=entry-content]",
                "[class*=article-content]", "[class*=post-content]", "[class*=story-body]", "[class*=content-body]",
                "[class*=cuerpo]", "[class*=news-body]", "[class*=detail-body]", "[class*=paywall]",
                "article", "[role=main]", "main"]


def parsear_articulo(html, url=""):
    soup = BeautifulSoup(html, "html.parser")
    og_img = ""
    m = soup.find("meta", property="og:image")
    if m and m.get("content", "").startswith("http") and not _generic(m["content"]):
        og_img = m["content"]
    og_t = soup.find("meta", property="og:title")
    h1 = soup.find("h1")
    titulo = (og_t.get("content", "").strip() if og_t else "") or (h1.get_text(strip=True) if h1 else "")
    desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    bajada = desc.get("content", "").strip() if desc else ""
    site = soup.find("meta", property="og:site_name")
    medio = site.get("content", "").strip() if site else _dominio(url)
    for t in soup(["script", "style", "nav", "header", "footer", "aside", "form", "figure", "noscript", "iframe", "button"]):
        t.decompose()
    parrafos = []
    for sel in _SELS_CUERPO:
        el = soup.select_one(sel)
        if el:
            ps = [p.get_text(" ", strip=True) for p in el.find_all("p") if len(p.get_text(strip=True)) > 40]
            if sum(len(p) for p in ps) > 300:
                parrafos = ps
                break
    if not parrafos:
        parrafos = [p.get_text(" ", strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 50][:14]
    return {"titulo": titulo, "bajada": bajada, "parrafos": parrafos[:60], "imagen": og_img, "url": url, "medio": medio}


def leer_articulo(url):
    if "news.google.com" in url:
        raise ValueError("Los enlaces de Google News no se pueden leer completos: se usa el título y la bajada.")
    r = _get(url, timeout=15)
    return parsear_articulo(r.text, url)


# ═══════════════════════ Curaduría: agrupar titulares por historia ═══════════════════════
_STOP = set("""para como pero desde hasta entre sobre ante tras esta este estos estas todo todos todas cada tambien porque cuando
donde quien cual fueron sera tiene tienen nuevo nueva hace dijo contra luego antes despues otra otro sigue este esto eso ahora
mismo seran estan fue son ser tras segun sobre sera puede pueden hacia durante ademas mientras aunque pais gobierno the and
for with from this that will have after over they their what when about into more than been were said says como con los las
del una uno por que dos tres anos hoy ayer manana semana nota video fotos minuto vivo""".split())

RUIDO = re.compile(r"hor[oó]scopo|quiniela|loter[ií]a|quini ?6|telekino|brinco|receta|efem[eé]ride|pron[oó]stico del tiempo|"
                   r"clima (de )?hoy|d[oó]lar (blue )?hoy|cotizaci[oó]n del d[oó]lar|cup[oó]n|descuento|sorteo|patrocinado|"
                   r"publirreportaje|contenido de marca|cyber ?monday|hot ?sale", re.IGNORECASE)


def norm(t):
    t = unicodedata.normalize("NFD", str(t or "")).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"(\d)[.,](\d)", r"\1\2", t)
    t = re.sub(r"(\d)\s*-\s*(\d)", r"\1a\2", t)
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def _palabras(t):
    return {w for w in norm(t).split() if (len(w) > 3 and w not in _STOP) or (len(w) >= 2 and any(ch.isdigit() for ch in w))}


def _parecido(a, b):
    if not a or not b:
        return False
    inter = len(a & b)
    return inter >= 3 or (inter >= 2 and inter / len(a | b) >= 0.3)


def curar(notas, quitar_ruido=True):
    """Agrupa las notas que cuentan la misma historia y ordena las historias por importancia
    (cuántos medios la tienen y si alguno la lleva en tapa). Cada nota necesita titulo, medio y puesto."""
    orden = sorted(range(len(notas)), key=lambda i: (int(notas[i].get("puesto") or 0), i))
    grupos = []
    for i in orden:
        t = str(notas[i].get("titulo_es") or notas[i].get("titulo", ""))   # traducido si lo hay: agrupa mejor
        if not t.strip() or (quitar_ruido and RUIDO.search(t)):
            continue
        w = _palabras(t)
        if not w:
            continue
        g = next((g for g in grupos if any(_parecido(w, x) for x in g["ws"])), None)
        if g is None:
            g = {"ws": [], "ids": [], "medios": [], "secs": Counter(), "rmin": 99}
            grupos.append(g)
        g["ws"].append(w)
        g["ids"].append(i)
        m = notas[i].get("medio", "")
        if m and m not in g["medios"]:
            g["medios"].append(m)
        if notas[i].get("seccion"):
            g["secs"][notas[i]["seccion"]] += 1
        g["rmin"] = min(g["rmin"], int(notas[i].get("puesto") or 0))
    for g in grupos:
        g["score"] = 3 * len(g["medios"]) + max(0, 3 - g["rmin"]) * 2 + (1 if len(g["ids"]) > 1 else 0)
        g["seccion"] = g["secs"].most_common(1)[0][0] if g["secs"] else ""
        g["notas"] = [notas[i] for i in sorted(g["ids"], key=lambda i: int(notas[i].get("puesto") or 0))]
        g["titulo"] = g["notas"][0].get("titulo_es") or g["notas"][0]["titulo"]
    grupos.sort(key=lambda g: -g["score"])
    return grupos


def una_por_medio(notas, maximo=5):
    """Hasta `maximo` notas, una por medio primero."""
    out, medios = [], set()
    for n in notas:
        if n.get("medio") not in medios:
            out.append(n)
            medios.add(n.get("medio"))
    for n in notas:
        if n not in out:
            out.append(n)
    return out[:maximo]


def buscar(notas, consulta):
    """Busca una o varias palabras (separadas por coma) sin importar tildes ni mayúsculas."""
    terminos = [norm(x).strip() for x in (consulta or "").split(",") if norm(x).strip()]
    if not terminos:
        return []
    out = []
    for n in notas:
        txt = " " + norm(n.get("titulo", "") + " " + (n.get("titulo_es") or "") + " " + (n.get("bajada") or "")) + " "
        if any(all(p in txt for p in t.split()) for t in terminos):
            out.append(n)
    return out
