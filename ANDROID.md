# Android · cliente nativo

El cliente está en `android/`. GitHub Actions genera el artefacto **Bee-Muse-Android-debug** con el APK.

## Ampliación 0.5 · asistente, control y navegador

La aplicación incorpora una pantalla **Asistente y control del teléfono**:

- Abre aplicaciones por el nombre exacto que muestra su lanzador. Acepta órdenes escritas y dictadas con el reconocimiento del teléfono.
- Ejecuta pulsaciones por texto visible único o coordenadas en píxeles del dispositivo, pulsación prolongada, arrastre completo, desplazamientos cortos, atrás e inicio mediante un servicio de accesibilidad. No traduce coordenadas del navegador.
- El servicio verifica que volvió a la aplicación prevista y que el equipo está desbloqueado. Las pantallas de contraseñas, permisos, ajustes e instalación requieren interacción directa del propietario. No se reciben órdenes por red ni desde páginas web.
- Permite solicitar el rol de asistente predeterminado. Incluye servicio y sesión de interacción de voz, con delegación explícita a un reconocedor del sistema diferente de Bee-Muse. La invocación se hace mediante el mecanismo de asistente de Android; no incluye una palabra de activación ni escucha continua.
- Avisos hablados opcionales para aplicaciones elegidas. Se omiten con el teléfono bloqueado, no se lee el cuerpo del mensaje y sólo se anuncia remitente si se habilita esa opción y Android lo identifica. No se envían notificaciones al modelo ni al servidor. Puede anunciar que Android está solicitando un permiso; la decisión permanece en la pantalla del sistema.
- Solicita el desbloqueo a Android; no sustituye ni evita PIN, huella o reconocimiento facial.
- Navegador HTTPS integrado, con dirección, atrás, adelante y recarga. No expone archivos, terminal, control del teléfono ni credenciales del cliente nativo al contenido web. No tiene aún un adaptador de navegación para agentes.

Los accesos a accesibilidad y notificaciones se habilitan y revocan desde Ajustes. Los avisos están desactivados y su lista de aplicaciones está vacía al instalar. La voz actual sigue siendo la del teléfono.

Ejemplos de órdenes: `abre WhatsApp`, `baja`, `sube`, `atrás`, `inicio`, `pulsa Buscar`, `pulsa 400 800`, `mantén pulsado 400 800`, `arrastra 400 800 a 400 500`. Al dictar se intenta ejecutar la orden reconocida; las frases no admitidas no producen gestos.

El registro local conserva las últimas 50 acciones con dispositivo, sesión y evento. La recepción de un comando, la aceptación de un gesto por Android y la comprobación de su efecto son estados distintos: el registro no afirma que el contenido de otra aplicación haya cambiado sólo porque Android completó el gesto.

Estas ampliaciones requieren compilación y uso físico en el Pixel; no se presentan todavía como validadas en ese dispositivo.

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
