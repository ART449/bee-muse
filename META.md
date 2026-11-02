# Bee-Muse · configuración de Meta

## Registro confirmado el 2 de noviembre de 2026

- Aplicación: **Bee-Muse**.
- App ID público: `1747909204005226`.
- [Panel de Meta for Developers](https://developers.facebook.com/apps/1747909204005226/).
- Modo: desarrollo. El registro se realizó después de que Art aceptó expresamente los términos de Meta y se comprobó con una lectura posterior del MCP oficial.
- Propietario: portfolio **IArtLabs**, ID `1042930465579250`. La vinculación permanente fue autorizada expresamente por Art, aplicada y comprobada mediante una nueva lista de aplicaciones.
- Caso de uso `FB_LOGIN`: agregado después de la autorización expresa de Art y confirmado mediante una nueva lectura de los casos configurados.
- Retornos OAuth: la lectura de ajustes avanzados todavía devuelve `oauth_redirect_uris: null`. El registro y el caso de uso no completan ese ajuste.

El ID de aplicación es público. El secreto de la aplicación no se obtiene mediante este MCP ni debe incluirse en código, artefactos, capturas, mensajes o historial Git.

## Conexión con Firebase

La aplicación utiliza Firebase Authentication para verificar las identidades. En el equipo original, la configuración pública existente corresponde al proyecto `byflow-d3a0f`; el archivo `firebase-web.json` está excluido del repositorio. No se ha modificado la configuración de ese proyecto compartido.

Datos concretos para el proveedor Facebook:

| Campo | Valor |
| --- | --- |
| Facebook App ID | `1747909204005226` |
| Dominio de autenticación existente | `byflow-d3a0f.firebaseapp.com` |
| URI de retorno OAuth de Firebase | `https://byflow-d3a0f.firebaseapp.com/__/auth/handler` |
| Caso de uso de Meta | `FB_LOGIN` |

Antes de modificar el proveedor del proyecto compartido, comprobar si ya sirve a otra aplicación. No reemplazar un proveedor existente sin revisar su uso. El secreto de Meta se introduce directamente en la configuración protegida del proveedor Facebook de Firebase; nunca en el cliente de Bee-Muse.

El MCP actual permite crear la aplicación, consultar ajustes y gestionar casos de uso y portfolio. No ofrece escritura de los retornos OAuth ni entrega el secreto. Esos ajustes requieren el panel de Meta y la configuración protegida de Firebase. La [guía oficial de Firebase](https://firebase.google.com/docs/auth/web/facebook-login) describe el App ID, el secreto y el retorno necesarios.

## Qué constituye una comprobación completa

1. Conservar el propietario IArtLabs y el caso de uso `FB_LOGIN`, ya confirmados en Meta.
2. Comprobar el retorno OAuth y el proveedor Facebook habilitado en Firebase.
3. Entrar desde Bee-Muse con Facebook y comprobar que el servidor verifica un ID token de ese proveedor.
4. Cerrar la sesión y comprobar que ya no aparece autenticada.

El registro de la aplicación y el botón visible no certifican todavía el recorrido de acceso. Muse conserva su propia autorización, separada de esta identidad. La ronda completa de pruebas se hará después de terminar las integraciones, según lo solicitado por Art.
