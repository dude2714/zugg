$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'

# Always rebuild addon zip from current working source so repo payload can't pick up a stale package.
powershell -NoProfile -ExecutionPolicy Bypass -File 'tools\build-fenjr-addon.ps1'

$repo = 'repo_fenjr'
$repoAddon = Join-Path $repo 'repository.fenjr'
$repoVersion = '1.0.1'
$addonXmlPath = 'plugin.video.fenjr\addon.xml'
[xml]$addonXml = Get-Content -LiteralPath $addonXmlPath
$addonVersion = $addonXml.addon.version
$addonZipName = 'plugin.video.fenjr-' + $addonVersion + '.zip'
$addonZipPath = Join-Path 'plugin.video.fenjr' $addonZipName
if (!(Test-Path $addonZipPath)) { throw ('Missing built addon zip: ' + $addonZipPath) }

# Refresh repository feed checksum.
$md5 = (Get-FileHash -Algorithm MD5 (Join-Path $repo 'addons.xml')).Hash.ToLower()
Set-Content -LiteralPath (Join-Path $repo 'addons.xml.md5') -Value $md5 -NoNewline

# Copy Fen Jr addon zip at root and Kodi datadir subfolder.
Copy-Item -LiteralPath $addonZipPath -Destination (Join-Path $repo $addonZipName) -Force
New-Item -ItemType Directory -Path (Join-Path $repo 'plugin.video.fenjr') -Force | Out-Null
Copy-Item -LiteralPath $addonZipPath -Destination (Join-Path (Join-Path $repo 'plugin.video.fenjr') $addonZipName) -Force
if (Test-Path 'plugin.video.fenjr\icon.png') {
    Copy-Item -LiteralPath 'plugin.video.fenjr\icon.png' -Destination (Join-Path $repo 'plugin.video.fenjr\icon.png') -Force
}
if (Test-Path 'plugin.video.fenjr\fanart.png') {
    Copy-Item -LiteralPath 'plugin.video.fenjr\fanart.png' -Destination (Join-Path $repo 'plugin.video.fenjr\fanart.png') -Force
}

# Copy dependency zips at root and nested addon-id subfolders.
$deps = @(
    'script.module.requests-2.31.0.zip',
    'script.module.certifi-2023.5.7.zip',
    'script.module.chardet-5.1.0.zip',
    'script.module.idna-3.4.0.zip',
    'script.module.urllib3-1.26.16+matrix.1.zip'
)

foreach ($d in $deps) {
    Copy-Item -LiteralPath $d -Destination (Join-Path $repo $d) -Force
    $id = $d -replace '-[0-9].+$', ''
    $depDir = Join-Path $repo $id
    New-Item -ItemType Directory -Path $depDir -Force | Out-Null
    Copy-Item -LiteralPath $d -Destination (Join-Path $depDir $d) -Force
}

# Build repository.fenjr zip with strict internal structure.
$stage = '_fenjr_repo_stage'
Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $stage 'repository.fenjr') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repoAddon 'addon.xml') -Destination (Join-Path $stage 'repository.fenjr\addon.xml') -Force
Copy-Item -LiteralPath (Join-Path $repoAddon 'icon.png') -Destination (Join-Path $stage 'repository.fenjr\icon.png') -Force
Copy-Item -LiteralPath (Join-Path $repoAddon 'fanart.jpg') -Destination (Join-Path $stage 'repository.fenjr\fanart.jpg') -Force

Set-Location $stage
if (Test-Path ("repository.fenjr-" + $repoVersion + ".zip")) {
    Remove-Item ("repository.fenjr-" + $repoVersion + ".zip") -Force
}
tar.exe -a -c -f ("repository.fenjr-" + $repoVersion + ".zip") 'repository.fenjr'
Set-Location ..

Copy-Item -LiteralPath (Join-Path $stage ("repository.fenjr-" + $repoVersion + ".zip")) -Destination (Join-Path $repo ("repository.fenjr-" + $repoVersion + ".zip")) -Force
Copy-Item -LiteralPath (Join-Path $stage ("repository.fenjr-" + $repoVersion + ".zip")) -Destination (Join-Path $repoAddon ("repository.fenjr-" + $repoVersion + ".zip")) -Force

# Convenience copies for local Kodi testing.
$desk = 'C:\Users\johns\OneDrive\Desktop\Kodi Updates'
New-Item -ItemType Directory -Path $desk -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repo ("repository.fenjr-" + $repoVersion + ".zip")) -Destination (Join-Path $desk ("repository.fenjr-" + $repoVersion + ".zip")) -Force
if (Test-Path 'L:\') {
    Copy-Item -LiteralPath (Join-Path $repo ("repository.fenjr-" + $repoVersion + ".zip")) -Destination ("L:\repository.fenjr-" + $repoVersion + ".zip") -Force
}

Write-Host 'Fen Jr repository payload built.'
