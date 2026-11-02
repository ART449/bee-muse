# Android

El servicio utiliza Python estándar y puede ejecutarse localmente en Android mediante Termux. Es una forma de probar el núcleo; todavía no es un APK nativo.

1. Instala Python y Git en Termux.
2. Clona este repositorio con tu acceso privado.
3. Ejecuta `python run.py --port 8767`.
4. Abre `http://127.0.0.1:8767/muse` en el navegador del mismo dispositivo.
5. Si necesitas indexar almacenamiento compartido, concede ese acceso a Termux y elige las carpetas en Bee-Muse.

La biblioteca y la interfaz no requieren Muse para abrirse. Para conversación, código y transcripción hace falta un ejecutor Muse compatible y autenticado en ese entorno. Su disponibilidad en Android no se ha verificado. No se distribuye una sesión ni claves del propietario.

Pendiente: cliente Android nativo, conexión autenticada a un ejecutor de escritorio y pruebas reales en dispositivo. El servidor actual es local; no debe exponerse a internet ni desactivarse su control de origen para conectar el teléfono.
