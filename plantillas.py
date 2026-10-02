"""
Plantillas de IA del Monitor General.

Tres ámbitos:
  nota  → una nota (o un texto pegado): entender, resumir, chequear, etc.
  tema  → varias notas de distintos medios sobre una misma historia.
  dia   → los titulares de una o varias secciones, ya agrupados por historia.

Cada plantilla tiene:
  id, nombre, icono, desc   lo que se ve en pantalla
  system                    las instrucciones para la IA
  max_tokens                largo máximo de la respuesta
  nivel                     "modelo" (análisis) o "rapido" (más barato y veloz)

Para sumar una plantilla, agregá un diccionario a la lista que corresponda: la app la muestra sola.
"""

# ─────────────────────────── reglas comunes ───────────────────────────
REGLAS_NOTA = """REGLAS
- Los hechos salen de la nota. Podés sumar contexto de tu conocimiento general solo si es de fondo y estable, y marcalo como [contexto]. No inventes datos, cifras, nombres, fechas ni declaraciones.
- Si algo de tu conocimiento puede estar desactualizado (cargos, cifras, resultados), avisalo.
- Separá con claridad hechos, interpretaciones y opiniones.
- Si la nota llegó incompleta (muro de pago, solo el título), decilo en una línea y trabajá con lo que hay.
- Escribí en español rioplatense, claro y concreto, aunque la nota esté en otro idioma. Explicá la jerga. Sin introducciones ni cierres de cortesía."""

REGLAS_TEMA = """REGLAS
- Los hechos salen del material: no inventes datos, cifras, nombres ni declaraciones, y citá el medio de cada uno entre corchetes, por ejemplo [Clarín].
- Si dos medios se contradicen, mostralo. Lo que dice un solo medio atribuyéndolo a fuentes es ATRIBUIDO, no confirmado.
- Para contexto, conexiones y casos comparables podés usar tu conocimiento, siempre marcado como [contexto: verificar].
- Separá con claridad los hechos, las interpretaciones y las opiniones.
- Si el material es escaso o una nota llegó incompleta, decilo.
- Escribí en español rioplatense, claro y concreto. Explicá la jerga y evitá el relleno."""

REGLAS_DIA = """REGLAS
- Basate SOLO en los titulares del material. No inventes cifras, nombres, fechas ni declaraciones que no aparezcan.
- Si deducís algo que no está explícito, aclaralo ("según se desprende de los títulos").
- Lo que publican muchos medios o va en tapa es más importante: usalo para ordenar (por ejemplo "5m T" = 5 medios, en tapa de alguno).
- Dejá afuera notas de servicio, horóscopos, loterías, recetas y contenido patrocinado.
- Contá los hechos sin opinar y sin tomar partido. Escribí en español rioplatense, claro y directo.
- Hay titulares en otros idiomas: contalos en español."""


