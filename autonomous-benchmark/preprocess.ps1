param(
    [string]$RawDir = "raw",
    [string]$IndexFile = "index.json",
    [string[]]$Process
)

$ErrorActionPreference = "Stop"
$benchDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$composeFile = Join-Path $benchDir "compose.yml"
$env:RAW_DIR = if ([IO.Path]::IsPathRooted($RawDir)) { $RawDir } else { Join-Path $benchDir $RawDir }
$env:INDEX_FILE = if ([IO.Path]::IsPathRooted($IndexFile)) { $IndexFile } else { Join-Path $benchDir $IndexFile }
$arguments = @("python", "-m", "benchmark.pipeline.preprocess", "--index", "/corpus/index.json", "--raw-dir", "/corpus/raw", "--output-dir", "/prepared")
foreach ($processId in $Process) { $arguments += @("--process", $processId) }

docker compose -f $composeFile --profile preprocess run --rm preprocess @arguments
exit $LASTEXITCODE
