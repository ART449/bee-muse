# Android · cliente nativo

El cliente está en `android/`. GitHub Actions genera el artefacto **Bee-Muse-Android-debug** con el APK.

Incluye selector de carpeta Android sin permisos globales, filtro por extensión (hasta 5000 entradas por recorrido), apertura de archivos, chat con el servidor de Muse, animaciones y dictado/lectura mediante los servicios del teléfono. Las voces del teléfono no se presentan como modelos Meta.

El acceso al servidor usa HTTPS y un código de emparejamiento de un solo uso, válido cinco minutos. La sesión dura ocho horas y se conserva sólo en memoria del cliente.

## Conectar

Inicia el servicio con `python run.py --port 8767`. Con un certificado TLS propio válido, inicia `python service/remote_gateway.py --backend http://127.0.0.1:8767 --bind 0.0.0.0 --port 9443 --cert certificado.pem --key clave.pem`, indicando tus archivos de certificado. Mantén el servicio en tu red privada autorizada. Escribe en Android la dirección HTTPS y el código impreso por el gateway. No desactives la validación TLS.

Elige el proyecto de trabajo desde el equipo principal antes de pedir cambios. Los archivos del teléfono se consultan localmente: no se suben automáticamente y el agente no ejecuta terminal dentro de Android.

Para compilar: JDK 17, Gradle 8.11.1 y SDK 35; ejecutar `gradle assembleDebug` dentro de `android/`. La automatización genera el APK sin claves privadas del propietario. Compilación y prueba de uso en dispositivo se registran por separado.

## Alternativa anterior: núcleo en Termux

El servicio utiliza Python estándar y puede ejecutarse localmente en Android mediante Termux. Es una forma de probar el núcleo; todavía no es un APK nativo.

1. Instala Python y Git en Termux.
2. Clona este repositorio con tu acceso privado.
3. Ejecuta `python run.py --port 8767`.
4. Abre `http://127.0.0.1:8767/muse` en el navegador del mismo dispositivo.
5. Si necesitas indexar almacenamiento compartido, concede ese acceso a Termux y elige las carpetas en Bee-Muse.

La biblioteca y la interfaz no requieren Muse para abrirse. Para conversación, código y transcripción hace falta un ejecutor Muse compatible y autenticado en ese entorno. Su disponibilidad en Android no se ha verificado. No se distribuye una sesión ni claves del propietario.

El cliente nativo y el gateway sustituyen el pendiente de conexión remota. El servidor principal sigue en loopback; no desactives sus controles de origen. Las pruebas completas en dispositivo se realizarán después de cerrar las integraciones, según la instrucción de Art.
