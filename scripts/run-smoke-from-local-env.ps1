# Carga scripts/smoke.local.env (KEY=valor por linea) y ejecuta smoke-role-logins.ps1.
# No imprime valores de contrasena.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $here "smoke.local.env"
if (-not (Test-Path $envFile)) {
    $alt = Join-Path $here "smoke.local.env.txt"
    if (Test-Path $alt) { $envFile = $alt }
}
if (-not (Test-Path $envFile)) {
    Write-Error "No existe smoke.local.env (ni smoke.local.env.txt). Copia smoke.local.env.example y guarda como smoke.local.env (sin .txt si el editor lo permite)."
    exit 1
}
Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -match '^\s*#' -or $line -eq '') { return }
    $i = $line.IndexOf('=')
    if ($i -lt 1) { return }
    $key = $line.Substring(0, $i).Trim()
    $val = $line.Substring($i + 1).Trim()
    if ($key) { [Environment]::SetEnvironmentVariable($key, $val, "Process") }
}
& (Join-Path $here "smoke-role-logins.ps1")
exit $LASTEXITCODE
