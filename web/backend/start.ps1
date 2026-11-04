# Windows Server startup for the submission API, using external region resources.
param(
    [string] $RegionsDir = 'C:\guance\regions',
    [string] $HostAddress = '127.0.0.1',
    [int] $Port = 8000
)

$ErrorActionPreference = 'Stop'
$required = @(
    'mainland-province-prefecture-county.json',
    'manifest.json',
    'policy-region-map.json',
    'policy-region-review.json'
)
if (-not (Test-Path -LiteralPath $RegionsDir -PathType Container)) {
    throw "地区资源目录不存在：$RegionsDir；先执行 scripts/install_regions.ps1。"
}
foreach ($name in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $RegionsDir $name) -PathType Leaf)) {
        throw "地区资源缺少：$name；请补齐已审核的四个文件。"
    }
}
$env:GUANCE_POLICY_REGIONS_DIR = (Resolve-Path -LiteralPath $RegionsDir).Path
Push-Location $PSScriptRoot
try {
    python -m uvicorn app.main:app --host $HostAddress --port $Port
} finally {
    Pop-Location
}
