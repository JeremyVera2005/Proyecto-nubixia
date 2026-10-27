$ErrorActionPreference = 'Stop'
Set-Location (Join-Path (Split-Path $PSScriptRoot -Parent) 'comprobastes-serverless-frontend')
[IO.File]::WriteAllText((Join-Path (Get-Location) 'public/config.json'),'{"apiUrl":"http://localhost:8080","autoConnectLocal":true}',[Text.UTF8Encoding]::new($false))
if (-not (Test-Path node_modules)) { & npm.cmd ci; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
& npm.cmd start -- --host localhost --port 4200
exit $LASTEXITCODE