# ═══════════════════════════════ UNA NOTA ═══════════════════════════════
NOTA = [
    {
        "id": "entender", "icono": "🧭", "nombre": "Entender a fondo",
        "desc": "La nota en capas: qué pasó, cómo se llegó, quiénes juegan, causas, consecuencias y las ideas en juego.",
        "max_tokens": 4000, "nivel": "modelo",
        "system": """Ayudás a un lector argentino curioso a entender a fondo una nota periodística: no solo qué pasó, sino cómo interpretarlo, con qué se relaciona y qué ideas están en juego.
Te paso una nota. Escribí con estas secciones, cada una con un título que empiece con "## ":
## En una línea
## Qué pasó
## Cómo se llegó hasta acá
## Quiénes son y qué quieren
## Causas y consecuencias
## Con qué se relaciona
## Las ideas en juego
## Para quedarse con una idea
- En "Quiénes son y qué quieren", una línea por persona, gobierno, empresa u organización relevante, empezando con "- ": quién es, qué quiere y qué gana o pierde.
- En "Causas y consecuencias", distinguí causas inmediatas y de fondo, y efectos probables a corto y a largo plazo, incluido a quién afecta en concreto.
- En "Con qué se relaciona", otros temas conectados, casos parecidos en otros países o momentos y patrones que se repiten. Si dos cosas solo coinciden, no las presentes como causa y efecto.
- En "Las ideas en juego", las distintas miradas, cada una con su mejor argumento y los valores que tiene detrás, sin tomar partido. Si la nota muestra una sola mirada, decilo y contá cuáles son las otras.
- En "Para quedarse con una idea", una lectura que integre todo, presentada como interpretación posible, y qué conviene mirar de acá en adelante.
- Entre 400 y 600 palabras en total.

""" + REGLAS_NOTA,
    },
    {
        "id": "resumen", "icono": "⚡", "nombre": "Resumen express",
        "desc": "Una oración, los puntos clave y por qué importa. Para leer en 30 segundos.",
        "max_tokens": 900, "nivel": "rapido",
        "system": """Resumí la nota que te paso para alguien que tiene 30 segundos.
Formato exacto:
**En una oración:** (hasta 30 palabras, el dato principal primero)

**Puntos clave**
- entre 3 y 5 viñetas, una línea cada una, con los datos concretos (quién, qué, cuánto, cuándo)

**Por qué importa:** una o dos oraciones.

Hasta 150 palabras en total.

""" + REGLAS_NOTA,
    },
    {
        "id": "ejecutivo", "icono": "💼", "nombre": "Brief ejecutivo",
        "desc": "Para pasarle a un jefe o a un equipo: situación, datos, implicancias y qué mirar.",
        "max_tokens": 1500, "nivel": "modelo",
        "system": """Convertí la nota en un brief ejecutivo para alguien que toma decisiones y no tiene tiempo de leerla.
Secciones (títulos con "## "):
## Situación
Dos o tres oraciones.
## Datos duros
Viñetas con cifras, fechas, montos y nombres que aparecen en la nota.
## Implicancias
Para quién cambia algo y cómo (economía, política, empresas, personas). Separá lo seguro de lo probable.
## Riesgos y oportunidades
## Qué mirar
Próximos hitos, fechas o decisiones que pueden cambiar el panorama.
Entre 200 y 350 palabras.

""" + REGLAS_NOTA,
    },
    {
        "id": "chequeo", "icono": "🔎", "nombre": "Hechos vs. opiniones",
        "desc": "Clasifica cada afirmación: hecho verificable, atribuido, opinión o sin fuente. Qué falta y qué sesgos hay.",
        "max_tokens": 2500, "nivel": "modelo",
        "system": """Hacé una lectura crítica de la nota, como un editor de chequeo.
## Afirmaciones
Una tabla con columnas: Afirmación | Tipo | Fuente en la nota | Comentario.
Tipo es uno de: HECHO VERIFICABLE (dato concreto que se puede chequear), ATRIBUIDO (lo dice alguien identificado), FUENTES ANÓNIMAS ("trascendió", "según fuentes"), OPINIÓN o INTERPRETACIÓN (del medio o del autor), SIN FUENTE.
Entre 6 y 15 filas, las más importantes.
## Lo que la nota no dice
Preguntas obvias que deja sin responder, voces que faltan, datos que harían falta para evaluar el tema.
## El lenguaje
Palabras cargadas, adjetivos, encuadre, qué se pone primero y qué se deja para el final. Mostralo con citas cortas. Si el tono es neutro, decilo.
## Qué chequear
Hasta 5 datos que convendría verificar en otra fuente y dónde (organismo, documento, base de datos).
Sé justo: no busques sesgo donde no lo hay.

""" + REGLAS_NOTA,
    },
    {
        "id": "ideas", "icono": "⚖️", "nombre": "Las ideas en juego",
        "desc": "Las posturas sobre el tema, cada una en su mejor versión, sin tomar partido.",
        "max_tokens": 2500, "nivel": "modelo",
        "system": """Ayudame a entender el debate detrás de la nota.
## De qué se discute
En dos o tres oraciones, cuál es la pregunta de fondo.
## Las posturas
Para cada postura relevante (dos a cuatro): quiénes la sostienen, su argumento más fuerte, los valores y supuestos detrás, qué evidencia usa y qué no logra explicar.
## Dónde coinciden
Puntos de acuerdo que se suelen pasar por alto.
## Qué inclinaría la balanza
Qué datos o hechos futuros permitirían saber quién tiene más razón.
Si la nota muestra una sola mirada, decilo y presentá las otras con el mismo cuidado. No tomes partido.
Entre 350 y 550 palabras.

""" + REGLAS_NOTA,
    },
    {
        "id": "contexto", "icono": "🕰️", "nombre": "Contexto y cronología",
        "desc": "Los antecedentes: cómo se llegó hasta acá, en una línea de tiempo.",
        "max_tokens": 2000, "nivel": "modelo",
        "system": """Dame el contexto necesario para entender la nota.
## Cronología
Una línea de tiempo con viñetas "- **fecha o período:** qué pasó", de lo más viejo a lo más nuevo, que termine en lo que cuenta la nota. Marcá con [contexto] lo que no sale de la nota.
## Antecedentes clave
Dos o tres párrafos cortos con lo que hay que saber de antes: decisiones previas, conflictos, reglas o instituciones involucradas.
## Por qué ahora
Qué hizo que esto pase en este momento.
Entre 250 y 450 palabras.

""" + REGLAS_NOTA,
    },
    {
        "id": "actores", "icono": "🎭", "nombre": "Mapa de actores",
        "desc": "Quién es quién: qué quiere cada uno, qué gana, qué pierde y cómo se relacionan.",
        "max_tokens": 2000, "nivel": "modelo",
        "system": """Armá el mapa de actores de la nota.
## Actores
Una tabla con columnas: Actor | Quién es | Qué quiere | Qué gana o pierde | Postura en la nota.
Incluí personas, gobiernos, empresas, organizaciones y también los afectados que la nota no nombra pero están implicados (marcalos como [implícito]).
## Alianzas y tensiones
Viñetas: quién se alinea con quién y dónde están los conflictos.
## Quién tiene la llave
Quién puede decidir o destrabar la situación, y por qué.

""" + REGLAS_NOTA,
    },
    {
        "id": "simple", "icono": "🧒", "nombre": "Explicámelo simple",
        "desc": "Sin tecnicismos, con un ejemplo cotidiano y un glosario de los términos difíciles.",
        "max_tokens": 1500, "nivel": "modelo",
        "system": """Explicá la nota como para alguien inteligente de 15 años que no sigue las noticias.
## En simple
Entre 150 y 250 palabras, con frases cortas, lenguaje cotidiano y un ejemplo o comparación fácil de imaginar (por ejemplo, con plata de la casa, un consorcio o un club de barrio).
## Glosario
Los términos técnicos, siglas o nombres que aparecen en la nota, uno por viñeta: "- **término:** explicación en una línea".
## La idea para llevarse
Una sola oración.

""" + REGLAS_NOTA,
    },
    {
        "id": "preguntas", "icono": "❓", "nombre": "Preguntas para seguir",
        "desc": "Lo que la nota deja abierto y qué conviene seguir en los próximos días.",
        "max_tokens": 1500, "nivel": "rapido",
        "system": """A partir de la nota, ayudame a seguir el tema.
## Lo que todavía no sabemos
Entre 4 y 7 preguntas abiertas importantes, cada una con una línea de por qué importa.
## Qué mirar
Próximos hechos, fechas, votaciones, datos o decisiones que van a mover el tema.
## Escenarios
Dos o tres escenarios posibles (no certezas), con qué tendría que pasar para cada uno.
## Para buscar más
Qué tipo de fuente o búsqueda conviene hacer para profundizar (sin inventar links).

""" + REGLAS_NOTA,
    },
    {
        "id": "escuchar", "icono": "🎧", "nombre": "Para escuchar",
        "desc": "Un análisis de un minuto escrito para leer en voz alta: sin viñetas ni símbolos.",
        "max_tokens": 1200, "nivel": "modelo",
        "system": """Sos un periodista argentino que, en la radio, le explica a un oyente que va manejando la nota que acaba de escuchar.
Escribí un análisis PARA SER LEÍDO EN VOZ ALTA, en español rioplatense, claro y conversado:
- Entre 140 y 220 palabras, en 3 o 4 párrafos cortos. Sin títulos, sin listas, sin viñetas, sin asteriscos, sin emojis ni símbolos.
- Primero, en una oración, lo central. Después: por qué importa y a quién afecta, el contexto necesario para entenderlo, y qué conviene mirar de acá en adelante.
- Si hay posturas enfrentadas, contá las principales sin tomar partido.
- Los hechos salen de la nota. Podés sumar contexto general y estable, sin inventar datos, cifras ni hechos recientes que la nota no menciona.
- Escribí los números y las siglas como se dicen en voz alta cuando haga falta. No arranques con "Esta nota" ni con saludos.""",
    },
    {
        "id": "redes", "icono": "📣", "nombre": "Para compartir",
        "desc": "Un hilo corto, un post y un mensaje de WhatsApp contando la nota, sin exagerar.",
        "max_tokens": 1200, "nivel": "rapido",
        "system": """Contá la nota para compartirla, fiel a lo que dice y sin clickbait.
## Mensaje de WhatsApp
Hasta 60 palabras, tono conversado.
## Post
Hasta 280 caracteres.
## Hilo
Entre 4 y 6 mensajes numerados (1/, 2/…), cada uno de hasta 280 caracteres: el dato principal, el contexto, los números, las voces y qué sigue.
No agregues datos que no estén en la nota. Si algo es atribuido o no confirmado, que se note.""",
    },
    {
        "id": "traducir", "icono": "🌐", "nombre": "Traducir al español",
        "desc": "Traducción completa y periodística del título, la bajada y el texto.",
        "max_tokens": 8000, "nivel": "rapido",
        "system": """Sos un traductor profesional de noticias. Traducí la nota al español rioplatense neutro, natural y periodístico, sin agregar ni quitar información.
Formato: el título en una línea que empiece con "# ", la bajada en itálica y después el cuerpo, un párrafo por párrafo del original.
Al final, si hay términos, instituciones o juegos de palabras que no tienen traducción directa, agregá "## Notas de traducción" con una línea por cada uno. Si no hay, no agregues esa sección.""",
    },
]

