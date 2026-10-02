"""
Fuentes del Monitor General (las mismas de Panorama), organizadas por sección.

Campos:
  id, nombre, url, color  obligatorios
  lang       "es" o "en"
  rss        True si la url es un feed RSS/Atom
  wp         True si es un sitio WordPress (se intenta /feed/ primero)
  q          búsqueda de Google News para usar como respaldo (o como fuente principal si la url es de news.google.com)
  filtro_ia  True para quedarse solo con las notas sobre inteligencia artificial (feeds de tecnología en general)
  rss_extra  otros feeds del mismo medio que se suman a la principal (sin repetir notas), para traer más

Si una fuente falla o no devuelve notas, se pide a Google News: primero con `q` si existe,
si no con `site:dominio`. Así cada medio muestra algo aunque cambie su sitio.
"""

NYT = "https://rss.nytimes.com/services/xml/rss/nyt/"

def gn(q, lang="es"):
    loc = "hl=es-419&gl=AR&ceid=AR:es-419" if lang == "es" else "hl=en-US&gl=US&ceid=US:en"
    return f"https://news.google.com/rss/search?q={q}&{loc}"

SECCIONES = [
    {"id": "argentina", "nombre": "Argentina", "desc": "Los principales medios nacionales.", "fuentes": [
        {"id": "clarin",     "nombre": "Clarín",        "url": "https://www.clarin.com/",           "color": "#d7261e"},
        {"id": "lanacion",   "nombre": "La Nación",     "url": "https://www.lanacion.com.ar/",      "color": "#1e5aa8"},
        {"id": "infobae",    "nombre": "Infobae",       "url": "https://www.infobae.com/",          "color": "#e2701f"},
        {"id": "pagina12",   "nombre": "Página/12",     "url": "https://www.pagina12.com.ar/",      "color": "#1d1d1b"},
        {"id": "perfil",     "nombre": "Perfil",        "url": "https://www.perfil.com/",           "color": "#c8102e"},
        {"id": "tn",         "nombre": "TN",            "url": "https://tn.com.ar/",                "color": "#0a58ca"},
        {"id": "eldiarioar", "nombre": "elDiarioAR",    "url": "https://www.eldiarioar.com/",       "color": "#00a19a"},
        {"id": "lpo",        "nombre": "La Política Online", "url": "https://www.lapoliticaonline.com/", "color": "#b71c1c"},
        {"id": "eldestape",  "nombre": "El Destape",    "url": "https://www.eldestapeweb.com/",     "color": "#e53935"},
        {"id": "minutouno",  "nombre": "Minuto Uno",    "url": "https://www.minutouno.com/",        "color": "#e30613"},
        {"id": "c5n",        "nombre": "C5N",           "url": "https://www.c5n.com/",              "color": "#d50000"},
        {"id": "cronica",    "nombre": "Crónica",       "url": "https://www.cronica.com.ar/",       "color": "#f4b400"},
        {"id": "chequeado",  "nombre": "Chequeado",     "url": "https://chequeado.com/",            "color": "#2b8a3e", "wp": True},
        {"id": "na",         "nombre": "Noticias Argentinas", "url": gn("site:noticiasargentinas.com"), "color": "#2c3e50", "rss": True},
    ]},
    {"id": "economia", "nombre": "Economía", "desc": "Economía, finanzas y negocios.", "fuentes": [
        {"id": "ambito",     "nombre": "Ámbito",        "url": "https://www.ambito.com/",           "color": "#00594e"},
        {"id": "cronista",   "nombre": "El Cronista",   "url": "https://www.cronista.com/",         "color": "#0b3d91"},
        {"id": "iprofesional","nombre": "iProfesional", "url": "https://www.iprofesional.com/",     "color": "#1565c0"},
        {"id": "infobae_eco","nombre": "Infobae Economía","url": "https://www.infobae.com/economia/", "color": "#e2701f"},
        {"id": "lanacion_eco","nombre": "La Nación Economía","url": "https://www.lanacion.com.ar/economia/", "color": "#1e5aa8"},
        {"id": "clarin_eco", "nombre": "Clarín Economía","url": "https://www.clarin.com/economia/", "color": "#d7261e"},
        {"id": "bloomberg",  "nombre": "Bloomberg Línea","url": "https://www.bloomberglinea.com/latinoamerica/argentina/", "color": "#5b2c8e"},
        {"id": "forbes",     "nombre": "Forbes Argentina","url": "https://www.forbesargentina.com/", "color": "#111111"},
        {"id": "eleconomista","nombre": "El Economista","url": "https://eleconomista.com.ar/",     "color": "#1f4e79"},
    ]},
    {"id": "mundo", "nombre": "Mundo", "desc": "Noticias internacionales en español y de agencias.", "fuentes": [
        {"id": "elpais",     "nombre": "El País",       "url": "https://elpais.com/internacional/", "color": "#1a1a1a"},
        {"id": "bbcmundo",   "nombre": "BBC Mundo",     "url": "https://feeds.bbci.co.uk/mundo/rss.xml", "color": "#b80000", "rss": True},
        {"id": "cnnesp",     "nombre": "CNN en Español","url": "https://cnnespanol.cnn.com/",       "color": "#cc0000", "wp": True},
        {"id": "dw",         "nombre": "DW Español",    "url": "https://rss.dw.com/rdf/rss-sp-all", "color": "#05b2fc", "rss": True},
        {"id": "france24",   "nombre": "France 24",     "url": "https://www.france24.com/es/rss",   "color": "#0f3b8c", "rss": True},
        {"id": "infobae_am", "nombre": "Infobae América","url": "https://www.infobae.com/america/", "color": "#e2701f"},
        {"id": "elmundo",    "nombre": "El Mundo (ES)", "url": "https://www.elmundo.es/internacional.html", "color": "#0a3d62"},
        {"id": "efe",        "nombre": "EFE",           "url": gn("site:efe.com"), "color": "#0055a5", "rss": True},
        {"id": "nytimes",    "nombre": "The New York Times", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "color": "#111111", "rss": True, "lang": "en",
         "rss_extra": [NYT + s + ".xml" for s in ("Americas", "Europe", "AsiaPacific", "MiddleEast", "Africa")]},
        {"id": "guardian",   "nombre": "The Guardian",  "url": "https://www.theguardian.com/world/rss", "color": "#052962", "rss": True, "lang": "en"},
        {"id": "reuters",    "nombre": "Reuters",       "url": gn("site:reuters.com%20world", "en"), "color": "#ff8000", "rss": True, "lang": "en"},
        {"id": "ap",         "nombre": "AP News",       "url": gn("site:apnews.com", "en"), "color": "#e4002b", "rss": True, "lang": "en"},
    ]},
    {"id": "exterior", "nombre": "Exterior", "desc": "Las portadas de los principales diarios del mundo, en su idioma.", "fuentes": [
        # Estados Unidos
        {"id": "ext_nyt",      "nombre": "The New York Times", "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "color": "#111111", "rss": True, "lang": "en", "pais": "EE.UU.", "q": "site:nytimes.com",
         "rss_extra": [NYT + s + ".xml" for s in ("World", "US", "Politics", "Business", "Technology", "Science", "Health", "Sports", "Arts", "Opinion", "Americas")]},
        {"id": "ext_wapo",     "nombre": "The Washington Post", "url": "https://www.washingtonpost.com/", "color": "#1a1a1a", "lang": "en", "pais": "EE.UU."},
        {"id": "ext_wsj",      "nombre": "The Wall Street Journal", "url": "https://www.wsj.com/", "color": "#0274b6", "lang": "en", "pais": "EE.UU."},
        {"id": "ext_cnn",      "nombre": "CNN",                "url": "https://edition.cnn.com/", "color": "#cc0000", "lang": "en", "pais": "EE.UU."},
        # Reino Unido
        {"id": "ext_bbc",      "nombre": "BBC News",           "url": "https://feeds.bbci.co.uk/news/rss.xml", "color": "#b80000", "rss": True, "lang": "en", "pais": "Reino Unido", "q": "site:bbc.com/news"},
        {"id": "ext_guardian", "nombre": "The Guardian",       "url": "https://www.theguardian.com/international/rss", "color": "#052962", "rss": True, "lang": "en", "pais": "Reino Unido", "q": "site:theguardian.com"},
        {"id": "ext_ft",       "nombre": "Financial Times",    "url": "https://www.ft.com/", "color": "#f2a7a0", "lang": "en", "pais": "Reino Unido"},
        {"id": "ext_economist","nombre": "The Economist",      "url": "https://www.economist.com/", "color": "#e3120b", "lang": "en", "pais": "Reino Unido", "q": "site:economist.com"},
        # Agencias y Medio Oriente
        {"id": "ext_reuters",  "nombre": "Reuters",            "url": gn("site:reuters.com", "en"), "color": "#ff8000", "rss": True, "lang": "en", "pais": "Agencia"},
        {"id": "ext_aljazeera","nombre": "Al Jazeera",         "url": "https://www.aljazeera.com/xml/rss/all.xml", "color": "#c69c3f", "rss": True, "lang": "en", "pais": "Qatar", "q": "site:aljazeera.com"},
        # Europa
        {"id": "ext_elpais",   "nombre": "El País",            "url": "https://elpais.com/", "color": "#1a1a1a", "lang": "es", "pais": "España", "q": "site:elpais.com"},
        {"id": "ext_elmundo",  "nombre": "El Mundo",           "url": "https://www.elmundo.es/", "color": "#0a3d62", "lang": "es", "pais": "España"},
        {"id": "ext_lemonde",  "nombre": "Le Monde",           "url": "https://www.lemonde.fr/rss/une.xml", "color": "#111111", "rss": True, "lang": "fr", "pais": "Francia", "q": "site:lemonde.fr"},
        {"id": "ext_figaro",   "nombre": "Le Figaro",          "url": "https://www.lefigaro.fr/", "color": "#163860", "lang": "fr", "pais": "Francia"},
        {"id": "ext_corriere", "nombre": "Corriere della Sera","url": "https://www.corriere.it/", "color": "#9b1c1c", "lang": "it", "pais": "Italia"},
        {"id": "ext_repubblica","nombre": "la Repubblica",     "url": "https://www.repubblica.it/", "color": "#0e2b5c", "lang": "it", "pais": "Italia"},
        {"id": "ext_spiegel",  "nombre": "Der Spiegel",        "url": "https://www.spiegel.de/schlagzeilen/index.rss", "color": "#e64415", "rss": True, "lang": "de", "pais": "Alemania", "q": "site:spiegel.de"},
        # América Latina
        {"id": "ext_folha",    "nombre": "Folha de S.Paulo",   "url": "https://www.folha.uol.com.br/", "color": "#1e3a8a", "lang": "pt", "pais": "Brasil"},
        {"id": "ext_oglobo",   "nombre": "O Globo",            "url": "https://oglobo.globo.com/", "color": "#0d47a1", "lang": "pt", "pais": "Brasil"},
        {"id": "ext_eluniversal","nombre": "El Universal",     "url": "https://www.eluniversal.com.mx/", "color": "#1c2a48", "lang": "es", "pais": "México"},
        {"id": "ext_latercera","nombre": "La Tercera",         "url": "https://www.latercera.com/", "color": "#c8102e", "lang": "es", "pais": "Chile"},
        {"id": "ext_eltiempo", "nombre": "El Tiempo",          "url": "https://www.eltiempo.com/", "color": "#1e3a6d", "lang": "es", "pais": "Colombia"},
        {"id": "ext_observador","nombre": "El Observador",     "url": "https://www.elobservador.com.uy/", "color": "#004b87", "lang": "es", "pais": "Uruguay"},
    ]},
    {"id": "provincias", "nombre": "Provincias", "desc": "Diarios de las provincias.", "fuentes": [
        {"id": "lavoz",      "nombre": "La Voz (Córdoba)",   "url": "https://www.lavoz.com.ar/",       "color": "#0070b8"},
        {"id": "lacapital",  "nombre": "La Capital (Rosario)","url": "https://www.lacapital.com.ar/",  "color": "#6a0d8a"},
        {"id": "losandes",   "nombre": "Los Andes (Mendoza)","url": "https://www.losandes.com.ar/",    "color": "#0a3d7a"},
        {"id": "eldia",      "nombre": "El Día (La Plata)",  "url": "https://www.eldia.com/",          "color": "#004a8f"},
        {"id": "lagaceta",   "nombre": "La Gaceta (Tucumán)","url": "https://www.lagaceta.com.ar/",    "color": "#1f3d7a"},
        {"id": "rionegro",   "nombre": "Río Negro",          "url": "https://www.rionegro.com.ar/",    "color": "#00796b"},
        {"id": "ellitoral",  "nombre": "El Litoral (Santa Fe)","url": "https://www.ellitoral.com/",    "color": "#0066b3"},
        {"id": "diariouno",  "nombre": "Diario Uno (Mendoza)","url": "https://www.diariouno.com.ar/",  "color": "#e2001a"},
        {"id": "rosario3",   "nombre": "Rosario3",           "url": "https://www.rosario3.com/",       "color": "#f39200"},
        {"id": "eltribuno",  "nombre": "El Tribuno (Salta)", "url": "https://www.eltribuno.com/salta", "color": "#1b5e20"},
        {"id": "lanueva",    "nombre": "La Nueva (Bahía Blanca)","url": "https://www.lanueva.com/",    "color": "#283593"},
        {"id": "misiones",   "nombre": "Misiones Online",    "url": "https://misionesonline.net/",     "color": "#2e7d32", "wp": True},
    ]},
    {"id": "deportes", "nombre": "Deportes", "desc": "Las portadas deportivas de los principales medios argentinos.", "fuentes": [
        {"id": "dep_ole",       "nombre": "Olé",                "url": "https://www.ole.com.ar/",                 "color": "#00a846"},
        {"id": "dep_ole_ult",   "nombre": "Olé · Últimas",      "url": "https://www.ole.com.ar/rss/ultimas-noticias/", "color": "#00a846", "rss": True, "q": "site:ole.com.ar"},
        {"id": "dep_tyc",       "nombre": "TyC Sports",         "url": gn("site:tycsports.com"),                  "color": "#1565c0", "rss": True},
        {"id": "dep_espn",      "nombre": "ESPN",               "url": gn("site:espn.com.ar"),                    "color": "#cc0000", "rss": True},
        {"id": "dep_infobae",   "nombre": "Infobae Deportes",   "url": "https://www.infobae.com/deportes/",       "color": "#e2701f"},
        {"id": "dep_lanacion",  "nombre": "La Nación Deportes", "url": gn("site:lanacion.com.ar/deportes"),       "color": "#1e5aa8", "rss": True},
        {"id": "dep_clarin",    "nombre": "Clarín Deportes",    "url": "https://www.clarin.com/deportes/",        "color": "#d7261e"},
        {"id": "dep_tn",        "nombre": "TN Deportes",        "url": "https://tn.com.ar/deportes/",             "color": "#0a58ca"},
        {"id": "dep_tnt",       "nombre": "TNT Sports",         "url": "https://www.tntsports.com.ar/",           "color": "#e4002b"},
        {"id": "dep_pagina12",  "nombre": "Página/12 · Líbero", "url": "https://www.pagina12.com.ar/secciones/deportes", "color": "#1d1d1b"},
        {"id": "dep_elgrafico", "nombre": "El Gráfico",         "url": "https://www.elgrafico.com.ar/",           "color": "#b07800"},
        {"id": "dep_mundod",    "nombre": "Mundo D (Córdoba)",  "url": "https://mundod.lavoz.com.ar/",            "color": "#00843d"},
    ]},
    {"id": "ia", "nombre": "Inteligencia artificial", "corto": "IA", "desc": "Noticias de IA de todo el mundo, en español e inglés.", "fuentes": [
        # En español
        {"id": "futuria",    "nombre": "Futuria · La Nación", "url": gn("site:lanacion.com.ar%20(Futuria%20OR%20%22inteligencia%20artificial%22)"), "color": "#1e5aa8", "rss": True},
        {"id": "elpais_ia",  "nombre": "El País · IA",   "url": "https://elpais.com/noticias/inteligencia-artificial/", "color": "#1a1a1a", "q": "site:elpais.com%20%22inteligencia%20artificial%22"},
        {"id": "infobae_ia", "nombre": "Infobae · IA",   "url": gn("site:infobae.com%20%22inteligencia%20artificial%22"), "color": "#e2701f", "rss": True},
        {"id": "clarin_ia",  "nombre": "Clarín · IA",    "url": gn("site:clarin.com%20%22inteligencia%20artificial%22"), "color": "#d7261e", "rss": True},
        {"id": "bbc_ia",     "nombre": "BBC Mundo · IA", "url": gn("site:bbc.com/mundo%20%22inteligencia%20artificial%22"), "color": "#b80000", "rss": True},
        {"id": "xataka",     "nombre": "Xataka",         "url": "https://www.xataka.com/tag/inteligencia-artificial", "color": "#e2231a", "q": "site:xataka.com%20%22inteligencia%20artificial%22"},
        {"id": "hipertextual","nombre": "Hipertextual",  "url": gn("site:hipertextual.com%20%22inteligencia%20artificial%22"), "color": "#ff3b30", "rss": True},
        {"id": "ia_es",      "nombre": "IA en español",  "url": gn("%22inteligencia%20artificial%22"), "color": "#6d48a8", "rss": True},
        # In English
        {"id": "nyt_ia",     "nombre": "The New York Times", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", "color": "#111111", "rss": True, "lang": "en", "filtro_ia": True, "q": "site:nytimes.com%20%22artificial%20intelligence%22",
         "rss_extra": [NYT + s + ".xml" for s in ("Business", "Science", "Opinion", "US", "World", "HomePage")]},
        {"id": "guardian_ia","nombre": "The Guardian · AI", "url": "https://www.theguardian.com/technology/artificialintelligenceai/rss", "color": "#052962", "rss": True, "lang": "en"},
        {"id": "verge_ia",   "nombre": "The Verge · AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "color": "#5200ff", "rss": True, "lang": "en"},
        {"id": "techcrunch", "nombre": "TechCrunch · AI","url": "https://techcrunch.com/category/artificial-intelligence/feed/", "color": "#0a9e01", "rss": True, "lang": "en"},
        {"id": "mittr",      "nombre": "MIT Technology Review", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "color": "#e6001f", "rss": True, "lang": "en"},
        {"id": "wired_ia",   "nombre": "Wired · AI",     "url": "https://www.wired.com/feed/tag/ai/latest/rss", "color": "#000000", "rss": True, "lang": "en"},
        {"id": "venturebeat","nombre": "VentureBeat · AI","url": "https://venturebeat.com/category/ai/feed/", "color": "#c8102e", "rss": True, "lang": "en"},
        {"id": "ars_ia",     "nombre": "Ars Technica · AI","url": "https://arstechnica.com/ai/feed/", "color": "#ff4e00", "rss": True, "lang": "en", "q": "site:arstechnica.com%20AI"},
        {"id": "reuters_ia", "nombre": "Reuters · AI",   "url": gn("site:reuters.com%20%22artificial%20intelligence%22", "en"), "color": "#ff8000", "rss": True, "lang": "en"},
        # Laboratorios y empresas
        {"id": "openai",     "nombre": "OpenAI",         "url": "https://openai.com/news/rss.xml", "color": "#10a37f", "rss": True, "lang": "en", "q": "OpenAI"},
        {"id": "googleai",   "nombre": "Google AI",      "url": "https://blog.google/technology/ai/rss/", "color": "#4285f4", "rss": True, "lang": "en", "q": "%22Google%20AI%22%20OR%20Gemini"},
        {"id": "anthropic",  "nombre": "Anthropic",      "url": gn("Anthropic%20Claude", "en"), "color": "#d97757", "rss": True, "lang": "en"},
        {"id": "huggingface","nombre": "Hugging Face",   "url": "https://huggingface.co/blog/feed.xml", "color": "#ffb000", "rss": True, "lang": "en", "q": "%22Hugging%20Face%22"},
    ]},
]

FUENTE_POR_ID = {}
for _s in SECCIONES:
    for _f in _s["fuentes"]:
        _f.setdefault("lang", "es")
        _f["seccion"] = _s["id"]
        FUENTE_POR_ID[_f["id"]] = _f
