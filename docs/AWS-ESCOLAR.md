# Configuración escolar AWS

Frontend y backend publicados en https://0qx6ww77nl.execute-api.us-east-2.amazonaws.com/demo/.

El sitio usa API Gateway y Lambda para HTTPS y archivos Angular. CloudFront fue rechazado porque la cuenta requiere verificación; la web funciona sin ese servicio. Cognito Lite gestiona registro, confirmación de correo, login y recuperación de contraseña. Los comprobantes son privados por usuario y se guardan en DynamoDB; XML/PDF en S3 privado.

## Consumo

- Tres Lambda Java 17 de 512 MB, timeout 30 segundos, sin concurrencia aprovisionada.
- API con throttling 1 solicitud/s por método y ráfaga 25. La cuota antigua por clave no limita las rutas con JWT.
- DynamoDB bajo demanda con stream, sin PITR; SQS/DLQ con procesador máximo de dos ejecuciones concurrentes.
- S3 cifrado SSE-S3 y enlaces firmados de cinco minutos para archivos.
- Logs CloudWatch por tres días. Sin EC2, RDS, NAT, balanceadores ni dominio de pago.

No se garantiza costo cero; las cuotas son de mejor esfuerzo y no constituyen un corte absoluto del gasto. No se cambió el plan de facturación.

## Código y despliegue

Plantilla operativa: `infra/template-web-api-auth.json`. Recompilar con `scripts/build-web-api.ps1`. Para pruebas usar `scripts/verify-public-web.mjs`. Consulta `ESTADO-DESPLIEGUE-AWS.md`, `AUTENTICACION.md` y `VERIFICACION.md`.

Las plantillas CloudFront y el intento fallido se conservan para diagnóstico, no como alojamiento activo. La configuración privada queda fuera de Git y del ZIP.

Referencias:
- [Nivel gratuito](https://aws.amazon.com/free/free-tier-faqs/)
- [Cuotas de Lambda](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [Cognito y su modelo de autorización](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication-flows-public-server-side.html)