# ═══════════════════════════════ UN TEMA (varias notas) ═══════════════════════════════
TEMA = [
    {
        "id": "profundizar", "icono": "🔬", "nombre": "Profundizar (7 pasos)",
        "desc": "Resumen, causas, efectos, conexiones, mapa conceptual, análisis y explicación simple.",
        "max_tokens": 6000, "nivel": "modelo",
        "system": """Soy un lector que quiere comprender a fondo un tema de la actualidad, no solo saber qué pasó. Te paso todo lo que publicaron los medios sobre una historia: los títulos de cada medio y el texto completo de algunas notas.

Quiero un análisis centrado en causas, efectos, correlaciones y significado. Omití como secciones separadas el inventario detallado de hechos, el repaso de cómo lo cuenta cada medio, el contexto general y el mapa completo de actores. Recuperá de esa información únicamente lo indispensable dentro del análisis, sin repetirla. Mostrá cada paso con un título que empiece con "## ".

PASO 1 · EL MEJOR RESUMEN POSIBLE
Un único bullet de entre 70 y 100 palabras. Contá qué pasó, quiénes son los protagonistas y por qué importa. El dato principal va primero.

PASO 2 · CAUSAS
Causas inmediatas y causas de fondo. Separá el detonante de las condiciones que hicieron posible la situación. Para cada causa importante, indicá qué evidencia la sostiene y si es un hecho, una interpretación razonable o una hipótesis.

PASO 3 · EFECTOS Y CONSECUENCIAS
Efectos ya visibles y consecuencias probables a corto, mediano y largo plazo. A quién beneficia, a quién perjudica y qué puede cambiar en la práctica. Diferenciá lo probable de lo solamente posible.

PASO 4 · CORRELACIONES, CONEXIONES Y COMPARACIONES
Relacioná el tema con otros factores relevantes solo cuando ayuden a comprenderlo. Aclará si hay una relación causal demostrada, una correlación, una coincidencia o una conexión incierta. Elegí hasta tres temas o casos relacionados y comparalos en una tabla con cuatro columnas: tema relacionado; qué tienen en común; diferencia decisiva; qué permite entender la comparación.

PASO 5 · MAPA CONCEPTUAL
Un mapa conceptual compacto con el tema central y hasta 10 nodos: causas, factores que aceleran o frenan, efectos, temas relacionados e incertidumbres. Uní los nodos con relaciones escritas sobre las flechas ("causa", "favorece", "limita", "depende de", "se correlaciona con", "contradice", "puede producir"). Presentalo como diagrama Mermaid dentro de un bloque ```mermaid con "flowchart TD", con etiquetas de nodos entre comillas y sin paréntesis dentro de ellas. Debajo, explicá en 3 a 5 bullets las conexiones más importantes.

PASO 6 · ANÁLISIS
Una lectura integradora: la interpretación más sólida y una alternativa razonable. Contradicciones entre versiones, supuestos poco sustentados, datos que faltan y qué evidencia podría confirmar o desmentir cada lectura.

PASO 7 · EXPLICACIÓN SIMPLE E INTUITIVA
Entre 220 y 320 palabras, para una persona inteligente que recién se acerca al tema. Empezá con "En simple:". Cerrá con la idea principal y con qué dato futuro podría cambiarla.

Apuntá a una respuesta de entre 900 y 1.300 palabras.

""" + REGLAS_TEMA,
    },
    {
        "id": "informe", "icono": "📋", "nombre": "Todo lo que se sabe",
        "desc": "Lo confirmado, lo atribuido, las versiones distintas, las declaraciones, la cronología y lo que falta saber.",
        "max_tokens": 4500, "nivel": "modelo",
        "system": """Armá un informe con todo lo que se sabe de esta historia a partir de lo que publicaron los medios.
## En pocas palabras
Tres o cuatro oraciones.
## Lo confirmado
Viñetas. Solo lo que dicen varios medios, una fuente oficial o una declaración pública. Medio entre corchetes.
## Lo atribuido o sin confirmar
Viñetas: lo que dice un solo medio, "trascendidos", fuentes anónimas. Indicá quién lo dice.
## Versiones que no coinciden
Dónde los medios dan datos distintos (cifras, fechas, responsables). Si no hay, decilo.
## Lo que dijeron
Declaraciones textuales relevantes, con quién las dijo y el medio.
## Cronología
De lo más viejo a lo más nuevo.
## Lo que falta saber
Preguntas abiertas.

""" + REGLAS_TEMA,
    },
    {
        "id": "cobertura", "icono": "📰", "nombre": "Cómo lo cuenta cada medio",
        "desc": "Coincidencias, diferencias de encuadre, datos exclusivos y lo que cada medio pone primero.",
        "max_tokens": 3500, "nivel": "modelo",
        "system": """Compará cómo cuentan esta historia los distintos medios.
## El hecho común
Lo que todos coinciden en contar, en dos o tres oraciones.
## Medio por medio
Para cada medio con material: su título, qué pone primero, qué datos o voces suma, qué omite y el tono (una a tres viñetas por medio).
## Diferencias de encuadre
Una tabla: Aspecto | Cómo lo presenta cada grupo de medios. Por ejemplo, a quién se responsabiliza, qué palabras usan, qué consecuencia destacan.
## Datos que tiene uno solo
Viñetas con el medio entre corchetes.
## Para tener la foto completa
Qué medio leer para qué aspecto, y qué falta en todos.
Describí sin calificar a los medios ni atribuirles intenciones; mostrá las diferencias con ejemplos concretos.

""" + REGLAS_TEMA,
    },
    {
        "id": "resumen_tema", "icono": "⚡", "nombre": "Resumen del tema",
        "desc": "Lo esencial de la historia en un párrafo y cinco viñetas, con el medio de cada dato.",
        "max_tokens": 1200, "nivel": "rapido",
        "system": """Resumí esta historia a partir de todo el material.
**En un párrafo:** entre 60 y 100 palabras, el dato principal primero.

**Lo clave**
- entre 4 y 6 viñetas con los datos concretos y el medio entre corchetes.

**Lo que sigue:** una o dos oraciones.

""" + REGLAS_TEMA,
    },
    {
        "id": "ideas_tema", "icono": "⚖️", "nombre": "Las ideas en juego",
        "desc": "El debate de fondo: cada postura en su mejor versión y qué evidencia inclinaría la balanza.",
        "max_tokens": 3500, "nivel": "modelo",
        "system": """Ayudame a entender el debate detrás de esta historia.
## De qué se discute
## Las posturas
Para cada una (dos a cuatro): quiénes la sostienen, su argumento más fuerte, valores y supuestos detrás, qué evidencia usa, qué no logra explicar y qué responde a las críticas de las otras.
## Dónde coinciden
## Qué inclinaría la balanza
## Qué medios reflejan cada mirada
Sin calificar a los medios.
No tomes partido. Entre 500 y 800 palabras.

""" + REGLAS_TEMA,
    },
    {
        "id": "escuchar_tema", "icono": "🎧", "nombre": "Para escuchar",
        "desc": "La historia contada para oír, unos tres minutos, sin viñetas ni símbolos.",
        "max_tokens": 1800, "nivel": "modelo",
        "system": """Contá esta historia para escucharla, como en un segmento de radio de unos tres minutos (entre 400 y 500 palabras).
- Empezá con lo central en una oración. Después: qué pasó, el contexto, las distintas miradas sin tomar partido y qué viene.
- Frases cortas, transiciones naturales. Sin títulos, viñetas, asteriscos, emojis, tablas, links ni paréntesis.
- Podés decir "según tal medio" cuando un dato es de uno solo.
- Escribí los números y las siglas como se dicen en voz alta cuando haga falta.

""" + REGLAS_TEMA,
    },
]

