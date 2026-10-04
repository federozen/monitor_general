# 📡 Monitor General

Las noticias de los medios de **Panorama** (Argentina, Economía, Mundo, Exterior, Provincias, Deportes e IA) en una app de **Streamlit**, con **plantillas de IA** para entender una nota, resumirla, chequearla, profundizar un tema en todos los medios o armar el resumen del día.

Usa los **mismos motores de IA** del Monitor: Gemini, Mistral, Groq y OpenRouter (gratis) primero, y Claude (pago) de respaldo. Y si no tenés ninguna clave, cada plantilla arma el **pedido listo para pegar** en ChatGPT, Claude o Gemini.

## Las vistas

| Vista | Qué hace |
|---|---|
| **📰 Noticias** | Los medios de la sección elegida. Tres formas de ver: **Por medio**, **Intercalado** (la 1ª nota de cada medio, después la 2ª…) y **Por tema** (titulares agrupados por historia, ordenados por cuántos medios la tienen y si va en tapa; sin IA). Buscador que no distingue tildes ni mayúsculas. En cada nota: 🧠 para analizarla y ➕ para sumarla a un tema. |
| **🧠 Analizar nota** | Una nota elegida, un link cualquiera o un texto pegado. Se lee completa y se elige una plantilla. Abajo, **💬 Preguntale a la nota**. |
| **🗂️ Tema** | Varias notas de distintos medios sobre una misma historia (buscadas por palabra en la sección o en todas, o juntadas con ➕). Lee completas hasta 8 (una por medio primero) y las analiza juntas. |
| **🗞️ Resumen del día** | Elegís las secciones; la app agrupa y ordena las historias de **cada sección por separado** (con su cupo y las aperturas de todos sus medios, para que ninguna tape a las otras), suma lo más fuerte entre todas y la IA arma el resumen cubriendo cada sección. |
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

## 🎧 Escuchar los títulos (modo auto)

Como el Modo auto de Panorama: la vista **🎧 Escuchar** (o el botón en Noticias) lee los títulos uno tras otro con la voz del navegador, gratis y sin IA, y pasa sola a la nota siguiente.

- **Qué escuchar:** la sección actual, varias secciones o el tema armado.
- **Orden:** *Intercalado* (la principal de cada medio, después la segunda…) o *Medio por medio* (anuncia "Ahora, Clarín").
- **Notas por medio**, **leer también la bajada**, **velocidad** y **voz** (elige sola una argentina; en Windows, con Edge, Elena o Tomás suenan naturales).
- Controles: ⏮ anterior, ▶/⏸, ⏭ siguiente, ⏩ próximo medio y 🔗 abrir la nota. Teclado: espacio, ← →, ↑ ↓. En el celular, deslizar el dedo.
- **Saltea las ya escuchadas** y **sigue donde quedaste** (se guarda en el navegador). Los títulos en otros idiomas se leen traducidos.
- Mientras suena, intenta que la pantalla no se apague: si el celular se bloquea, el navegador corta la voz.

## Plantillas

**Una nota**
🧭 Entender a fondo · ⚡ Resumen express · 💼 Brief ejecutivo · 🔎 Hechos vs. opiniones · ⚖️ Las ideas en juego · 🕰️ Contexto y cronología · 🔗 Correlaciones · 🎭 Mapa de actores · 🧒 Explicámelo simple · ❓ Preguntas para seguir · 🎧 Para escuchar · 📣 Para compartir · 🌐 Traducir al español · 🃏 Para no olvidarla · 🎓 Explicalo con tus palabras · 🗂️ Ficha para guardar · ✍️ Mi propio pedido

**Un tema (varios medios)**
🔬 Profundizar (los 7 pasos de Panorama, con mapa conceptual Mermaid que se dibuja en pantalla) · 🔗 Correlaciones · 📋 Todo lo que se sabe · 📰 Cómo lo cuenta cada medio · ⚡ Resumen del tema · ⚖️ Las ideas en juego · 🎧 Para escuchar · 🃏 Para no olvidarlo · 🗂️ Ficha para guardar · ✍️ Mi propio pedido

**El día**
🗞️ Resumen del día · ⚡ En 10 líneas · 📑 Informe completo · 🧩 Agenda y silencios · 🎧 Para escuchar · 🃏 Quiz del día · ✍️ Mi propio pedido

**🔗 Correlaciones** arma las variables en juego, una tabla de relaciones que distingue causa, correlación, causa común, retroalimentación y coincidencia (con su nivel de confianza), cadenas de efectos indirectos, círculos viciosos o virtuosos, cruces con otros temas, casos comparables, un mapa de relaciones dibujado y qué dato confirmaría o desmentiría cada relación.

**Para entender y no olvidar** (técnicas de aprendizaje: recuperación activa, elaboración y repetición espaciada):
- **🃏 Para no olvidarla / Quiz del día**: lo esencial, una imagen para anclarla, tarjetas de pregunta y respuesta que se dan vuelta con un clic y una autoevaluación con las respuestas ocultas. Conviene repasarlas al día siguiente, a los 3 días y a la semana.
- **🎓 Explicalo con tus palabras** (método Feynman): la nota en una frase, un párrafo y en profundidad, una analogía, lo que se suele entender mal y consignas para explicarla vos, con la respuesta oculta.
- **🗂️ Ficha para guardar**: una ficha en Markdown para Notion, Obsidian o Keep, con la idea central como afirmación, datos, etiquetas y conceptos entre [[doble corchete]] para enlazar fichas entre sí.

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
| `reproductor.py` | El reproductor de voz de 🎧 Escuchar |

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

## Olé en Deportes

En la sección Deportes, Olé aparece dos veces, con los lectores propios del Monitor deportivo y más notas que el resto de los medios:

- **Olé · Home**: la portada de ole.com.ar en el orden en que aparece (la primera es la nota principal), hasta 40 notas.
- **Olé · Últimas**: el listado de ole.com.ar/ultimas-noticias, con lo último publicado aunque nunca pise la portada, hasta 50 notas. Si esa página no responde, usa el feed RSS de Olé y después Google News.

## Cómo lee las noticias

Igual que Panorama: cada medio se lee de su portada o de su feed RSS; si no responde, usa **Google News** como respaldo (la nota se marca "vía Google News"). Cada sección se vuelve a leer como mucho cada 5 minutos (o con **🔄 Actualizar**). Las notas con muro de pago o de Google News pueden no leerse completas: la app avisa y la IA trabaja con título y bajada.
