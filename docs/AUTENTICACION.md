# Autenticación y sitio público

URL: https://0qx6ww77nl.execute-api.us-east-2.amazonaws.com/demo/

## Flujo

1. Crear cuenta con nombre, correo y contraseña de 10 caracteres como mínimo, con mayúscula, minúscula y número.
2. Confirmar el código que Cognito envía al correo. Hay opción de reenviar el código.
3. Iniciar sesión para acceder al panel. También se implementó recuperación de contraseña por código.
4. Cerrar sesión elimina las credenciales locales y revoca el refresh token. Los ID tokens ya emitidos pueden ser válidos hasta su expiración de 15 minutos.

Cognito Lite almacena las credenciales; el backend propio no recibe ni guarda contraseñas. La SPA usa un cliente público sin secreto. Los tokens se conservan durante la sesión de la pestaña y se renuevan con el refresh token, válido durante un día. No hay credenciales IAM ni claves compartidas en el JavaScript o config.json público.

## Protección de datos

API Gateway verifica el ID token con el authorizer Cognito. Lambda toma el sub únicamente del contexto del authorizer, nunca del cuerpo ni de headers inventados. Cada registro DynamoDB guarda owner y su ID incluye el usuario en el hash de identidad. Listado, consulta y descarga verifican el propietario. El procesador actualiza el payload sin borrar owner.

Los comprobantes compartidos de las pruebas anteriores se conservan, pero no pertenecen a una cuenta nueva y no aparecen en su panel. Los archivos S3 son privados y se descargan mediante enlaces firmados de cinco minutos después de comprobar la propiedad.

## Alojamiento

La landing y la SPA Angular se empaquetan como recursos web del JAR. Lambda sirve solo archivos permitidos por nombre; no expone application.properties, .env ni rutas arbitrarias. API Gateway entrega el sitio por HTTPS bajo /demo/. Los archivos binarios usan respuesta base64 y la configuración de Cognito se obtiene del entorno de Lambda.

CSP permite scripts únicamente del propio origen. La compilación desactiva inlineCritical para cargar CSS sin manejadores JavaScript inline. Se agregan nosniff, DENY para frames y no-referrer. El panel y las respuestas de autenticación no se almacenan en caché.

## Recompilar

Con JAVA_HOME apuntando al JDK 17:

```powershell
.\scripts\build-web-api.ps1
```

Compila Angular con base href /demo/, copia los archivos públicos al backend y ejecuta Maven package. config.json se genera en Lambda con IDs públicos de Cognito, sin claves.

La primera cuenta y la recepción efectiva de su correo de confirmación debe comprobarlas su propietario. Las pruebas automatizadas no crean cuentas reales ni envían correos a terceros.
