# Plataformas de Bee-Muse

Qué se compila, dónde y qué queda verificado en cada combinación. La integración continua está en `.github/workflows/desktop.yml` (escritorio) y `.github/workflows/android.yml` (Android); ambas se disparan en `main`, en ramas `feat/ports-**` y de forma manual.

## Escritorio

| Plataforma | Arquitectura | Runner de CI | Cómo se construye | Verificado en CI | NO verificado |
|---|---|---|---|---|---|
| Linux | x64 | `ubuntu-latest` | PyInstaller (`scripts/build_desktop.py`) + Electron (`desktop/package.cjs`) + `scripts/archive_desktop.py` → `Bee-Muse-<ver>-Linux-x64.tar.gz` | Pruebas unitarias, compilación del backend, arranque del binario y `/health`, empaquetado Electron | Uso humano del paquete en un equipo real |
| Linux | arm64 | `ubuntu-24.04-arm` | Igual → `Bee-Muse-<ver>-Linux-arm64.tar.gz` | Ídem | Uso humano del paquete |
| Windows | x64 | `windows-latest` | Igual → `Bee-Muse-<ver>-Windows-x64.zip` (incluye `Instalar-Bee-Muse.cmd`) | Ídem | Uso humano del paquete; firma de código |
| Windows | arm64 | `windows-11-arm` | Igual → `Bee-Muse-<ver>-Windows-arm64.zip` | Ídem | Uso humano del paquete. `imageio-ffmpeg` no publica rueda `win_arm64`: la transcripción de voz necesita un `ffmpeg` del sistema en `PATH` |
| macOS | arm64 (Apple Silicon) | `macos-latest` | Igual → `Bee-Muse-<ver>-macOS-arm64.tar.gz` | Ídem | Uso humano del paquete; firma y notarización |
| macOS | x64 (Intel) | `macos-15-intel` | Igual → `Bee-Muse-<ver>-macOS-x64.tar.gz` | Ídem | Uso humano del paquete; firma y notarización |

Qué significa cada columna:

- **Verificado en CI**: `python -m unittest discover -s tests`, compilación del backend con PyInstaller, `scripts/smoke_backend.py` (arranca `desktop/backend/bee-muse-service` con `--port 0` sobre una copia de `desktop/library-template`, comprueba que anuncia `http://127.0.0.1:<puerto>` y que `/health` responde JSON con `app`), empaquetado con `@electron/packager` y archivo portable con SHA-256.
- **NO verificado**: nadie ha abierto todavía la aplicación empaquetada en un equipo físico de esa plataforma y arquitectura. La ventana Electron, el navegador integrado, el diálogo de carpetas y la conversación real con Muse solo se han usado a mano en Windows x64.

Los artefactos de CI se llaman `Bee-Muse-<plataforma>-<arquitectura>` (por ejemplo `Bee-Muse-macos-x64`). La etiqueta de arquitectura la calcula `scripts/archive_desktop.py` con `platform.machine()`: `ARM64` (Windows), `arm64` (macOS) y `aarch64` (Linux) se normalizan a `arm64`; todo lo demás es `x64`.

## Ejecutar desde el código en Linux y macOS

Requiere Python 3.11 o posterior. Desde la raíz del repositorio:

```sh
python3 -m pip install -r requirements-mcp.txt -r requirements-voice.txt
sh start-unix.sh
```

`start-unix.sh` equivale a `python3 run.py --open`: levanta el servicio local en `127.0.0.1` y abre la biblioteca en el navegador. En Windows se usa `START-WINDOWS.cmd`.

### Muse Code debe estar instalado e iniciado en ese equipo

Bee-Muse no incluye Muse ni ninguna sesión. `service/muse_bridge.py` busca el ejecutable en este orden:

1. `BEE_MUSE_EXECUTABLE` (ruta absoluta al binario, si se define).
2. En Windows, `%LOCALAPPDATA%\Programs\muse\muse-bin-*.exe`.
3. `muse` en `PATH`.
4. `~/.local/bin/muse`, `/usr/local/bin/muse`, `/opt/homebrew/bin/muse`.

Si no lo encuentra, la conversación y las herramientas reportan Muse como no disponible. Inicia sesión en Muse Code con tu propia cuenta antes de usar Bee-Muse.

## Móvil

- **Android**: cliente nativo en `android/`; CI (`android.yml`, `ubuntu-latest`) ejecuta las pruebas unitarias y genera el APK de depuración como artefacto `Bee-Muse-Android-debug`. No verificado en dispositivo; consulta `ANDROID.md`.
- **iOS**: proyecto en `ios/`; CI solo compila para el simulador (`ios.yml`). Sin firma, sin TestFlight y sin uso en dispositivo.
