<#
.SYNOPSIS
  Prueba login, GET /user/me y (opcional) varios GET protegidos por rol contra el API.

.DESCRIPTION
  Roles (user.role):
    0 = Super Administrador
    1 = Administrador
    2 = Gerente
    3 = Evaluador

  Variables de entorno:
    CX_SMOKE_EMAIL_0..3, CX_SMOKE_PASSWORD_0..3
    CX_SMOKE_API_BASE (opcional)
    CX_SMOKE_DEEP=0 desactiva las pruebas GET adicionales (por defecto estan activas).

  Ejemplo:
    .\scripts\smoke-role-logins.ps1
    .\scripts\smoke-role-logins.ps1 -Shallow
#>
param(
    [string]$ApiBase = $(if ($env:CX_SMOKE_API_BASE) { $env:CX_SMOKE_API_BASE } else { "https://siete-api-staging.up.railway.app/api/v1" }),
    [switch]$Shallow
)

$ErrorActionPreference = "Stop"
$script:SmokeFailed = $false
$doDeep = -not $Shallow
if ($env:CX_SMOKE_DEEP -eq '0') { $doDeep = $false }

$roles = @(
    @{ Id = 0; Name = "Super Administrador" }
    @{ Id = 1; Name = "Administrador" }
    @{ Id = 2; Name = "Gerente" }
    @{ Id = 3; Name = "Evaluador" }
)

# Codigos HTTP esperados por rol (segun rutas actuales en app/routes).
$ExpectedByRole = @{
    0 = @{
        campaign       = 403
        evaluations    = 200
        dashboard      = 200
        audit          = 200
        survey         = 200
        qualityCatalog = 200
    }
    1 = @{
        campaign       = 200
        evaluations    = 200
        dashboard      = 200
        audit          = 200
        survey         = 200
        qualityCatalog = 200
    }
    2 = @{
        campaign       = 200
        evaluations    = 200
        dashboard      = 200
        audit          = 200
        survey         = 200
        qualityCatalog = 403
    }
    3 = @{
        campaign       = 403
        evaluations    = 200
        dashboard      = 200
        audit          = 403
        survey         = 403
        qualityCatalog = 403
    }
}

$DeepPaths = @(
    @{ Key = "campaign";       Path = "campaign/?limit=5" }
    @{ Key = "evaluations"; Path = "evaluations/?limit=5" }
    @{ Key = "dashboard";   Path = "dashboard/" }
    @{ Key = "audit";       Path = "audit/?limit=5" }
    @{ Key = "survey";      Path = "survey/?limit=5" }
    @{ Key = "qualityCatalog"; Path = "quality/industries?limit=5" }
)

function Invoke-Login {
    param([string]$Email, [string]$Password)
    $encEmail = [uri]::EscapeDataString($Email)
    $encPass = [uri]::EscapeDataString($Password)
    $form = "username=$encEmail&password=$encPass"
    return Invoke-RestMethod -Uri "$ApiBase/auth/login" -Method Post -Body $form -ContentType "application/x-www-form-urlencoded"
}

function Invoke-UserMe {
    param([string]$Token)
    $hdr = @{ Authorization = "Bearer $Token" }
    return Invoke-RestMethod -Uri "$ApiBase/user/me" -Method Get -Headers $hdr
}

function Get-HttpStatus {
    param([string]$Token, [string]$RelativePath)
    $base = $ApiBase.TrimEnd("/")
    $rel = $RelativePath.TrimStart("/")
    $url = "$base/$rel"
    $hdr = @{ Authorization = "Bearer $Token" }
    try {
        $resp = Invoke-WebRequest -Uri $url -Headers $hdr -Method Get -UseBasicParsing -ErrorAction Stop
        return [int]$resp.StatusCode
    }
    catch {
        try {
            return [int]$_.Exception.Response.StatusCode.value__
        }
        catch {
            return 0
        }
    }
}

function Invoke-DeepChecks {
    param([string]$Token, [int]$Role)
    $exp = $ExpectedByRole[$Role]
    if (-not $exp) {
        Write-Host "  [deep] sin tabla de expectativas para role=$Role" -ForegroundColor DarkYellow
        return
    }
    Write-Host "  [deep] GETs por permisos (rol $Role):" -ForegroundColor Cyan
    foreach ($item in $DeepPaths) {
        $want = $exp[$item.Key]
        $code = Get-HttpStatus -Token $Token -RelativePath $item.Path
        if ($code -eq $want) {
            Write-Host "    $($item.Path) -> $code OK" -ForegroundColor Green
        }
        else {
            Write-Host "    $($item.Path) -> $code (esperado $want) FAIL" -ForegroundColor Red
            $script:SmokeFailed = $true
        }
    }
}

Write-Host "API: $ApiBase" -ForegroundColor Cyan
if ($doDeep) {
    Write-Host "Modo: login + /user/me + pruebas GET por rol (CX_SMOKE_DEEP=0 o -Shallow para omitir)" -ForegroundColor Cyan
}
else {
    Write-Host "Modo: solo login + /user/me (-Shallow o CX_SMOKE_DEEP=0)" -ForegroundColor Cyan
}

$any = $false
foreach ($r in $roles) {
    $i = $r.Id
    $emailVar = "CX_SMOKE_EMAIL_$i"
    $passVar = "CX_SMOKE_PASSWORD_$i"
    $email = (Get-Item "Env:$emailVar" -ErrorAction SilentlyContinue).Value
    $password = (Get-Item "Env:$passVar" -ErrorAction SilentlyContinue).Value
    if ([string]::IsNullOrWhiteSpace($email) -or [string]::IsNullOrWhiteSpace($password)) {
        Write-Host "[omitido] rol $($r.Id) $($r.Name) - sin $emailVar / $passVar" -ForegroundColor DarkGray
        continue
    }
    $any = $true
    Write-Host "`n--- Rol $($r.Id) ($($r.Name)) - $email ---" -ForegroundColor Yellow
    try {
        $login = Invoke-Login -Email $email -Password $password
        $token = $login.access_token
        if (-not $token) {
            Write-Host "FAIL: respuesta sin access_token" -ForegroundColor Red
            $script:SmokeFailed = $true
            continue
        }
        $roleFromLogin = $login.user.role
        Write-Host "login OK - role en body: $roleFromLogin" -ForegroundColor Green
        if ($roleFromLogin -ne $r.Id) {
            Write-Host "AVISO: esperabas rol $($r.Id) en configuracion pero el usuario tiene role=$roleFromLogin" -ForegroundColor DarkYellow
        }
        $me = Invoke-UserMe -Token $token
        Write-Host "GET /user/me OK - id=$($me.id) email=$($me.email) role=$($me.role) company_id=$($me.company_id)" -ForegroundColor Green
        if ($doDeep) {
            Invoke-DeepChecks -Token $token -Role ([int]$me.role)
        }
    }
    catch {
        Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host $_.ErrorDetails.Message -ForegroundColor Red
        }
        $script:SmokeFailed = $true
    }
}

if (-not $any) {
    Write-Host "`nNo hay credenciales: define CX_SMOKE_EMAIL_0..3 y CX_SMOKE_PASSWORD_0..3" -ForegroundColor Magenta
    exit 2
}

if ($script:SmokeFailed) {
    exit 1
}
exit 0
