# Evidencia de esta versión

## Verificado en Windows

- 18 pruebas automatizadas aprobadas: conversación sin coincidencias, autorización de rutas locales, identidad Facebook con proveedor verificado mediante simulación del proveedor, flujo de acceso de escritorio de un solo uso, archivos indexados, búsqueda más allá de 50 000 registros, bloqueo de rutas arbitrarias y enlaces, nueve animaciones servidas, un cliente MCP externo y la preparación del decodificador de voz.
- Prueba real con Muse: creó un archivo con el contenido exacto solicitado en una carpeta temporal y respondió con el resultado correcto de un cálculo.
- Prueba real Muse + MCP: consultó `search_html` y devolvió el nombre exacto del archivo del catálogo sintético sin recorrer el disco.
- INBEEBOX local respondió `status: ok` y `service: inbeebox-api` a la consulta de salud. No se enviaron mensajes.

Las pruebas sintéticas no contienen documentos ni credenciales del propietario. No acreditan por sí solas el funcionamiento de todos los proyectos, proveedores o plataformas.

## Pendientes explícitos

### Ampliación 0.5.0

- Android: la compilación de los nuevos servicios, actividades y recursos terminó correctamente en la ejecución [Build Bee-Muse Android](https://github.com/ART449/bee-muse/actions/runs/41510052508). Se descargó su APK. Aún no se probó el uso físico de gestos, notificaciones, rol de asistente ni navegador en el Pixel.
- Navegador de escritorio: la prueba local con Electron abrió `https://example.com`, comprobó el título, rechazó esquemas locales/inseguros y direcciones con credenciales y verificó que el contenido remoto no recibe Node, BeeDesktop ni BeeBrowser. Con Bee-Muse Search se añadieron búsqueda desde la barra, apertura de superficies locales (Chingaquedito) y el puente loopback para Muse: rechaza un token incorrecto y sólo admite navegar, no leer la página (12 aserciones, 4-nov-2026, Windows). `tests/test_mcp_stdio.py` comprueba que las seis herramientas `browser_*` se publican por MCP. La revisión visual completa, una navegación dirigida por Muse en conversación real y el uso en otros sistemas siguen pendientes. El script reproducible está en `scripts/verify_browser.cjs` y necesita Electron instalado en desktop/node_modules.
- Las nuevas pruebas unitarias de órdenes Android comprueban que frases de conversación no se transforman en acciones, así como coordenadas, arrastre y normalización del español. Su resultado se registra aparte de la compilación previa.
- Los nuevos módulos no sustituyen la integración pendiente de BeeCode, el bus completo, la captura de micrófono real ni el cierre OAuth de Firebase.
- Actualización de voz: el dictado de Meta ya transcribió un WAV sintético a través de `voice_bridge.transcribe`, con el ejecutor real autenticado. Se corrigió la búsqueda literal de `ffmpeg` del CLI en Windows proporcionando también un alias sin extensión en el directorio temporal. El audio y el decodificador se retiran al terminar la solicitud. Faltan la captura con micrófono real y la ronda de uso en otras máquinas.
- La revisión `db5e46e` terminó compilaciones y pruebas automatizadas en Windows, Linux y macOS: [ejecución](https://github.com/ART449/bee-muse/actions/runs/41513553354). Android con los cinco casos de órdenes y la entrada protegida de asistente terminó en la revisión `df1944b`: [ejecución](https://github.com/ART449/bee-muse/actions/runs/41512152076).
- Distribución cerrada en `5807c65`: [compilaciones y archivos portables](https://github.com/ART449/bee-muse/actions/runs/41514484719), todas aprobadas. Se descargaron los tres paquetes, se comprobaron sus SHA-256, los permisos ejecutables de Linux/macOS y los 14 enlaces del paquete Mac. El ZIP Windows incluye instalador y desinstalador.
- También se inició el backend compilado del paquete Windows con una biblioteca sintética vacía y se realizó una transcripción de Meta por su API HTTP local autenticada. El ejecutable arrancó y devolvió el texto del audio; no se usaron documentos personales. El registro local de la entrega es compiled-voice-proof.json.

- Facebook: el flujo está implementado y se prueba su validación con datos simulados. La aplicación Bee-Muse ya está registrada en Meta con ID `1747909204005226`, en modo de desarrollo, asignada al portfolio IArtLabs y con `FB_LOGIN` agregado. Los tres cambios fueron autorizados por Art y comprobados mediante lecturas posteriores del MCP oficial. Falta configurar el retorno OAuth y el proveedor en Firebase y completar un acceso real. No se han copiado secretos de Meta. [Estado y datos de configuración](META.md).
- Dictado de Meta: transcripción real de WAV sintético aprobada después de corregir la detección del decodificador en Windows. Falta comprobar el micrófono en la interfaz y el uso en las otras plataformas.
- Voz de respuesta: utiliza síntesis del sistema/navegador con activación explícita; no se presenta como una voz generada por Meta.
- Linux y macOS: la matriz CI de la versión 0.5.0 completó compilaciones y pruebas automatizadas. Las pruebas de interacción con los paquetes en equipos reales siguen pendientes. [Ejecución comprobada](https://github.com/ART449/bee-muse/actions/runs/41513553354).
- Android: el proyecto nativo compiló su APK de depuración en CI. El cliente incluye emparejamiento con un gateway HTTPS, consulta local de carpetas, chat y voces del equipo. El gateway está implementado; no se ha certificado una conexión con certificado real ni la ronda de uso en dispositivo. [Compilación comprobada](https://github.com/ART449/bee-muse/actions/runs/41500341989) y [conexión Android](ANDROID.md).
- BeeCode: recuperar el fork correcto antes de conectarlo.

## Repetir las pruebas

```sh
python -m pip install -r requirements-mcp.txt
python -m unittest discover -s tests -v
```

Las pruebas automatizadas no llaman al modelo ni gastan cuota. Las pruebas reales se registran aparte para no enviarlas automáticamente en CI.
