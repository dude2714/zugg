$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $PSScriptRoot
$zipBuilder = Join-Path $PSScriptRoot 'build-kodi-zip.py'

$copies = @(
    @{ Source = Join-Path $base 'repository.venom\icon.png'; Destination = Join-Path $base 'repo_pov\repository.pov\icon.png' },
    @{ Source = Join-Path $base 'repository.venom\fanart.jpg'; Destination = Join-Path $base 'repo_pov\repository.pov\fanart.jpg' },
    @{ Source = Join-Path $base 'repository.venom\icon.png'; Destination = Join-Path $base 'repo_fenfork\repository.fenfork\icon.png' },
    @{ Source = Join-Path $base 'repository.venom\fanart.jpg'; Destination = Join-Path $base 'repo_fenfork\repository.fenfork\fanart.jpg' },
    @{ Source = Join-Path $base 'script.module.requests-2.31.0.zip'; Destination = Join-Path $base 'repo_pov\script.module.requests-2.31.0.zip' },
    @{ Source = Join-Path $base 'script.module.certifi-2023.5.7.zip'; Destination = Join-Path $base 'repo_pov\script.module.certifi-2023.5.7.zip' },
    @{ Source = Join-Path $base 'script.module.chardet-5.1.0.zip'; Destination = Join-Path $base 'repo_pov\script.module.chardet-5.1.0.zip' },
    @{ Source = Join-Path $base 'script.module.idna-3.4.0.zip'; Destination = Join-Path $base 'repo_pov\script.module.idna-3.4.0.zip' },
    @{ Source = Join-Path $base 'script.module.urllib3-1.26.16+matrix.1.zip'; Destination = Join-Path $base 'repo_pov\script.module.urllib3-1.26.16+matrix.1.zip' },
    @{ Source = Join-Path $base 'script.module.requests-2.31.0.zip'; Destination = Join-Path $base 'repo_fenfork\script.module.requests-2.31.0.zip' },
    @{ Source = Join-Path $base 'script.module.certifi-2023.5.7.zip'; Destination = Join-Path $base 'repo_fenfork\script.module.certifi-2023.5.7.zip' },
    @{ Source = Join-Path $base 'script.module.chardet-5.1.0.zip'; Destination = Join-Path $base 'repo_fenfork\script.module.chardet-5.1.0.zip' },
    @{ Source = Join-Path $base 'script.module.idna-3.4.0.zip'; Destination = Join-Path $base 'repo_fenfork\script.module.idna-3.4.0.zip' },
    @{ Source = Join-Path $base 'script.module.urllib3-1.26.16+matrix.1.zip'; Destination = Join-Path $base 'repo_fenfork\script.module.urllib3-1.26.16+matrix.1.zip' }
)

foreach ($copy in $copies) {
    Copy-Item -LiteralPath $copy.Source -Destination $copy.Destination -Force
}

foreach ($repo in @('repo_pov', 'repo_fenfork')) {
    $path = Join-Path $base $repo
    $content = Get-Content -LiteralPath (Join-Path $path 'addons.xml') -Raw
    $lf = $content -replace "`r`n", "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($lf)
    $md5 = ([BitConverter]::ToString([System.Security.Cryptography.MD5]::Create().ComputeHash($bytes)) -replace '-', '').ToLower()
    Set-Content -LiteralPath (Join-Path $path 'addons.xml.md5') -Value $md5 -NoNewline
}

[xml]$povRepoAddon = Get-Content -LiteralPath (Join-Path $base 'repo_pov\repository.pov\addon.xml')
$povRepoVersion = $povRepoAddon.addon.version

[xml]$povAddon = Get-Content -LiteralPath (Join-Path $base '_pov_check\plugin.video.pov\addon.xml')
$povAddonVersion = $povAddon.addon.version

[xml]$fenforkRepoAddon = Get-Content -LiteralPath (Join-Path $base 'repo_fenfork\repository.fenfork\addon.xml')
$fenforkRepoVersion = $fenforkRepoAddon.addon.version

[xml]$fenforkAddon = Get-Content -LiteralPath (Join-Path $base 'plugin.video.fenfork\addon.xml')
$fenforkAddonVersion = $fenforkAddon.addon.version

$zipTargets = @(
    @{ Folder = Join-Path $base '_pov_check\plugin.video.pov'; Zip = Join-Path $base ("repo_pov\plugin.video.pov-{0}.zip" -f $povAddonVersion) },
    @{ Folder = Join-Path $base 'plugin.video.fenfork'; Zip = Join-Path $base ("repo_fenfork\plugin.video.fenfork-{0}.zip" -f $fenforkAddonVersion) },
    @{ Folder = Join-Path $base 'repo_pov\repository.pov'; Zip = Join-Path $base ("repo_pov\repository.pov-{0}.zip" -f $povRepoVersion) },
    @{ Folder = Join-Path $base 'repo_fenfork\repository.fenfork'; Zip = Join-Path $base ("repo_fenfork\repository.fenfork-{0}.zip" -f $fenforkRepoVersion) }
)

foreach ($target in $zipTargets) {
    if (Test-Path $target.Zip) {
        Remove-Item -Force $target.Zip
    }
    python $zipBuilder $target.Folder $target.Zip
}

Write-Output 'BUILT_SPLIT_REPOS'
