$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$privatePath = Join-Path $projectRoot '.env.aws.json'
if (-not (Test-Path -LiteralPath $privatePath)) { throw 'Falta la configuración privada del despliegue AWS.' }
$config = Get-Content -LiteralPath $privatePath -Raw | ConvertFrom-Json
if (-not $config.apiUrl -or -not $config.apiKey) { throw 'El despliegue todavía no tiene una API operativa configurada.' }
Set-Location (Join-Path $projectRoot 'comprobastes-serverless-frontend')
$runtimePath = Join-Path (Get-Location) 'public/config.json'
$previousRuntime = [IO.File]::ReadAllText($runtimePath)
try {
 $runtimeConfig = @{apiUrl='/api';localProxy=$true;cloudMode=$true}
 if ($config.auth) { $runtimeConfig.auth=$config.auth }
 [IO.File]::WriteAllText($runtimePath,($runtimeConfig | ConvertTo-Json -Depth 5 -Compress),[Text.UTF8Encoding]::new($false))
 if (-not (Test-Path node_modules)) { & npm.cmd ci; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
 & npm.cmd start -- --host localhost --port 4200 --proxy-config proxy.conf.cjs
 if ($LASTEXITCODE -ne 0) { throw "No se pudo iniciar el frontend AWS (código $LASTEXITCODE)." }
} finally {
 [IO.File]::WriteAllText($runtimePath,$previousRuntime,[Text.UTF8Encoding]::new($false))
}
