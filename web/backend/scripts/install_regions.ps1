# Installs the FOUR existing reviewed region assets into one directory.
# The assets are deployment resources, NOT part of the source-only submission.
param(
    [Parameter(Mandatory = $true)][string] $SourceDir,
    [string] $DestinationDir = 'C:\guance\regions'
)

$ErrorActionPreference = 'Stop'
$files = @(
    'mainland-province-prefecture-county.json',
    'manifest.json',
    'policy-region-map.json',
    'policy-region-review.json'
)
$src = (Resolve-Path -LiteralPath $SourceDir).Path
foreach ($name in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $src $name) -PathType Leaf)) {
        throw "地区资源缺少：$name；请从原有已审核部署资源中获取，不能生成虚构映射。"
    }
}
if (-not (Test-Path -LiteralPath $DestinationDir)) {
    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
}
foreach ($name in $files) {
    $source = Join-Path $src $name
    $target = Join-Path $DestinationDir $name
    if ($source -ne $target) { Copy-Item -LiteralPath $source -Destination $target -Force }
}
$env:GUANCE_POLICY_REGIONS_DIR = (Resolve-Path -LiteralPath $DestinationDir).Path
Write-Host ("地区资源路径：" + $env:GUANCE_POLICY_REGIONS_DIR)
Write-Host '已复制四个地区资源文件；请运行 web/backend/start.ps1 启动服务，由后端做哈希及版本校验。'