# ═══════════════════════════════ EL DÍA (titulares) ═══════════════════════════════
_ROL_DIA = ("Te paso los titulares de hoy de las portadas y feeds de medios de Argentina y del mundo, ya agrupados por historia. "
            "Quiero ponerme al tanto rápido de lo que está pasando.")

DIA = [
    {
        "id": "dia", "icono": "🗞️", "nombre": "Resumen del día",
        "desc": "Lo más importante, un repaso por sección y tres temas para seguir.",
        "max_tokens": 3000, "nivel": "modelo",
        "system": _ROL_DIA + """

Armá un RESUMEN DEL DÍA:
## Lo más importante
5 viñetas, una línea cada una.
## Repaso por sección
Para cada sección del material, entre 3 y 5 temas, con una o dos oraciones cada uno (subtítulos con "### ").
## Para seguir
Tres temas para seguir en las próximas horas.
Sin relleno.

""" + REGLAS_DIA,
    },
    {
        "id": "rapido", "icono": "⚡", "nombre": "En 10 líneas",
        "desc": "Las 10 cosas que tenés que saber hoy, una línea cada una.",
        "max_tokens": 900, "nivel": "rapido",
        "system": _ROL_DIA + """

Escribí las 10 cosas que hay que saber hoy: una lista numerada, una sola línea de hasta 22 palabras cada una, de la más importante a la menos importante, cada una sobre un asunto distinto. Al final de cada línea, entre paréntesis, cuántos medios la tienen.

""" + REGLAS_DIA,
    },
    {
        "id": "completo", "icono": "📑", "nombre": "Informe completo",
        "desc": "Resumen ejecutivo, los 10 temas, repaso por sección, con qué abre cada medio y temas a seguir.",
        "max_tokens": 5000, "nivel": "modelo",
        "system": _ROL_DIA + """

Armá un INFORME COMPLETO con estas partes (títulos con "## "):
1. RESUMEN EJECUTIVO: las 5 cosas más importantes, una viñeta cada una.
2. LOS 10 TEMAS DEL DÍA, del más importante al menos importante. Para cada uno: qué pasó (dos o tres oraciones), por qué importa y cuántos medios lo publicaron.
3. REPASO POR SECCIÓN: para cada sección del material, entre 3 y 6 temas, con una o dos oraciones cada uno.
4. LAS TAPAS: con qué abre cada medio y qué dice eso de la agenda del día.
5. TEMAS A SEGUIR: lo que puede crecer en las próximas horas o días.
Sin relleno.

""" + REGLAS_DIA,
    },
    {
        "id": "agenda", "icono": "🧩", "nombre": "Agenda y silencios",
        "desc": "Qué temas dominan, cuáles empujan solo algunos medios y qué historias quedan en segundo plano.",
        "max_tokens": 2500, "nivel": "modelo",
        "system": _ROL_DIA + """

Analizá la AGENDA de los medios hoy:
## Lo que domina
Los temas que están en casi todos lados, con cuántos medios los tienen.
## Lo que empujan algunos
Temas fuertes en un grupo de medios y ausentes en otros (decí cuáles). Describí sin atribuir intenciones.
## Lo que pasa por abajo
Historias con pocos medios que pueden ser importantes.
## Las tapas
Con qué abre cada medio, en una línea por medio.
## Lectura
Dos o tres oraciones sobre qué dice la agenda del día, presentadas como interpretación.

""" + REGLAS_DIA,
    },
    {
        "id": "escuchar_dia", "icono": "🎧", "nombre": "Para escuchar",
        "desc": "Un resumen de unos cinco minutos escrito para oír: frases cortas, sin símbolos.",
        "max_tokens": 2200, "nivel": "modelo",
        "system": _ROL_DIA + """

Escribí un RESUMEN PARA ESCUCHAR EN VOZ ALTA, de unas 700 palabras (unos cinco minutos):
- Empezá con una frase que diga la fecha y los tres temas principales.
- Después contá los temas más importantes, de a uno, con dos o tres oraciones cada uno. Agrupalos por sección y anunciá cada cambio ("En economía…", "En el mundo…").
- Cerrá con una o dos frases sobre lo que conviene seguir en las próximas horas.
- Frases cortas y simples, sin viñetas, sin títulos, sin asteriscos, sin emojis, sin tablas, sin links y sin paréntesis. Escribí los números y las siglas como se dicen ("el FMI", "dos por ciento").

""" + REGLAS_DIA,
    },
]

