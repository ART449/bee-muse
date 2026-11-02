# Evidencia de esta versión

## Verificado en Windows

- 15 pruebas automatizadas aprobadas: conversación sin coincidencias, autorización de rutas locales, identidad Facebook con proveedor verificado mediante simulación del proveedor, flujo de acceso de escritorio de un solo uso, archivos indexados, bloqueo de rutas arbitrarias y enlaces, nueve animaciones servidas y un cliente MCP externo.
- Prueba real con Muse: creó un archivo con el contenido exacto solicitado en una carpeta temporal y respondió con el resultado correcto de un cálculo.
- Prueba real Muse + MCP: consultó `search_html` y devolvió el nombre exacto del archivo del catálogo sintético sin recorrer el disco.
- INBEEBOX local respondió `status: ok` y `service: inbeebox-api` a la consulta de salud. No se enviaron mensajes.

Las pruebas sintéticas no contienen documentos ni credenciales del propietario. No acreditan por sí solas el funcionamiento de todos los proyectos, proveedores o plataformas.

## Pendientes explícitos

- Facebook: el flujo está implementado y se prueba su validación con datos simulados. Falta habilitar el proveedor en Firebase, registrar la aplicación y el retorno OAuth en Meta y completar un acceso real. No se han creado aplicaciones ni copiado secretos de Meta.
- Dictado de Meta: la grabación y el adaptador están implementados. La prueba real con audio sintético falló porque el CLI de Muse en este Windows no reconoció un decodificador de audio, incluso habiendo FFmpeg disponible. No se afirma que el dictado esté funcionando.
- Voz de respuesta: utiliza síntesis del sistema/navegador con activación explícita; no se presenta como una voz generada por Meta.
- Linux y macOS: hay compilación reproducible y una matriz CI. Las pruebas reales en esas máquinas siguen pendientes hasta que corra y se inspeccione CI y los usuarios prueben cada paquete.
- Android: el núcleo puede probarse mediante Python en Termux. No hay todavía un APK nativo ni una conexión remota autenticada a Muse.
- BeeCode: recuperar el fork correcto antes de conectarlo.

## Repetir las pruebas

```sh
python -m pip install -r requirements-mcp.txt
python -m unittest discover -s tests -v
```

Las pruebas automatizadas no llaman al modelo ni gastan cuota. Las pruebas reales se registran aparte para no enviarlas automáticamente en CI.
