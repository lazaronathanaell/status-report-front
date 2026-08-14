param(
    [string]$EnvFile = "configs/22001149961202519.env"
)

$ErrorActionPreference = "Stop"
$benchDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$envPath = if ([IO.Path]::IsPathRooted($EnvFile)) { $EnvFile } else { Join-Path $benchDir $EnvFile }
$composeFile = Join-Path $benchDir "compose.yml"
$composeExecutable = if (Get-Command docker-compose -ErrorAction SilentlyContinue) { "docker-compose" } else { "docker" }
$composePrefix = if ($composeExecutable -eq "docker") { @("compose") } else { @() }

function Invoke-BenchCompose {
    & $composeExecutable @composePrefix -f $composeFile --env-file $envPath @args
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose falhou: $($args -join ' ')" }
}

$exitCode = 0
try {
    Invoke-BenchCompose up -d --build --wait ollama
    Invoke-BenchCompose run --rm model-pull
    Invoke-BenchCompose up -d --build metrics
    & $composeExecutable @composePrefix -f $composeFile --env-file $envPath up --build --no-deps benchmark
    $exitCode = $LASTEXITCODE
    Invoke-BenchCompose wait metrics
}
finally {
    & $composeExecutable @composePrefix -f $composeFile --env-file $envPath down
}

exit $exitCode
