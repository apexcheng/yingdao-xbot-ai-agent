$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    qmd update
    if ($LASTEXITCODE -ne 0) { throw "qmd update failed with exit code $LASTEXITCODE" }

    qmd embed
    if ($LASTEXITCODE -ne 0) { throw "qmd embed failed with exit code $LASTEXITCODE" }

    qmd status
    if ($LASTEXITCODE -ne 0) { throw "qmd status failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
