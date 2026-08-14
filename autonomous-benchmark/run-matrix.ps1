param(
    [string]$Matrix = "matrix.json",
    [string]$EnvFile = "configs/example.env"
)

$ErrorActionPreference = "Stop"
$benchDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $benchDir "matrix_runner.py") --matrix $Matrix --env-file $EnvFile
exit $LASTEXITCODE
