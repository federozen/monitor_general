# 📡 Monitor General

Las noticias de los medios de **Panorama** (Argentina, Economía, Mundo, Exterior, Provincias, Deportes e IA) en una app de **Streamlit**, con **plantillas de IA** para entender una nota, resumirla, chequearla, profundizar un tema en todos los medios o armar el resumen del día.

Usa los **mismos motores de IA** del Monitor: Gemini, Mistral, Groq y OpenRouter (gratis) primero, y Claude (pago) de respaldo. Y si no tenés ninguna clave, cada plantilla arma el **pedido listo para pegar** en ChatGPT, Claude o Gemini.

## Las vistas

| Vista | Qué hace |
|---|---|
| **📰 Noticias** | Los medios de la sección elegida. Tres formas de ver: **Por medio**, **Intercalado** (la 1ª nota de cada medio, después la 2ª…) y **Por tema** (titulares agrupados por historia, ordenados por cuántos medios la tienen y si va en tapa; sin IA). Buscador que no distingue tildes ni mayúsculas. En cada nota: 🧠 para analizarla y ➕ para sumarla a un tema. |
| **🧠 Analizar nota** | Una nota elegida, un link cualquiera o un texto pegado. Se lee completa y se elige una plantilla. Abajo, **💬 Preguntale a la nota**. |
| **🗂️ Tema** | Varias notas de distintos medios sobre una misma historia (buscadas por palabra en la sección o en todas, o juntadas con ➕). Lee completas hasta 8 (una por medio primero) y las analiza juntas. |
| **🗞️ Resumen del día** | Elegís las secciones; la app agrupa y ordena las historias (como Panorama) y la IA arma el resumen. |
| **🕘 Historial** | Todo lo que generó la IA en la sesión, para descargar en un solo .md. |

## Títulos traducidos

Con **🌐 Traducir títulos de otros idiomas** (en la barra lateral, viene prendido), las notas en inglés, francés, italiano, alemán o portugués aparecen con el título en español y el original debajo, en itálica. Usa el modelo rápido de los motores gratuitos:

- Solo traduce títulos, de a tandas de 40 (25 con Groq): una sección como Exterior son unos 6 a 8 pedidos chicos.
- Cada título se traduce **una sola vez**: al actualizar, solo se piden los nuevos.
- Si fallan los motores, los títulos quedan en su idioma y se reintenta a los 10 minutos.
- Los títulos traducidos también sirven para buscar, para agrupar historias (un tema en inglés se junta con el mismo en español) y para el resumen del día.

## Llevarlo a ChatGPT, Claude o Gemini (sin API key)

Debajo de **✦ Generar con IA** está la barra para copiar:

- **📋 Copiar pedido**: copia al portapapeles el pedido completo (instrucciones de la plantilla + la nota, el tema o los titulares). Después lo pegás donde quieras con Ctrl+V.
- **Copiar y abrir ChatGPT / Claude / Gemini**: copia y abre la IA en otra pestaña; ahí solo pegás y mandás.
- **Ver el pedido** lo muestra entero, y si es demasiado largo para pegar se puede descargar como .txt.

Cada resultado de la IA de la app también tiene **📋 Copiar el resultado**, para llevarlo a un mail, un chat o un documento.

## Plantillas

**Una nota**
🧭 Entender a fondo · ⚡ Resumen express · 💼 Brief ejecutivo · 🔎 Hechos vs. opiniones · ⚖️ Las ideas en juego · 🕰️ Contexto y cronología · 🎭 Mapa de actores · 🧒 Explicámelo simple · ❓ Preguntas para seguir · 🎧 Para escuchar · 📣 Para compartir · 🌐 Traducir al español · ✍️ Mi propio pedido

**Un tema (varios medios)**
🔬 Profundizar (los 7 pasos de Panorama, con mapa conceptual Mermaid que se dibuja en pantalla) · 📋 Todo lo que se sabe · 📰 Cómo lo cuenta cada medio · ⚡ Resumen del tema · ⚖️ Las ideas en juego · 🎧 Para escuchar · ✍️ Mi propio pedido

**El día**
🗞️ Resumen del día · ⚡ En 10 líneas · 📑 Informe completo · 🧩 Agenda y silencios · 🎧 Para escuchar · ✍️ Mi propio pedido

Cada resultado se puede **descargar (.md)**, **copiar** y **escuchar** con la voz del navegador (gratis, elige una voz argentina si hay; en Windows, Edge trae Elena y Tomás).

Para sumar o cambiar una plantilla, editá `plantillas.py`: cada una es un diccionario con nombre, descripción e instrucciones. La app la muestra sola.

## Archivos

| Archivo | Qué es |
|---|---|
| `app.py` | La interfaz de Streamlit |
| `plantillas.py` | Las plantillas de IA y el armado del material |
| `lector.py` | Lectura de portadas, feeds y notas (el motor de Panorama, sin FastAPI) + agrupado de titulares |
| `fuentes.py` | Secciones y medios (el mismo de Panorama) |
| `ia_motores.py` | Los motores de IA (el mismo del Monitor) |
| `traductor.py` | Traducción de títulos en tandas, con memoria |

## Probar en tu computadora

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # y pegá al menos una clave
streamlit run app.py
```

## Publicar en Streamlit Cloud

1. Subí la carpeta a un repo de GitHub (el `.gitignore` ya deja afuera `secrets.toml`).
2. En share.streamlit.io → **Create app** → elegí el repo y `app.py`.
3. **Settings → Secrets**: pegá el contenido de `.streamlit/secrets.toml.example` con tus claves. Alcanza con una (Gemini es la más fácil y es gratis).

También se pueden pegar las claves en la barra lateral (🔑 Claves), y duran lo que dura la sesión.

## Cómo lee las noticias

Igual que Panorama: cada medio se lee de su portada o de su feed RSS; si no responde, usa **Google News** como respaldo (la nota se marca "vía Google News"). Cada sección se vuelve a leer como mucho cada 5 minutos (o con **🔄 Actualizar**). Las notas con muro de pago o de Google News pueden no leerse completas: la app avisa y la IA trabaja con título y bajada.
