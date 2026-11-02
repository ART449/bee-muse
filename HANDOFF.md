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
- GitHub Actions completó con éxito las compilaciones Windows, Linux y macOS de la revisión anterior a la última mejora de búsqueda. Compilar no certifica interacción gráfica ni OAuth en cada equipo.

## Pendientes reales, en orden

1. Confirmar la última compilación en Actions y comprobar visualmente el paquete Windows actualizado. No confundirlo con la app antigua que puede seguir abierta.
2. Recuperar el fork OpenCode correcto de BeeCode. La copia C:\BYFLOW\beecode-work tiene README de Crush; el GitHub histórico ART449/beecode presenta una app Android. No usarlos como fuente buena por el nombre.
3. Probar conversación y selección de archivos en la GUI con la biblioteca existente. Conservar catálogo, historial, versiones y credenciales locales; no subirlos.
4. Dictado Meta: el CLI instalado rechazó la decodificación de WAV incluso con FFmpeg disponible. No marcarlo funcionando. La lectura de respuestas utiliza voz del equipo, no TTS de Meta.
5. Facebook: código y validaciones listos; falta configurar el proveedor Firebase y la aplicación/retorno OAuth en Meta, y completar un login real. No pedir secretos por chat ni inventar acceso configurado.
6. Android: ya existe cliente nativo y compiló su APK de depuración. ANDROID.md describe la conexión HTTPS mediante código de un solo uso, consulta local de carpetas, chat y voces del teléfono. Falta la ronda completa de uso en dispositivo, según el orden solicitado por Art.

## Ampliación del 2 de noviembre

- Cliente Android compilado y descargado como artefacto Bee-Muse-Android-debug. No afirmar que sólo existe una especificación o que requiere Termux para instalar este cliente.
- Gateway HTTPS independiente con emparejamiento; el backend principal conserva su acceso loopback.
- Instalador de usuario y desinstalador Windows en scripts/. Conservan Roaming y la biblioteca. Se añadieron metadatos de versión al backend; no se ha firmado con certificado de publicación.
- Versión de escritorio alineada a 0.4.0.
- Meta for Developers requiere una nueva aplicación Facebook. Se abrió el portal y está solicitando login; se pidió a Art iniciar sesión directamente. No se crearon credenciales ni se completó el registro.
- La auditoría pegada por Art corresponde al portable 0.2.0. Varios procesos Electron no demuestran por sí solos varias instancias: hay procesos auxiliares. Verificar ventanas y backends antes de cerrar procesos.

## Comandos desde la raíz

Pruebas sin cuota: `python -m unittest discover -s tests -v` después de instalar requirements-mcp.txt.

Prueba real opcional, consume cuota de la sesión propia: `python scripts/verify_real_muse.py`.

Compilación: instalar requirements-build.txt, requirements-mcp.txt y requirements-voice.txt; ejecutar `python scripts/build_desktop.py`; en desktop ejecutar `npm ci` y `npm run package`.

Resultado: desktop/ready/. Conservar toda la carpeta junto al ejecutable. No se han firmado ni notarizado paquetes.

## Límite importante

El handoff histórico de Biblioteca-HTML del 30 de octubre es evidencia del estado anterior, no el estado final de esta versión. No afirmar que las restricciones antiguas siguen describiendo toda la aplicación ni que todas las integraciones nuevas están probadas.
