# Bee-Muse · continuidad operativa

## Fuente vigente

Repositorio privado: https://github.com/ART449/bee-muse

La base recuperada y las mejoras tienen commits separados. Este repositorio es Bee-Muse; no renombrar ni reemplazar el repositorio histórico de BeeCode con este código.

## Intención de Art

Herramientas para IA, no una IA nueva ni solamente un buscador HTML. Muse es el cerebro; Bee-Muse reúne conversación, archivos, código, terminal, MCP y herramientas del ecosistema. Integrar después el BeeCode correcto de OpenCode e INBEEBOX. Destinos: Windows, Linux, macOS y Android.

## Comprobado

- 16 pruebas locales aprobadas, incluyendo búsqueda de coincidencias más allá de los primeros 50 000 registros.
- Prueba real de Muse: creación de archivo, respuesta al cálculo solicitado y selección de un archivo del índice MCP. Evidencia local en runtime/live-probe-windows.json, excluida de Git por ser salida de ejecución.
- Cliente MCP externo descubre y consulta herramientas.
- INBEEBOX local respondió a /health; no se enviaron mensajes.
- Nueve animaciones copiadas del ZIP de Art, con huellas y estados de la aplicación.
- GitHub Actions completó con éxito las compilaciones y pruebas automatizadas Windows, Linux y macOS de la versión 0.4.0, commit `7ee7de5`, ejecución `41500896693`. El APK Android también compiló, ejecución `41500341989`. Compilar no certifica interacción gráfica ni OAuth en cada equipo.
- Meta: aplicación Bee-Muse `1747909204005226` creada, asignada al portfolio IArtLabs `1042930465579250` y con `FB_LOGIN` agregado. Art autorizó cada operación y las lecturas posteriores confirmaron el resultado. No hay retornos OAuth configurados todavía.

## Pendientes reales, en orden

1. Completar el retorno OAuth en Meta y el proveedor Facebook en Firebase. Los datos están en META.md. El MCP no entrega el secreto ni permite escribir el retorno; configurarlos en los paneles protegidos sin copiar secretos al chat. Revisar el proveedor actual antes de modificar el proyecto Firebase compartido con ByFlow.
2. Recuperar el fork OpenCode correcto de BeeCode. La copia C:\BYFLOW\beecode-work tiene README de Crush; el GitHub histórico ART449/beecode presenta una app Android. No usarlos como fuente buena por el nombre.
3. Probar conversación y selección de archivos en la GUI con la biblioteca existente. Conservar catálogo, historial, versiones y credenciales locales; no subirlos.
4. Dictado Meta: el CLI instalado rechazó la decodificación de WAV incluso con FFmpeg disponible. No marcarlo funcionando. La lectura de respuestas utiliza voz del equipo, no TTS de Meta.
5. Comprobar visualmente el paquete Windows 0.4.0 actualizado, sin confundirlo con la app antigua que puede seguir abierta. Después de completar las integraciones, realizar la ronda de uso real, incluido Facebook, en las plataformas disponibles.
6. Android: ya existe cliente nativo y compiló su APK de depuración. ANDROID.md describe la conexión HTTPS mediante código de un solo uso, consulta local de carpetas, chat y voces del teléfono. Falta la ronda completa de uso en dispositivo, según el orden solicitado por Art.

## Ampliación del 2 de noviembre

- Cliente Android compilado y descargado como artefacto Bee-Muse-Android-debug. No afirmar que sólo existe una especificación o que requiere Termux para instalar este cliente.
- Gateway HTTPS independiente con emparejamiento; el backend principal conserva su acceso loopback.
- Instalador de usuario y desinstalador Windows en scripts/. Conservan Roaming y la biblioteca. Se añadieron metadatos de versión al backend; no se ha firmado con certificado de publicación.
- Versión de escritorio alineada a 0.4.0.
- Meta for Developers: Art autorizó la conexión OAuth del MCP oficial y aceptó expresamente los términos para crear Bee-Muse. La aplicación ya está registrada en modo de desarrollo, ID `1747909204005226`. Art también autorizó expresamente asignarla a IArtLabs y agregar Facebook Login; ambas operaciones terminaron y se comprobaron por MCP. Siguen pendientes el retorno OAuth, el proveedor Firebase y el acceso real. La consulta de ajustes avanzados devolvió el retorno vacío; no se ha revelado ni copiado el secreto.
- La auditoría pegada por Art corresponde al portable 0.2.0. Varios procesos Electron no demuestran por sí solos varias instancias: hay procesos auxiliares. Verificar ventanas y backends antes de cerrar procesos.

## Comandos desde la raíz

## Ampliación 0.5.0 · asistente Android y navegador

- Código Android versionado en `ac8c274` y corrección de API de notificaciones en `c1f2ece`. Compilación Android correcta, ejecución `41510052508`; APK descargado fuera del repositorio en outputs/Bee-Muse-Android-0.5.0/app-debug.apk.
- Nuevos comandos locales explícitos, servicio de accesibilidad con comparación de aplicación destino y rechazo de pantallas protegidas, registros de resultados, asistente Android con sesión propia y reconocimiento delegado al servicio del sistema.
- Avisos hablados optativos por aplicación; nombres de remitente sólo cuando se habilitan e identifican. No se lee el cuerpo de mensajes ni se envía al modelo. Con el teléfono bloqueado no se anuncian notificaciones.
- Navegador HTTPS nativo en Android y Chromium en escritorio. La página remota carece de puente hacia archivos, terminal o credenciales de Bee-Muse. El navegador de escritorio pasó una prueba de navegación e aislamiento en Windows.
- Queda comprobar físicamente la interacción con el Pixel. No se añadió escucha continua ni palabra de activación. Los gestos no se reciben por red o MCP; falta el adaptador de tareas entre Muse/INBEEBOX y el dispositivo. También falta navegación para agentes por MCP.
- La ronda completa de pruebas en dispositivo sigue siendo posterior al cierre de las integraciones, como pidió Art. Las pruebas de compilación y de autorización de órdenes no equivalen a esa ronda.

## Comandos desde la raíz

Pruebas sin cuota: `python -m unittest discover -s tests -v` después de instalar requirements-mcp.txt.

Prueba real opcional, consume cuota de la sesión propia: `python scripts/verify_real_muse.py`.

Compilación: instalar requirements-build.txt, requirements-mcp.txt y requirements-voice.txt; ejecutar `python scripts/build_desktop.py`; en desktop ejecutar `npm ci` y `npm run package`.

Resultado: desktop/ready/. Conservar toda la carpeta junto al ejecutable. No se han firmado ni notarizado paquetes.

## Límite importante

El handoff histórico de Biblioteca-HTML del 30 de octubre es evidencia del estado anterior, no el estado final de esta versión. No afirmar que las restricciones antiguas siguen describiendo toda la aplicación ni que todas las integraciones nuevas están probadas.