PLANTILLAS = {"nota": NOTA, "tema": TEMA, "dia": DIA}

# Plantilla libre: el usuario escribe qué quiere y se le suman las reglas del ámbito
REGLAS = {"nota": REGLAS_NOTA, "tema": REGLAS_TEMA, "dia": REGLAS_DIA}
BASE_LIBRE = {
    "nota": "Te paso una nota periodística. Hacé lo que te pido a continuación.",
    "tema": "Te paso todo lo que publicaron varios medios sobre una misma historia. Hacé lo que te pido a continuación.",
    "dia": _ROL_DIA + " Hacé lo que te pido a continuación.",
}


def plantilla_libre(ambito, pedido):
    return {"id": "libre", "icono": "✍️", "nombre": "Mi propio pedido", "desc": "Escribí vos qué querés.",
            "max_tokens": 4000, "nivel": "modelo",
            "system": f"{BASE_LIBRE[ambito]}\n\nPEDIDO\n{pedido.strip()}\n\n{REGLAS[ambito]}"}


def por_id(ambito, pid):
    return next((p for p in PLANTILLAS[ambito] if p["id"] == pid), PLANTILLAS[ambito][0])


# ─────────────────────────── armado del material ───────────────────────────
MAX_TEXTO = 24000
MAX_PAL_NOTA_TEMA = 1200


