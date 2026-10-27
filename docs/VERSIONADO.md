# Versionado de Nubixia

El historial Git comienza con una línea base del proyecto existente el 26 de octubre de 2026. Este primer registro reúne trabajo previo; no reconstruye commits ni fechas de los sprints anteriores.

Repositorio remoto: https://github.com/JeremyVera2005/Proyecto-nubixia

Se encontró un commit de scaffolding dentro del frontend. Su repositorio original se conserva localmente en `.tools/git-backups/frontend-original.git`. El nuevo repositorio raíz reúne frontend, backend e infraestructura y no incorpora el frontend como submódulo.

## Qué se conserva

- Código del frontend Angular y backend Java.
- Dependencias declaradas y archivos de bloqueo para reproducir compilaciones.
- Plantillas de infraestructura, scripts, documentación y evidencias académicas.

Se excluyen credenciales AWS, archivos `.env` privados, claves, dependencias descargadas, datos locales, compilaciones, herramientas temporales y ZIP generados. `.env.example` contiene únicamente configuración de ejemplo. Las claves públicas de demostración local no son credenciales de AWS.

## Flujo de trabajo

Desde la raíz del proyecto:

```powershell
git switch main
git pull --ff-only
git switch -c mejora/nombre-del-cambio
# Editar y verificar el cambio
git status
git diff
git add ruta/del/archivo
git diff --cached
git commit -m "Describe el cambio y su propósito"
git push -u origin mejora/nombre-del-cambio
```

Después se abre un pull request hacia `main`, se revisa y se integra. Los commits nuevos deben representar cambios reales y usar la identidad del autor. El primer commit utiliza la identidad Git que ya estaba configurada en esta computadora.

## Relación con AWS

Subir un commit a GitHub conserva el código, pero no actualiza automáticamente el sitio AWS. El despliegue sigue el procedimiento de los scripts y las guías del proyecto. No hay un pipeline de despliegue automático configurado por esta preparación del repositorio.

Nunca se deben subir `.env.aws.json`, tokens Cognito, claves de acceso AWS ni credenciales de GitHub. Para compartir un repositorio privado con el profesor, se le debe conceder acceso desde GitHub cuando lo solicite el propietario.
