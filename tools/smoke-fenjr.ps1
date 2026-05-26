$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'

[xml]$addonXml = Get-Content -LiteralPath 'plugin.video.fenjr\addon.xml'
$addonVersion = $addonXml.addon.version
$addonZip = 'plugin.video.fenjr-' + $addonVersion + '.zip'
$repoZip = 'repository.fenjr-1.0.1.zip'

$requiredLocal = @(
    'repo_fenjr\addons.xml',
    'repo_fenjr\addons.xml.md5',
    (Join-Path 'repo_fenjr' $repoZip),
    (Join-Path 'repo_fenjr\plugin.video.fenjr' $addonZip),
    'repo_fenjr\plugin.video.fenjr\icon.png',
    'repo_fenjr\plugin.video.fenjr\fanart.png'
)

foreach ($path in $requiredLocal) {
    if (!(Test-Path $path)) {
        throw ('Missing local smoke-check file: ' + $path)
    }
}

$urls = @(
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenjr/addons.xml',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenjr/addons.xml.md5',
    ('https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenjr/' + $repoZip),
    ('https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenjr/plugin.video.fenjr/' + $addonZip),
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenjr/plugin.video.fenjr/icon.png',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenjr/plugin.video.fenjr/fanart.png'
)

foreach ($u in $urls) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Method Head -Uri $u -TimeoutSec 30
        Write-Host ('OK ' + $r.StatusCode + ' ' + $u)
    }
    catch {
        $retry = $u + '?cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        try {
            $r2 = Invoke-WebRequest -UseBasicParsing -Method Head -Uri $retry -TimeoutSec 30
            Write-Host ('OK ' + $r2.StatusCode + ' ' + $u + ' (cache-busted)')
        }
        catch {
            throw ('Smoke URL failed: ' + $u)
        }
    }
}

Write-Host ('FENJR_SMOKE_OK version=' + $addonVersion)