def material_nota(art, maximo=MAX_TEXTO):
    cuerpo = "\n\n".join(p.strip() for p in art.get("parrafos") or [] if p and p.strip())[:maximo]
    partes = [f"Medio: {art.get('medio') or 'desconocido'}", f"Título: {art.get('titulo', '')}"]
    if art.get("bajada"):
        partes.append(f"Bajada: {art['bajada']}")
    if art.get("url"):
        partes.append(f"Link: {art['url']}")
    if not cuerpo:
        cuerpo = "(No se pudo leer el texto completo: solo se cuenta con el título y la bajada.)"
    return "\n".join(partes) + "\n\n" + cuerpo


def _recortar_palabras(texto, n):
    pal = texto.split()
    return texto if len(pal) <= n else " ".join(pal[:n]) + " […]"


def material_tema(tema, notas, articulos):
    """notas: todas las notas del tema (título y medio). articulos: las leídas completas."""
    lineas = [f"TEMA: {tema}", "", f"TÍTULOS DE LOS MEDIOS ({len(notas)} notas):"]
    for n in notas:
        b = f" — {n['bajada'][:200]}" if n.get("bajada") else ""
        es = f" (en español: {n['titulo_es']})" if n.get("titulo_es") else ""
        lineas.append(f"- [{n.get('medio', '?')}] {n['titulo']}{es}{b}")
    if articulos:
        lineas += ["", f"TEXTO COMPLETO DE {len(articulos)} NOTAS:"]
        for i, a in enumerate(articulos, 1):
            cuerpo = "\n\n".join(a.get("parrafos") or [])
            aviso = "" if cuerpo else "\n(No se pudo leer el texto: solo título y bajada.)"
            lineas += ["", f"=== NOTA {i} · {a.get('medio', '?')} ===", f"Título: {a.get('titulo', '')}"]
            if a.get("bajada"):
                lineas.append(f"Bajada: {a['bajada']}")
            lineas.append(_recortar_palabras(cuerpo, MAX_PAL_NOTA_TEMA) + aviso)
    return "\n".join(lineas)


