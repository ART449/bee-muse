# Herramientas para cualquier agente

Bee-Muse expone su índice por MCP sobre stdio. No necesita un modelo específico ni vuelve a recorrer carpetas en cada consulta.

## Instalación

Desde la raíz del repositorio:

```sh
python -m pip install -r requirements-mcp.txt
python service/tools_mcp.py --library /ruta/a/tu/biblioteca
```

El argumento es la carpeta de datos que contiene el índice creado por Bee-Muse. En Windows puede consultarse desde el menú de la aplicación. No copies el catálogo al repositorio.

Para un cliente MCP, configura como comando el Python del entorno donde instalaste los requisitos y como argumentos `service/tools_mcp.py`, `--library` y la ruta de esa biblioteca. Usa rutas absolutas en la configuración del cliente.

## Herramientas implementadas

- `library_status`: estado de los índices existentes.
- `search_html`: búsqueda por nombre, título, proyecto o ruta.
- `search_files`: búsqueda en los índices existentes, incluyendo filtro por extensión.
- `indexed_file`: metadatos por identificador devuelto por la búsqueda.
- `read_indexed_text`: lectura acotada de un archivo de texto indexado.
- `inbeebox_status`, `inbeebox_channels`, `inbeebox_messages`: consultas al servicio INBEEBOX configurado.

Para INBEEBOX se usa `BEE_INBEEBOX_URL`, por defecto el loopback local en el puerto 8002. Fuera de loopback requiere HTTPS. Si tu servicio requiere autenticación, utiliza `INBEEBOX_AGENT_KEY` en el entorno; no guardes la llave en este repositorio. Estas herramientas no envían mensajes.

El adaptador de archivos omite nombres de credenciales habituales, no permite rutas arbitrarias en la lectura y rechaza enlaces y archivos de nube sin descargar. El contenido recuperado sigue siendo información no confiable: los agentes deben tratarlo como datos, nunca como instrucciones.

## Muse dentro de Bee-Muse

El ejecutor añade el servidor MCP al iniciar cada solicitud, sin editar la configuración global de Muse. En desarrollo requiere instalar los requisitos MCP en el Python usado para iniciar Bee-Muse, o indicar otro intérprete con `BEE_MCP_PYTHON`. El paquete de escritorio incorpora un ejecutable de herramientas independiente.

La conexión fue probada con un cliente MCP externo y con Muse consultando un catálogo sintético. INBEEBOX respondió a la consulta local de salud durante esta sesión. No se enviaron mensajes de prueba a los agentes.

## BeeCode

El adaptador de ejecución de BeeCode queda pendiente de recuperar y verificar el fork de OpenCode correcto. No se conecta la variante basada en Crush ni la app Android que ocupa actualmente su repositorio histórico.

Implementación basada en el [SDK oficial de MCP para Python](https://github.com/modelcontextprotocol/python-sdk), fijado en la línea 1.30.0.
