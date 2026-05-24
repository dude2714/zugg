$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'

[xml]$addonXml = Get-Content -LiteralPath 'plugin.video.fenjr\addon.xml'
$addonVersion = $addonXml.addon.version
$addonZip = 'plugin.video.fenjr-' + $addonVersion + '.zip'
$repoZip = 'repository.fenjr-1.0.1.zip'

$bundleDir = Join-Path 'C:\Users\johns\OneDrive\Desktop\Kodi Updates' ('FenJr-Final-' + $addonVersion)
Remove-Item -Recurse -Force $bundleDir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $bundleDir -Force | Out-Null

Copy-Item -LiteralPath (Join-Path 'plugin.video.fenjr' $addonZip) -Destination (Join-Path $bundleDir $addonZip) -Force
Copy-Item -LiteralPath (Join-Path 'repo_fenjr' $repoZip) -Destination (Join-Path $bundleDir $repoZip) -Force
Copy-Item -LiteralPath 'repo_fenjr\addons.xml' -Destination (Join-Path $bundleDir 'repo_fenjr.addons.xml') -Force
Copy-Item -LiteralPath 'repo_fenjr\addons.xml.md5' -Destination (Join-Path $bundleDir 'repo_fenjr.addons.xml.md5') -Force

if (Test-Path 'L:\') {
    Copy-Item -LiteralPath (Join-Path 'plugin.video.fenjr' $addonZip) -Destination (Join-Path 'L:\' $addonZip) -Force
    Copy-Item -LiteralPath (Join-Path 'repo_fenjr' $repoZip) -Destination (Join-Path 'L:\' $repoZip) -Force
}

Write-Host ('BUNDLE_DIR=' + $bundleDir)
Get-ChildItem -LiteralPath $bundleDir | Select-Object Name,Length | Format-Table -AutoSize
