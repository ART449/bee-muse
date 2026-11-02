# Bee-Muse · IArtLabs

Herramientas locales para inteligencia artificial, con Muse como cerebro: conversación, biblioteca de archivos y ejecución en una carpeta de trabajo elegida.

Este repositorio contiene Bee-Muse de escritorio y su servicio. Es distinto de BeeCode, de las variantes basadas en Crush y del experimento Bee-Muse Android.

## Ejecutar desde código

Requiere Python 3.11 o posterior. Desde la raíz:

```sh
python -m pip install -r requirements-mcp.txt -r requirements-voice.txt
python run.py --open
```

Instala Muse Code e inicia sesión con tu propia cuenta para conversar, ejecutar herramientas o intentar el dictado de Meta. No se distribuyen sesiones del propietario. El selector de carpeta del proyecto delimita el espacio de trabajo. Muse conserva sus controles de aprobación y ejecución.

La primera apertura crea una biblioteca vacía en los datos de la aplicación. Puedes indexar tus carpetas desde la interfaz. En un equipo con una biblioteca configurada, se reutiliza su ubicación y se conservan sus datos.

## Estado

- Windows: código recuperado de la aplicación existente. La nueva conexión con Muse creó un archivo real en una carpeta temporal y devolvió correctamente un cálculo solicitado.
- Linux y macOS: servicio Python portable y compilaciones configuradas en CI; pruebas de cada paquete pendientes.
- Android: cliente y pruebas pendientes. No se presenta Electron como un APK.
- INBEEBOX: herramientas MCP de consulta implementadas; salud local verificada.
- BeeCode: integración pendiente; no se sustituye el fork correcto por las variantes Android o Crush.

Conversación con historial, ejecución de herramientas y terminal, nueve animaciones de CyberBee/OctoHype asociadas a estados, proveedor Facebook preparado y controles de voz. Consulta [VALIDATION.md](VALIDATION.md) para distinguir lo probado de lo pendiente; especialmente dictado Meta, OAuth real y Android.

## Compilar escritorio

```sh
python -m pip install -r requirements-build.txt -r requirements-mcp.txt -r requirements-voice.txt
python scripts/build_desktop.py
cd desktop
npm ci
npm run package
```

La compilación se hace en cada sistema operativo. El resultado está en `desktop/ready/`. Los paquetes no están firmados ni notarizados. La matriz de GitHub Actions compila Windows, Linux y macOS y conserva sus artefactos.

Consulta [MCP.md](MCP.md) para conectar otras IA, y [ANDROID.md](ANDROID.md) para el estado de Android.

El repositorio no incluye catálogo personal, historial, cuentas ni credenciales. Muse Code requiere su propia instalación y sesión. Los modelos trabajan en la nube y pueden recibir el contenido necesario para las tareas solicitadas.

## Versionado

El primer commit conserva una base recuperada. Los cambios de conversación y herramientas se registran en commits posteriores. Las copias originales de trabajo se conservaron antes de editar.
