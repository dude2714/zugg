$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'

[xml]$addonXml = Get-Content -LiteralPath 'plugin.video.fenjr\addon.xml'
$addonVersion = $addonXml.addon.version
$addonZipName = 'plugin.video.fenjr-' + $addonVersion + '.zip'

$stage = '_fenjr_addon_stage'
Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $stage 'plugin.video.fenjr') -Force | Out-Null

Copy-Item -LiteralPath 'plugin.video.fenjr\addon.xml' -Destination (Join-Path $stage 'plugin.video.fenjr\addon.xml') -Force
if (Test-Path 'plugin.video.fenjr\changelog.txt') {
    Copy-Item -LiteralPath 'plugin.video.fenjr\changelog.txt' -Destination (Join-Path $stage 'plugin.video.fenjr\changelog.txt') -Force
}
Copy-Item -LiteralPath 'plugin.video.fenjr\resources' -Destination (Join-Path $stage 'plugin.video.fenjr\resources') -Recurse -Force
if (Test-Path 'plugin.video.fenjr\icon.png') {
    Copy-Item -LiteralPath 'plugin.video.fenjr\icon.png' -Destination (Join-Path $stage 'plugin.video.fenjr\icon.png') -Force
}
if (Test-Path 'plugin.video.fenjr\fanart.png') {
    Copy-Item -LiteralPath 'plugin.video.fenjr\fanart.png' -Destination (Join-Path $stage 'plugin.video.fenjr\fanart.png') -Force
}

$zipPath = Join-Path 'plugin.video.fenjr' $addonZipName
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Set-Location $stage
tar.exe -a -c -f (Join-Path '..' $zipPath) 'plugin.video.fenjr'
Set-Location ..

Write-Host ('Built ' + $zipPath)