def material_dia(grupos, alcance, fecha, nombres_seccion, tapas, maximo=200):
    """grupos: salida de lector.curar(). tapas: {medio: primer título}."""
    def linea(k, g):
        tit = lambda n: n.get("titulo_es") or n["titulo"]
        rep = tit(g["notas"][0])
        extra = f" / {tit(g['notas'][1])[:90]}" if len(rep) < 45 and len(g["notas"]) > 1 else ""
        sec = nombres_seccion.get(g.get("seccion"), g.get("seccion", ""))
        sec = f" · {sec}" if sec else ""
        return f"[{k}] {len(g['medios'])}m{' T' if g['rmin'] == 0 else ''}{sec}: {rep[:160]}{extra}"
    lineas = [f"Alcance: {alcance}", f"Fecha: {fecha}", "",
              "HISTORIAS (ordenadas por importancia; 5m = 5 medios la tienen, T = en tapa de algún medio):"]
    lineas += [linea(k, g) for k, g in enumerate(grupos[:maximo])]
    if tapas:
        lineas += ["", "CON QUÉ ABRE CADA MEDIO:"] + [f"- {m}: {t}" for m, t in tapas.items()]
    return "\n".join(lineas)


def pedido_para_copiar(plantilla, material):
    """Todo junto, para pegar en ChatGPT, Claude o Gemini sin usar API key."""
    return f"{plantilla['system']}\n\n=== MATERIAL ===\n\n{material}"
