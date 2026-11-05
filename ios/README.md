# iOS · cliente mínimo

Aplicación SwiftUI (iOS 16+, `com.iartlabs.beemuse.ios`) con un `WKWebView` que abre la dirección HTTPS del gateway remoto de Bee-Muse (`service/remote_gateway.py`). Cumple el mismo papel que el navegador integrado del cliente Android, sin el resto de funciones de ese cliente: no hay asistente, control del teléfono, selector de carpetas ni dictado.

## Qué hace

- Barra superior con la dirección, botón **Conectar**, atrás y recargar.
- Sólo acepta `https://` con host y sin `usuario:contraseña`. Las direcciones `http://` se rechazan antes de cargar y durante la navegación, igual que en Android.
- Recuerda la última dirección en `UserDefaults`. No guarda el código de emparejamiento ni la sesión: se escriben en la página del gateway y viven sólo en el contenido web.
- `NSAppTransportSecurity` queda con `NSAllowsArbitraryLoads: false`. No hay excepción de TLS ni certificados autofirmados; el gateway necesita un certificado válido, como indica `ANDROID.md` (sección Conectar).
- Sin puentes JavaScript, sin acceso a archivos locales y sin controladores de mensajes.

## Conectar

Igual que en Android: inicia `python run.py --port 8767`, luego `python service/remote_gateway.py --backend http://127.0.0.1:8767 --bind 0.0.0.0 --port 9443 --cert certificado.pem --key clave.pem`, y escribe en la app la dirección HTTPS y el código impreso por el gateway. Mantén el servicio en tu red privada autorizada.

## Compilar

No hay Mac en el equipo de desarrollo. El proyecto Xcode se genera con [XcodeGen](https://github.com/yonaskolb/XcodeGen) a partir de `project.yml`; `Info.plist` y `Bee-Muse.xcodeproj` son archivos generados, no fuente.

```
brew install xcodegen
xcodegen generate --spec ios/project.yml
xcodebuild -project ios/Bee-Muse.xcodeproj -scheme Bee-Muse -sdk iphonesimulator \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath ios/build CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO build
```

El flujo `.github/workflows/ios.yml` ejecuta esos pasos en `macos-latest` y publica el artefacto **Bee-Muse-iOS-simulator** (`Bee-Muse.app` para simulador, sin firma).

## Qué NO está verificado

- Nadie ha ejecutado esta aplicación en un iPhone ni en un simulador. La única comprobación prevista es que compile en GitHub Actions.
- No existe firma ni perfil de aprovisionamiento; el artefacto no se instala en dispositivos físicos.
- La compatibilidad de la interfaz web de Bee-Muse con WebKit móvil no se ha probado.
