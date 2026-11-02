# Evidencia de esta versión

## Verificado en Windows

- 16 pruebas automatizadas aprobadas: conversación sin coincidencias, autorización de rutas locales, identidad Facebook con proveedor verificado mediante simulación del proveedor, flujo de acceso de escritorio de un solo uso, archivos indexados, búsqueda más allá de 50 000 registros, bloqueo de rutas arbitrarias y enlaces, nueve animaciones servidas y un cliente MCP externo.
- Prueba real con Muse: creó un archivo con el contenido exacto solicitado en una carpeta temporal y respondió con el resultado correcto de un cálculo.
- Prueba real Muse + MCP: consultó `search_html` y devolvió el nombre exacto del archivo del catálogo sintético sin recorrer el disco.
- INBEEBOX local respondió `status: ok` y `service: inbeebox-api` a la consulta de salud. No se enviaron mensajes.

Las pruebas sintéticas no contienen documentos ni credenciales del propietario. No acreditan por sí solas el funcionamiento de todos los proyectos, proveedores o plataformas.

## Pendientes explícitos

- Facebook: el flujo está implementado y se prueba su validación con datos simulados. La aplicación Bee-Muse ya está registrada en Meta con ID `1747909204005226`, en modo de desarrollo, asignada al portfolio IArtLabs y con `FB_LOGIN` agregado. Los tres cambios fueron autorizados por Art y comprobados mediante lecturas posteriores del MCP oficial. Falta configurar el retorno OAuth y el proveedor en Firebase y completar un acceso real. No se han copiado secretos de Meta. [Estado y datos de configuración](META.md).
- Dictado de Meta: la grabación y el adaptador están implementados. La prueba real con audio sintético falló porque el CLI de Muse en este Windows no reconoció un decodificador de audio, incluso habiendo FFmpeg disponible. No se afirma que el dictado esté funcionando.
- Voz de respuesta: utiliza síntesis del sistema/navegador con activación explícita; no se presenta como una voz generada por Meta.
- Linux y macOS: la matriz CI de la versión 0.4.0 completó compilaciones y pruebas automatizadas. Las pruebas de interacción con los paquetes en equipos reales siguen pendientes. [Ejecución comprobada](https://github.com/ART449/bee-muse/actions/runs/41500896693).
- Android: el proyecto nativo compiló su APK de depuración en CI. El cliente incluye emparejamiento con un gateway HTTPS, consulta local de carpetas, chat y voces del equipo. El gateway está implementado; no se ha certificado una conexión con certificado real ni la ronda de uso en dispositivo. [Compilación comprobada](https://github.com/ART449/bee-muse/actions/runs/41500341989) y [conexión Android](ANDROID.md).
- BeeCode: recuperar el fork correcto antes de conectarlo.

## Repetir las pruebas

```sh
python -m pip install -r requirements-mcp.txt
python -m unittest discover -s tests -v
```

Las pruebas automatizadas no llaman al modelo ni gastan cuota. Las pruebas reales se registran aparte para no enviarlas automáticamente en CI.
