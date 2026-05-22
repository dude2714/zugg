$ErrorActionPreference = 'Stop'
$base = 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'

$copies = @(
    @{ Source = Join-Path $base 'repository.venom\icon.png'; Destination = Join-Path $base 'repo_pov\repository.pov\icon.png' },
    @{ Source = Join-Path $base 'repository.venom\fanart.jpg'; Destination = Join-Path $base 'repo_pov\repository.pov\fanart.jpg' },
    @{ Source = Join-Path $base 'repository.venom\icon.png'; Destination = Join-Path $base 'repo_fenfork\repository.fenfork\icon.png' },
    @{ Source = Join-Path $base 'repository.venom\fanart.jpg'; Destination = Join-Path $base 'repo_fenfork\repository.fenfork\fanart.jpg' }
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

$zipTargets = @(
    @{ Folder = Join-Path $base '_pov_check\plugin.video.pov'; Zip = Join-Path $base 'repo_pov\plugin.video.pov-6.05.11.zip' },
    @{ Folder = Join-Path $base 'plugin.video.fenfork'; Zip = Join-Path $base 'repo_fenfork\plugin.video.fenfork-3.5.08.zip' },
    @{ Folder = Join-Path $base 'repo_pov\repository.pov'; Zip = Join-Path $base 'repo_pov\repository.pov-1.0.0.zip' },
    @{ Folder = Join-Path $base 'repo_fenfork\repository.fenfork'; Zip = Join-Path $base 'repo_fenfork\repository.fenfork-1.0.0.zip' }
)

foreach ($target in $zipTargets) {
    if (Test-Path $target.Zip) {
        Remove-Item -Force $target.Zip
    }
    Compress-Archive -Path $target.Folder -DestinationPath $target.Zip -Force
}

Write-Output 'BUILT_SPLIT_REPOS'
