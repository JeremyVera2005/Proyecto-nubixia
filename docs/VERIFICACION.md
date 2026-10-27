# Verificación de la implementación

## Versión pública con Cognito, 26 de octubre de 2026

URL: https://0qx6ww77nl.execute-api.us-east-2.amazonaws.com/demo/

- Backend: 21 pruebas aprobadas. Incluyen aislamiento por propietario, rechazo de headers que intentan suplantar al usuario, IDs separados entre cuentas, conservación de owner durante el procesamiento y lista permitida de archivos públicos.
- Frontend: 12 pruebas aprobadas. Incluyen conexión, validación monetaria, duplicados, reintentos, login Cognito, renovación concurrente de sesión, limpieza de sesión vencida y rechazo de registros fallidos sin simular éxito.
- Angular compilado para /demo/ y empaquetado dentro del JAR Lambda. CSP sin scripts inline; inlineCritical desactivado para cargar la hoja de estilos completa.
- HTTP real: landing pública 200, JavaScript y PNG correctos, nosniff/CSP, config.json sin API key.
- API sin sesión o con token inventado: 401.
- Cognito real: login incorrecto devuelve NotAuthorizedException; registro con contraseña inválida devuelve InvalidPasswordException. No se crearon cuentas ni enviaron correos de prueba.
- Se revisaron en navegador landing, registro y login publicados. Las pantallas públicas no permiten entrar al panel de demostración local.

Reporte reproducible: `node scripts/verify-public-web.mjs`. Evidencia: `evidencias/aws-web-publica.json`. Una cuenta válida y la recepción de su código de confirmación debe comprobarlas el propietario de ese correo.

## Evidencia histórica del backend anterior

Antes de Cognito, H2 recibió 20 solicitudes simultáneas, todas aceptadas, con recepción de 44 a 59 ms. En AWS pasó el flujo completo de 20 comprobantes con concurrencia 2, recepción 192–546 ms y procesamiento 230–1032 ms, más validación, idempotencia y XML/PDF. Reporte: `evidencias/aws-flujo-escolar.json`.

Las pruebas AWS de 20 simultáneas sin reintentos no pasaron. Reportes: `aws-arranque-frio.json` y `aws-rafaga-20.json`. No confundirlos con la prueba funcional de concurrencia 2 ni con una prueba del acceso autenticado actual.

`scripts/verify.mjs` conserva la prueba histórica por API key para el backend local. En AWS esa clave ya no sustituye una sesión Cognito. Para validar la aplicación publicada usar verify-public-web.mjs y una cuenta propia confirmada.
