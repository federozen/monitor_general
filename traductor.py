"""
Traducción automática de títulos en otros idiomas, con los motores de IA (gratis primero).

- Solo los títulos (no las bajadas): son pedidos chicos, entran holgados en los planes gratuitos.
- Van de a tandas (40 títulos por pedido; 25 si el primer motor es Groq, que acepta pedidos cortos).
- Cada título se traduce una sola vez: la app guarda las traducciones en una memoria compartida,
  así al actualizar solo se traducen los títulos nuevos.
- Si fallan todos los motores, los títulos quedan en su idioma y se vuelve a intentar a los 10 minutos.

No depende de Streamlit.
"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

import ia_motores

SISTEMA = """Sos un traductor profesional de titulares de noticias. Traducí cada titular al español rioplatense neutro, natural y periodístico, sin agregar ni quitar información.
- Mantené los nombres propios, siglas y marcas como se usan en los medios en español (por ejemplo "Casa Blanca", "OTAN", "ONU").
- Respetá el estilo de titular: breve y directo.
Recibís un array JSON de titulares. Devolvé SOLO un array JSON de strings con la traducción de cada uno, en el mismo orden y con la misma cantidad de elementos. Nada de texto fuera del array."""

TANDA = 40
TANDA_GROQ = 25
MAX_POR_VEZ = 400          # tope de títulos nuevos por recarga, para no gastar de más
REINTENTO_SEG = 600        # si una tanda falla, esos títulos no se vuelven a pedir por 10 minutos
_FALLOS = {}               # título → cuándo falló
PARALELO = 3               # pocos pedidos a la vez: los planes gratuitos limitan los pedidos por minuto


def _parse_array(texto, n):
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (texto or "").strip())
    m = re.search(r"\[.*\]", t, re.DOTALL)
    try:
        arr = json.loads(m.group(0) if m else t)
    except Exception:
        return None
    if not isinstance(arr, list) or len(arr) != n or not all(isinstance(x, str) for x in arr):
        return None
    return [x.strip() for x in arr]


def _traducir_tanda(titulos):
    salida = ia_motores.generar(json.dumps(titulos, ensure_ascii=False), max_tokens=min(4000, 60 * len(titulos) + 200),
                                nivel="rapido", system=SISTEMA)
    arr = _parse_array(salida, len(titulos))
    if arr is None:
        raise ValueError("la respuesta no vino en el formato esperado")
    return dict(zip(titulos, arr))


def traducir_titulos(titulos, memoria):
    """Traduce los títulos que no están en `memoria` (dict original → traducción) y la actualiza.
    Devuelve (cantidad traducida ahora, error o None)."""
    ahora = time.time()
    pendientes = list(dict.fromkeys(t for t in titulos if t and t not in memoria
                                    and ahora - _FALLOS.get(t, 0) > REINTENTO_SEG))[:MAX_POR_VEZ]
    if not pendientes:
        return 0, None
    cad = ia_motores.cadena()
    tam = TANDA_GROQ if cad and cad[0] == "groq" else TANDA
    tandas = [pendientes[i:i + tam] for i in range(0, len(pendientes), tam)]
    hechas, error = 0, None
    with ThreadPoolExecutor(max_workers=PARALELO) as ex:
        for tanda, fut in [(t, ex.submit(_traducir_tanda, t)) for t in tandas]:
            try:
                res = fut.result()
                memoria.update(res)
                hechas += len(res)
            except Exception as e:
                error = str(e)[:300]
                _FALLOS.update(dict.fromkeys(tanda, ahora))
    if len(memoria) > 6000:                    # la memoria no crece sin límite
        for k in list(memoria)[:2000]:
            memoria.pop(k, None)
    return hechas, error


def aplicar(notas, memoria):
    """Pone `titulo_es` en las notas que ya tienen traducción."""
    for n in notas:
        if n.get("lang", "es") != "es" and n["titulo"] in memoria:
            n["titulo_es"] = memoria[n["titulo"]]
