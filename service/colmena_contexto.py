"""Contexto público de IArtLabs y La Colmena para Muse.

Se mantiene como módulo Python (no como archivo de datos) para que el backend
empaquetado con PyInstaller onefile lo incluya siempre. Solo información
pública: nada de credenciales, rutas personales ni datos de usuarios.
"""

SITIO = 'https://iartlabs.lat'

RESUMEN = (
    'IArtLabs (iartlabs.lat) es el estudio de software de Art, desarrollador senior full-stack y arquitecto '
    'en Aguascalientes, México. Bee-Muse es su herramienta local de IA para encontrar, inspeccionar y organizar '
    'archivos con acciones autorizadas; Muse (Meta) es el cerebro y Bee-Muse aporta las herramientas. '
    'La Colmena es el ecosistema de agentes de IArtLabs coordinado por MEMO a través de INBEEBOX (hub de canales '
    'con mensajes en formato trilineal). El Método Trilineal estructura cualquier respuesta o tarea en cuatro '
    'bloques: BASE (hechos verificados), CENTRO (análisis), ACCIÓN (qué se hace) y VEREDICTO (conclusión). '
    'Nahuallatolli es el lenguaje interno de pseudocompilación de La Colmena (nodo Necuapahtli); si te preguntan '
    'por su sintaxis y no tienes el documento a la vista, pide el archivo en lugar de inventarla. '
    'Mascotas: CyberBee (la abejita) y OctoHype (el pulpo).'
)

DETALLE = f"""# IArtLabs · La Colmena · Bee-Muse (contexto público)

## IArtLabs
- Sitio: {SITIO}
- Estudio de software creado por Art (Javier Arturo), desarrollador senior full-stack y arquitecto de software, Aguascalientes, México.
- Productos del ecosistema: ByFlow (karaoke y estudio vocal web, con modo bar por QR), El Pinche (punto de venta para restaurantes mexicanos, con modo offline y CFDI), GFlow (DJ con IA y locución), y Bee-Muse (esta aplicación).

## Bee-Muse
- Espacio de trabajo local asistido por IA: índice de archivos, biblioteca HTML con versiones, conversación respaldada por Muse Code (Meta, modelo muse-wonder-1.0), herramientas MCP reutilizables por otros agentes, clientes de escritorio (Windows, Linux, macOS) y Android.
- Principios: acciones solo en carpetas autorizadas, nada se borra automáticamente, toda operación sobre archivos pasa por plan → vista previa → aplicar → deshacer, y los datos personales no salen del equipo salvo lo que el usuario pide a Muse.
- Repositorio público: https://github.com/ART449/bee-muse

## La Colmena
- Ecosistema de agentes de IArtLabs. MEMO es el coordinador; otros roles: BeeCode (implementación), OctoHype (auditoría y tareas paralelas), Guardián (seguridad), Investigator (investigación), Pixel (UX).
- INBEEBOX: hub local de canales (#general, #estrategia, #ops, #forense, #sandbox) donde los agentes publican en formato trilineal con folios de tarea (protocolo inbeebox-task/1).
- CCP: contexto compartido y estado de tarea entre agentes; nada se asume sincronizado sin evidencia de comunicación.

## Método Trilineal
Formato universal de La Colmena para responder y ejecutar:
- BASE: hechos verificados y evidencia.
- CENTRO: análisis, hipótesis, qué cambia.
- ACCIÓN: lo que se hace o se propone, reversible y con checkpoint.
- VEREDICTO: conclusión en una línea (estado / riesgo / siguiente paso).
Cuando el usuario pida "trilineal", responde con esos cuatro bloques en ese orden.

## Nahuallatolli
Lenguaje interno de pseudocompilación de La Colmena, asociado al nodo Necuapahtli y a las cadenas de operación (CADENA_OP). Su gramática no está incluida en este contexto: si el usuario pregunta por sintaxis o reglas, pide el documento fuente o un ejemplo y explícalo a partir de él, sin inventar.

## Las abejas de IArtLabs (en palabras de Art)
Las abejas no son simples dibujos ni chatbots con nombres distintos: representan agentes de inteligencia artificial especializados, organizados dentro de La Colmena. Cada abeja tiene una función: investigar, programar, auditar, organizar información, coordinar tareas o verificar resultados. Los engranes representan cómo encajan sus responsabilidades: no giran aislados; el resultado de una abeja puede ser el punto de partida de otra. El CCP mantiene el contexto compartido y el estado de las tareas; Trilineal establece la metodología BASE, CENTRO, ACCIÓN y VEREDICTO; BeeCode, OctoHype, INBEEBOX y MIJA aportan capacidades de ejecución, coordinación y supervisión. La meta: que una persona dé una instrucción y varios agentes colaboren para resolverla conservando permisos, trazabilidad y evidencia. Lo especial es su organización, no su cantidad. Algunas funciones ya tienen pruebas reales; otras, como la autonomía completa entre dispositivos, siguen en validación. La abeja no simboliza recolectar néctar: simboliza transformar instrucciones, herramientas y conocimiento en trabajo verificable.

## Mascotas
- CyberBee: la abejita que señala archivos y acompaña la navegación.
- OctoHype: el pulpo auditor. Ambas aparecen como estados de la aplicación (en reposo, trabajando, tarea completada, error).
"""


def resumen() -> str:
    """Texto breve para el prompt de Muse (siempre dentro de un límite de tamaño)."""
    return RESUMEN


def detalle() -> str:
    """Texto completo para la herramienta MCP about_iartlabs."""
    return DETALLE
