$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$frontend=Join-Path $projectRoot 'comprobastes-serverless-frontend'
$backend=Join-Path $projectRoot 'comprobantes-serverless'
Push-Location $frontend
try {
 & npm.cmd run build -- --base-href /demo/
 if($LASTEXITCODE -ne 0){throw 'No se pudo compilar la web.'}
 $destination=Join-Path $backend 'src/main/resources/web'
 New-Item -ItemType Directory -Path $destination -Force | Out-Null
 Get-ChildItem -LiteralPath $destination -File | Where-Object {$_.Name -match '^(main|styles)-[a-zA-Z0-9]+\.(js|css)$'} | ForEach-Object {Remove-Item -LiteralPath $_.FullName}
 Get-ChildItem -LiteralPath (Join-Path $frontend 'dist/nubixia-web/browser') -File | Where-Object {$_.Name -ne 'config.json'} | Copy-Item -Destination $destination
} finally {Pop-Location}
Push-Location $backend
try {& .\mvnw.cmd -q package;if($LASTEXITCODE -ne 0){throw 'No se pudo empaquetar el backend.'}} finally {Pop-Location}
