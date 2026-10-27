$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $env:JAVA_HOME -and (Test-Path 'C:\Program Files\Java\jdk-17')) { $env:JAVA_HOME = 'C:\Program Files\Java\jdk-17' }
if ($env:JAVA_HOME) { $env:Path = "$env:JAVA_HOME\bin;$env:Path" }
Set-Location (Join-Path $projectRoot 'comprobantes-serverless')
if (-not $env:NUBIXIA_API_KEY) { $env:NUBIXIA_API_KEY = 'nubixia-demo-local-2026' }
& .\mvnw.cmd spring-boot:run
exit $LASTEXITCODE
