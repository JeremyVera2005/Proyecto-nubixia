# Nubixia — Plataforma académica de comprobantes

Aplicación completa con frontend Angular y backend Java 17 / Spring Boot. Recibe comprobantes ficticios, valida importes con IGV de 18%, procesa en segundo plano y genera XML y PDF consultables. Es una simulación académica; no emite comprobantes legales ni se conecta con SUNAT.

## Código y versionado

Repositorio: [JeremyVera2005/Proyecto-nubixia](https://github.com/JeremyVera2005/Proyecto-nubixia). El versionado del proyecto completo comienza con la línea base del 26 de octubre de 2026. Consulta el [flujo de trabajo Git](docs/VERSIONADO.md) y el [registro de cambios](CHANGELOG.md). Subir código a GitHub no despliega automáticamente en AWS.

## Sitio en AWS

Abre [Nubixia en AWS](https://0qx6ww77nl.execute-api.us-east-2.amazonaws.com/demo/).

Frontend y backend funcionan en AWS; no necesitas mantener esta computadora encendida. Incluye landing page, logo nuevo, registro, confirmación de correo, inicio/cierre de sesión y recuperación de contraseña con Cognito Lite. Cada usuario ve sus propios comprobantes. La base y los archivos siguen en DynamoDB y S3 privado.

La cuenta bloqueó CloudFront por verificación pendiente. Se publicó por HTTPS mediante API Gateway y Lambda. La plantilla operativa es `infra/template-web-api-auth.json`. Consulta [estado del despliegue](docs/ESTADO-DESPLIEGUE-AWS.md) y [autenticación](docs/AUTENTICACION.md).

## Iniciar en Windows para desarrollo local

La landing se abre primero. Para usar el backend local H2, elige Ingresar y luego Ver panel de demostración local. Ese acceso solo se muestra en localhost cuando no hay Cognito configurado. La web pública siempre exige una sesión real.

Requisitos: JDK 17 o superior y Node.js 24 con npm. Maven Wrapper descarga Maven y dependencias la primera vez. No necesitas AWS para probar la aplicación.

Desde esta carpeta, abre dos terminales PowerShell:

Terminal 1:
```powershell
.\scripts\start-backend.ps1
```

Terminal 2:
```powershell
.\scripts\start-frontend.ps1
```

Abre http://localhost:4200. Entra al panel de demostración local para conectar automáticamente con la API local. Usa estos valores solo si deseas revisar o cambiar la conexión:
- URL: `http://localhost:8080`
- API key local: `nubixia-demo-local-2026`

Pulsa Nuevo comprobante. Ejemplo: RUC 20123456789, cliente Demo, serie F001, número 1, cantidad 2 y precio 50. El total se calcula en S/ 118.00. El estado se actualiza cada 5 segundos. Abre Ver detalle para consultar el historial y descargar archivos.

Si PowerShell bloquea scripts, ejecuta directamente en cada carpeta:
```powershell
# En comprobantes-serverless (configura JAVA_HOME con tu JDK)
.\mvnw.cmd spring-boot:run
# En comprobastes-serverless-frontend
npm.cmd ci
npm.cmd start
```

Las variables de .env.example son una referencia; no se cargan automáticamente. Puedes cambiar la clave antes de iniciar el backend:
```powershell
$env:NUBIXIA_API_KEY = 'TuClaveLocalPersonal'
$env:NUBIXIA_CORS_ORIGIN = 'http://localhost:4200'
```

## Comportamiento y persistencia

- Local: base SQL H2 persistente en `comprobantes-serverless/data/nubixia.mv.db`, con tablas de comprobantes, ítems, historial y archivos XML/PDF. Flyway crea el esquema; se importan automáticamente los JSON anteriores. Cuatro trabajadores recuperan pendientes desde SQL. Consulta [acceso y consultas SQL](docs/BASE-DE-DATOS.md).
- AWS: API Gateway, tres Lambda, DynamoDB bajo demanda con Streams, SQS con DLQ, S3 privado, CloudWatch e IAM.
- Flujo: RECIBIDO → PROCESANDO → ACEPTADO. Datos inválidos en recepción devuelven 400 sin crear registro. RECHAZADO se reserva para datos inválidos detectados en procesamiento. Fallos técnicos se registran como ERROR y se reintentan.
- Identidad del comprobante: RUC + serie + número normalizado. El mismo contenido devuelve el original con `duplicado: true`; cambiar el contenido manteniendo esa identidad produce 409.
- Los archivos usan una ruta estable por documentId. Las escrituras se pueden repetir al reintentar un fallo, pero no crean nuevos comprobantes ni nuevas rutas de archivo.
- Los importes usan BigDecimal en Java y redondeo HALF_UP a 2 decimales por línea, luego IGV sobre subtotal. Se admite PEN únicamente.
- Máximo 100 ítems, descripción/cliente de 200 caracteres, cantidad positiva con 3 decimales y precio no negativo con 2. RUC: formato básico de 11 dígitos. Serie F/B seguida de tres caracteres alfanuméricos, número 1–99999999.
- El frontend conecta automáticamente en localhost con la clave pública de demostración. Si el backend está temporalmente apagado, reintenta cada 5 segundos. Para otra API o una clave personalizada, usa Conexión API; esos valores se conservan en sessionStorage. La clave local no se usa automáticamente con servidores remotos. Configura autoConnectLocal=false en public/config.json para desactivar este comportamiento.
- En local existe un espacio de demostración compartido por clave. En AWS hay cuentas Cognito y aislamiento por usuario; los registros antiguos compartidos no se muestran a las cuentas nuevas.

## API REST

En local, las rutas de datos requieren `X-API-Key`. En la web AWS requieren el ID token de Cognito en `Authorization`; /health, la landing y sus archivos son públicos.

| Método | Ruta | Resultado |
|---|---|---|
| GET | /health | Estado del servicio |
| POST | /comprobantes | 202 nuevo / 200 duplicado, documentId e historial |
| GET | /comprobantes | Objeto con array items, ordenado por creación descendente |
| GET | /comprobantes/{id} | Datos, estado, error e historial |
| GET | /comprobantes/{id}/archivos/xml | XML local; en AWS JSON con URL firmada |
| GET | /comprobantes/{id}/archivos/pdf | PDF local; en AWS JSON con URL firmada |

En AWS las URLs de descarga vencen a los 5 minutos. El frontend obtiene el archivo sin reenviar la API key a S3. Antes de ACEPTADO las descargas devuelven 409. Un ID inexistente devuelve 404; JSON incorrecto o datos inválidos, 400. Los errores técnicos devuelven un requestId para localizar logs.

Ejemplo PowerShell:
```powershell
$headers = @{ 'X-API-Key' = 'nubixia-demo-local-2026' }
$body = Get-Content .\docs\ejemplo-comprobante.json -Raw
$r = Invoke-RestMethod http://localhost:8080/comprobantes -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
Invoke-RestMethod ("http://localhost:8080/comprobantes/" + $r.documentId) -Headers $headers
```

## Pruebas y paquetes

```powershell
# Backend, desde comprobantes-serverless
.\mvnw.cmd test
.\mvnw.cmd package
# Frontend, desde comprobastes-serverless-frontend
npm.cmd test -- --watch=false
npm.cmd run build
# Prueba HTTP con ambos servicios disponibles, desde la raíz
node .\scripts\verify.mjs
```

El verificador crea 20 comprobantes ficticios F999 con números aleatorios y guarda evidencia en `evidencias/ultima-prueba.json`. Comprueba concurrencia real HTTP, autenticación, importes, tiempos, duplicados y descargas. Cada ejecución conserva sus comprobantes para poder consultarlos.

Para probar una API remota:
```powershell
$env:API_URL = 'https://TU-API.execute-api.us-east-1.amazonaws.com/demo'
$env:NUBIXIA_API_KEY = 'TuClaveAWS'
node .\scripts\verify.mjs
```

Paquetes producidos:
- `comprobantes-serverless/target/comprobantes-serverless-1.0.0-app.jar`: ejecutable local con `java -jar`.
- `comprobantes-serverless/target/comprobantes-serverless-1.0.0-lambda.jar`: clases y dependencias para AWS Lambda.
- `comprobastes-serverless-frontend/dist/nubixia-web/browser/`: frontend estático compilado.

## Despliegue AWS

El código de infraestructura está en `infra/template.yaml`. No se ha desplegado en una cuenta AWS durante esta implementación. Requiere AWS CLI, AWS SAM CLI, credenciales y permisos para CloudFormation, IAM, API Gateway, Lambda, DynamoDB, SQS, S3 y CloudWatch.

1. Compila con `mvnw.cmd package` desde backend.
2. Desde la raíz valida y despliega el JAR ya compilado:
```powershell
sam validate --lint --template-file infra/template.yaml
sam deploy --guided --template-file infra/template.yaml --capabilities CAPABILITY_IAM
```
3. Durante el asistente elige región/nombre de stack. ApiKeyValue debe ser una clave alfanumérica de 20–128 caracteres. CorsOrigin debe coincidir exactamente con el origen del frontend, inicialmente `http://localhost:4200`. No guardes la clave en Git.
4. Copia la salida ApiUrl y úsala en Conexión API con tu ApiKeyValue.
5. Ejecuta el verificador contra esa URL para obtener evidencia AWS. Las metas de latencia deben medirse allí; los arranques en frío Java pueden superar las metas del avance.
6. El frontend se puede ejecutar localmente contra AWS o servir su carpeta browser en hosting estático HTTPS. Para otro origen, actualiza CorsOrigin, vuelve a desplegar y modifica public/config.json antes de compilar, o usa la pantalla de conexión.

No es necesario `sam build`: la plantilla referencia el JAR lambda generado por Maven; `sam deploy` empaqueta y sube ese archivo.

### Trazabilidad y recuperación

La recepción hace una escritura condicional en DynamoDB. DynamoDB Streams publica INSERT a SQS mediante una Lambda adicional. Así, el guardado y la intención de encolar son durables, sin depender de dos escrituras independientes en la API.

SQS entrega al menos una vez. El procesador utiliza comparación condicional del registro, una concesión de 90 segundos y rutas de archivo estables. Los estados ACEPTADO/RECHAZADO no se reprocesan. Si hay un trabajador activo, la entrega se reintenta. La visibilidad de SQS es de 180 segundos frente al timeout Lambda de 30 segundos. Se reportan fallos parciales por mensaje para no repetir el lote entero.

Tras 5 entregas fallidas el mensaje pasa a la DLQ; el documento queda ERROR (o PROCESANDO hasta que expire su concesión si hubo timeout). Revisa CloudWatch y corrige la causa antes de usar la función de redrive de SQS. En local se permiten hasta 5 errores por documento y quedan registrados en el historial.

El stream conserva eventos por 24 horas. La alarma PublisherLagAlarm avisa en CloudWatch cuando el retraso supera 60 segundos. Si una interrupción del publicador dura más de la retención, revisa registros RECIBIDO y vuelve a enviar sus documentId a QueueUrl usando SQS. La alarma de DLQ detecta mensajes pendientes. No se configuró correo SNS: las alarmas se consultan en CloudWatch y la notificación funcional se realiza por consulta de estado, como permite el avance.

Logs de Lambda: retención de 14 días. Filtra por documentId; los errores incluyen stack trace. Los fallos en recepción incluyen requestId. Las alarmas no envían mensajes a destinatarios externos.

### Acceso y costos

API Gateway exige API key y usa un plan de 2 solicitudes/segundo promedio (aprox. 120/minuto), ráfaga de 40 y cuota diaria de 10000. El throttling de API Gateway es de mejor esfuerzo; no es un contador estricto por minuto. Localmente se aplica un contador fijo de 120 solicitudes/minuto por clave compartida, con 429 y Retry-After.

El bucket bloquea acceso público, cifra objetos y deniega transporte sin TLS. Las funciones reciben permisos limitados por recurso. La API no contiene credenciales AWS y usa el rol IAM de Lambda. La clave es apropiada para el alcance académico; para un producto con usuarios se debe incorporar JWT/Cognito y autorización por tenant.

Se crean recursos facturables, incluidos almacenamiento, backups, logs, alarmas y peticiones. No hay EC2 ni servidores Java persistentes en AWS. No se promete costo cero. Al terminar la demostración, revisa y elimina los recursos desde tu cuenta; un bucket con objetos debe vaciarse de forma consciente antes de eliminar el stack.

## Correspondencia con el avance

| Requisito | Implementación |
|---|---|
| RF-01/03 | POST, documentId determinista y registro RECIBIDO |
| RF-02 | Validación de emisor, cliente, fecha, ítems, importes y 18% IGV |
| RF-04 | Worker local / DynamoDB Streams → SQS → Lambda en AWS |
| RF-05 | XML escapado y PDF con paginación; H2 local / S3 privado |
| RF-06 | GET por ID e historial de estados |
| RF-07 | Escritura condicional y detección de conflicto 409 |
| RF-08 | Logs con documentId, errores visibles, reintentos y DLQ |
| Seguridad | API key, CORS explícito, rate limit y descargas autorizadas |
| Concurrencia | Pruebas automatizadas y verificador HTTP de 20 solicitudes |

La evidencia local no sustituye las capturas de API Gateway, S3, CloudWatch ni la prueba remota requeridas para sustentar el despliegue cloud. Para la sustentación: crea un comprobante, muestra RECIBIDO/ACEPTADO e historial, descarga XML/PDF, repite el envío, prueba una solicitud sin clave y ejecuta verify.mjs.

Para la demo de bajo uso, consulta docs/AWS-ESCOLAR.md y la plantilla infra/template-escolar.yaml. Su despliegue requiere verificar primero la cobertura gratuita de la cuenta.
