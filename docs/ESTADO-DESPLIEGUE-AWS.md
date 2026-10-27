# Estado real del despliegue AWS

Actualizado el 26 de octubre de 2026, America/Lima.

## Aplicación pública

https://0qx6ww77nl.execute-api.us-east-2.amazonaws.com/demo/

Frontend Angular y backend Java funcionan en AWS. No dependen de localhost ni de mantener esta computadora encendida. La pila operativa es `nubixia-escolar-demo`, región `us-east-2` (Ohio). La actualización con web y Cognito terminó en UPDATE_COMPLETE a las 00:28:10. El ajuste final de estilos quedó en UPDATE_COMPLETE a las 00:36:46 (versión API 2.0.1).

Incluye landing, logo nuevo, registro, confirmación de correo, login/logout, recuperación de contraseña y panel de comprobantes por usuario. La web y sus archivos se sirven por API Gateway y Lambda. DynamoDB, Streams, SQS/DLQ y S3 privado conservan el procesamiento asíncrono y las descargas firmadas.

Recursos de datos existentes:
- DynamoDB: `nubixia-escolar-demo-Documents-1A3Z7IFFHFLVT`.
- S3: `nubixia-escolar-demo-artifacts-gob4zuovhsec`.
- Artefactos de despliegue: `nubixia-escolar-deploy-002333107613-use2`.
- Cognito Lite: `us-east-2_kJ2s3wLov`.
- Cliente público Cognito: `4rl61388qgi2k1h5vfbmskhp0l`, sin secreto.

Plantilla operativa: `infra/template-web-api-auth.json`. Los parámetros privados quedan en `.env.aws.json`, fuera de Git y del ZIP. El sitio público recibe únicamente IDs públicos de Cognito; no recibe la clave compartida anterior.

## Protección

API Gateway valida los ID tokens Cognito. Lambda obtiene el sub del authorizer y filtra todos los comprobantes por propietario. Los identificadores también incluyen ese usuario para evitar colisiones entre cuentas. Los registros de prueba anteriores, sin propietario, se conservan pero no se muestran a las cuentas nuevas.

El registro exige confirmar un código por correo. La primera cuenta y la recepción de su correo debe comprobarlas el usuario; no se crearon cuentas reales ni se enviaron mensajes a terceros durante las pruebas automatizadas.

## CloudFront y alternativas

La pila `nubixia-escolar-web` se intentó con CloudFront y S3 privado. AWS rechazó Distribution con 403: la cuenta debe verificarse antes de crear nuevos recursos CloudFront. La pila se revirtió y conservó su UserPool según DeletionPolicy Retain. Se reutilizó ese pool en el backend existente, creando el cliente Cognito dentro de la pila operativa.

No se contactó a Soporte ni se modificó el plan de facturación. La publicación HTTPS final usa API Gateway/Lambda y no requiere CloudFront. La política autorizada `NubixiaSchoolDeploymentRolePolicy` se actualizó a versión 2 con los permisos aprobados de Cognito y CloudFront; no se añadieron permisos de administración de usuarios finales.

## Verificación

- 21 pruebas Java y 12 del frontend aprobadas.
- Web pública 200, bundle JS y logo PNG correctos, cabeceras de seguridad y configuración pública sin secretos.
- Datos sin sesión o con token inventado: 401.
- Cognito real rechaza credenciales incorrectas y contraseñas inválidas. Sin cuentas ni correos de prueba creados.
- Evidencia: `evidencias/aws-web-publica.json`, `nubixia-web-publicada.jpg` y `nubixia-registro-publicado.jpg`.

La prueba anterior a la autenticación aceptó 20 comprobantes con concurrencia 2. Las ráfagas de 20 simultáneos sin reintentos tuvieron rechazos; no se acredita ese objetivo en esta cuenta. Se conservan los reportes históricos y no se presentan como prueba del flujo autenticado actual.

## Consumo

Lambda bajo demanda de 512 MB, sin concurrencia aprovisionada; DynamoDB bajo demanda; procesador SQS máximo 2; logs 3 días. API conserva throttling de 1 solicitud/s por método y ráfaga 25. La cuota anterior de 500/día por API key no aplica a las rutas nuevas basadas solo en JWT. No existe un corte absoluto de gasto ni se garantiza costo cero. No se crearon EC2, RDS, NAT Gateway ni balanceadores.
