# Base de datos local

La API utiliza H2 SQL persistente. Al iniciar, Flyway crea el esquema y registra su versión. No necesitas instalar un servidor de base de datos.

El archivo está en `comprobantes-serverless/data/nubixia.mv.db`. Guarda:
- `COMPROBANTES`: emisor, cliente, serie, número, importes, estado y revisión para concurrencia.
- `COMPROBANTE_ITEMS`: líneas de productos o servicios.
- `COMPROBANTE_EVENTOS`: historial de transiciones.
- `COMPROBANTE_ARCHIVOS`: XML y PDF como datos binarios.

El snapshot interno de cada comprobante se conserva también en la columna PAYLOAD para que los adaptadores SQL y DynamoDB compartan el modelo. Las columnas y tablas relacionadas permiten hacer consultas SQL sin interpretar ese snapshot.

## Consultar los datos

Con el backend iniciado, abre http://localhost:8080/h2-console/.

Primero el navegador solicita autenticación HTTP:
- Usuario: `admin`
- Contraseña: tu API key local, inicialmente `nubixia-demo-local-2026`

Después completa la pantalla de H2:
- Driver Class: `org.h2.Driver`
- JDBC URL: `jdbc:h2:file:./data/nubixia`
- User Name: `nubixia`
- Password: `nubixia-local-db`

Las rutas relativas se resuelven desde la carpeta del backend, donde los scripts inician Java. Si defines NUBIXIA_DATA_DIR, usa la misma ruta en JDBC URL. Si defines NUBIXIA_DB_PASSWORD, usa esa contraseña en H2. El acceso web está restringido a la máquina local.

Consultas de ejemplo:
```sql
SELECT document_id, cliente, serie, numero, total, estado
FROM comprobantes ORDER BY creado_en DESC;

SELECT estado, COUNT(*) AS cantidad FROM comprobantes GROUP BY estado;

SELECT * FROM comprobante_items ORDER BY document_id, posicion;
SELECT * FROM comprobante_eventos ORDER BY document_id, posicion;

SELECT document_id, extension, OCTET_LENGTH(contenido) AS bytes
FROM comprobante_archivos;
```

El esquema está en `src/main/resources/db/migration/V1__comprobantes.sql`. Las futuras modificaciones deben agregarse como V2, V3, etc., sin cambiar una migración ya aplicada.

## Migración de la versión anterior

Al arrancar se importan los JSON de data/documents y los archivos de data/files. Cada comprobante y sus archivos se importan en una misma transacción. Los registros existentes no se duplican y los archivos originales se conservan. Si faltan XML/PDF de un comprobante ACEPTADO, el arranque informa el problema y no importa ese comprobante de forma incompleta.

Las nuevas emisiones y descargas usan SQL; los directorios JSON se mantienen únicamente como respaldo de la versión anterior. El worker consulta la base para recuperar pendientes.

## AWS

En AWS se mantiene DynamoDB para estados y S3 para XML/PDF, como exige el avance. H2 se usa en la aplicación local Spring Boot; las Lambda utilizan directamente AwsStore y no arrancan Spring ni H2.

## Verificación

Se aprobaron 15 pruebas de backend con la base SQL: recepción HTTP, consulta, archivos, concurrencia, duplicados, reintentos, límites, consola y migración de JSON. Las pruebas crean bases aisladas en directorios temporales. La prueba HTTP de carga se ejecuta desde la raíz con `node scripts/verify.mjs`.
