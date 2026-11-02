# Bee-Muse · plan de continuidad acordado

Revisado el 2 de noviembre de 2026 contra la conversación, el código y la entrega 0.5.0. Muse es el cerebro principal; Bee-Muse reúne herramientas propias reutilizables por otros agentes. Conservar español para Art y añadir inglés para evaluación. La interfaz, las órdenes locales y las voces configuradas todavía están en español.

## Orden de ejecución

1. **Confirmar la entrega e incorporar español/inglés.** Verificar las bases específicas y el material solicitado al participante. Extraer textos de escritorio, web y Android; selector persistente y detección inicial del idioma; adaptar órdenes y voces al idioma elegido. Criterio: completar el mismo recorrido en ambos idiomas sin perder la elección de Art. La exigencia de interfaz inglesa no está confirmada en las páginas públicas consultadas.
2. **Cerrar el recorrido entre Muse y las herramientas.** Unir Muse, el índice, el navegador, las acciones Android e INBEEBOX con permisos por herramienta, identidad de tarea/sesión/dispositivo/evento y resultados verificables. Criterio: una instrucción produce la acción autorizada en el dispositivo correcto y devuelve su resultado; registrar un comando o aceptar un gesto no basta para afirmar que funcionó.
3. **Recuperar e integrar el BeeCode correcto.** Su base es OpenCode. Apartar las variantes de Crush y la app Android contaminada, conservando su historial; no reemplazar repositorios por el nombre ni mezclar proyectos. Criterio: fuente correcta identificada, versionada, ejecutable y conectada como herramienta de código, manteniendo Muse como cerebro para el hackatón.
4. **Terminar Facebook y la conexión segura del teléfono.** La app Meta ya existe, pertenece a IArtLabs y tiene Facebook Login. Falta retorno OAuth, proveedor Firebase y acceso real. Las sesiones de Firebase/Google Cloud están disponibles; no pedir otra vez contraseñas ni guardar secretos en el chat. Verificar el certificado y emparejamiento HTTPS con el Pixel. Criterio: entrar, salir y conectar el teléfono de principio a fin.
5. **Completar la biblioteca y la comprensión de contenido.** Mantener búsqueda por extensión para cualquier tipo, previsualización, organización, colecciones y versiones. Resolver continuidad y actualización del índice para bibliotecas grandes. Añadir la comprensión de imágenes/SAM prevista: ver una miniatura no equivale a identificar su contenido. Criterio: encontrar el archivo correcto, previsualizarlo, elegir versión y organizar una colección sin navegar carpeta por carpeta.
6. **Ejecutar la ronda completa de pruebas después de integrar.** Pixel: abrir app, pulsar, arrastrar, desplazarse poco, revocar accesos, asistente, avisos por aplicación, bloqueo/desbloqueo delegado a Android, micrófono y respuestas habladas. Luego Windows, Linux y Mac, instalación, actualización y conservación de biblioteca/historial. Criterio: evidencia observada del recorrido completo; compilación y pruebas unitarias se registran aparte.
7. **Preparar y ensayar la demostración.** Guion y explicación en inglés, con español disponible; problema concreto, recorrido reproducible, herramientas propias y papel real de Meta. Medir una tarea con usuarios y conservar resultados reales. Verificar envío/inscripción y requisitos del evento; no presentar integraciones pendientes como demostradas.

## Lo que ya está comprobado

- Entrega 0.5.0 con Windows x64, Linux x64, Mac Apple Silicon y APK Android nativo. Código privado versionado y subido.
- 18 pruebas del servicio y cinco casos de órdenes Android aprobados; compilaciones de las cuatro plataformas aprobadas.
- Muse creó un archivo y resolvió un cálculo; un cliente externo y Muse consultaron el índice mediante MCP.
- Navegador de escritorio: navegación HTTPS y separación del contenido remoto respecto a las herramientas locales verificadas en Windows.
- Transcripción real de un WAV sintético por Meta, también desde el backend Windows compilado. Micrófono real pendiente. La salida hablada utiliza el sistema, no TTS de Meta.
- Nueve animaciones de CyberBee/OctoHype asociadas a estados. Organización, copias y versiones tienen implementación; falta su recorrido completo de uso.

## Huecos que no deben desaparecer del plan

- El control Android actual acepta órdenes locales explícitas; su conexión con los agentes y MCP todavía falta. El navegador propio tampoco tiene aún el adaptador de control para agentes.
- INBEEBOX ofrece consultas y tiene salud local comprobada; no está demostrado el circuito completo de mensajes, tareas y ejecución entre agentes.
- La búsqueda actual usa nombres, rutas, tipos y fechas. No hay integración verificada de SAM/OCR/comprensión visual.
- Índice general de escritorio: recorridos acotados a 10 000 archivos o 12 segundos, con estado parcial. Android: hasta 5 000 entradas por recorrido. La interfaz general pide entrar a subcarpetas cuando el índice es parcial; falta continuidad para cumplir la intención de evitar esa búsqueda manual.
- Asistente Android registrado en código; falta comprobar la selección e invocación en el Pixel. No hay palabra de activación ni escucha continua. Android conserva la autenticación para desbloquear y la decisión sobre permisos.
- Avisos hablados opcionales, por aplicaciones elegidas; no se envía su contenido a Muse ni se lee el cuerpo del mensaje. No se anuncian con el teléfono bloqueado.
- Jules es una consulta opcional por verificar. Las fichas de Drive, GitHub, GitBee/Gitea, Railway, Cloudflare, Beatscale y proveedores adicionales son planificación de conectores; no equivalen a integraciones activas. No ampliar esos frentes sin relación con el recorrido acordado.
- La aplicación que seguía abierta era el portable antiguo. Cerrar esa ventana antes de comprobar la entrega nueva; conservar perfil, historial y catálogo.

## Fuente y almacenamiento

- Código: repositorio privado ART449/bee-muse; consultar HANDOFF.md y VALIDATION.md al retomar.
- Entrega y archivos grandes: I:\Bee-Muse\2026-11-02. En C: permanecen el código y enlaces a compilaciones, herramientas y paquetes trasladados con comprobación SHA-256. Mantener I: disponible.
- Entrega nueva: outputs/Bee-Muse-0.5.0, enlazada a I:\Bee-Muse\2026-11-02\release-0.5.0. LEEME.txt, release-validation.json y compiled-voice-proof.json acompañan los paquetes.
- Las páginas públicas del evento consultadas indican entrega el 4 de noviembre; confirmar las bases específicas del participante antes del envío.
