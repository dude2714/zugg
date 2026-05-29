$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$repo = 'repo_thecrew'
$repoId = 'repository.thecrewsolo'

function Require-File([string]$path) {
    if (!(Test-Path $path)) {
        throw "Required file not found: $path"
    }
}

Require-File (Join-Path $repo (Join-Path $repoId 'addon.xml'))
Require-File '_crewsrc_crew.xml'
Require-File '_crewsrc_unhinged.xml'
Require-File '_kodi_addons.xml'

$repoAddonBody = (Get-Content -LiteralPath (Join-Path $repo (Join-Path $repoId 'addon.xml')) -Raw) -replace '^\s*<\?xml[^\n]*\?>\s*', ''

[xml]$crew = Get-Content -LiteralPath '_crewsrc_crew.xml'
[xml]$unhinged = Get-Content -LiteralPath '_crewsrc_unhinged.xml'
[xml]$kodi = Get-Content -LiteralPath '_kodi_addons.xml'

$plan = @(
    @{ Id='plugin.video.thecrew';            Source='crew';     Datadir='https://raw.githubusercontent.com/thecrewwh/zips/master/matrix/_zip'; FolderStyle=$true },
    @{ Id='script.module.thecrew';           Source='crew';     Datadir='https://raw.githubusercontent.com/thecrewwh/zips/master/matrix/_zip'; FolderStyle=$true },
    @{ Id='script.thecrew.artwork';          Source='crew';     Datadir='https://raw.githubusercontent.com/thecrewwh/zips/master/matrix/_zip'; FolderStyle=$true },
    @{ Id='script.module.resolveurl';        Source='unhinged'; Datadir='https://raw.githubusercontent.com/unhingedthemes/zips/main/_zips'; FolderStyle=$false },
    @{ Id='script.module.beautifulsoup4';    Source='kodi';     Datadir='https://mirrors.kodi.tv/addons/omega'; FolderStyle=$true },
    @{ Id='script.module.inputstreamhelper'; Source='kodi';     Datadir='https://mirrors.kodi.tv/addons/omega'; FolderStyle=$true },
    @{ Id='script.module.kodi-six';          Source='kodi';     Datadir='https://mirrors.kodi.tv/addons/omega'; FolderStyle=$true },
    @{ Id='script.module.simplejson';        Source='kodi';     Datadir='https://mirrors.kodi.tv/addons/omega'; FolderStyle=$true },
    @{ Id='script.module.six';               Source='kodi';     Datadir='https://mirrors.kodi.tv/addons/omega'; FolderStyle=$true },
    @{ Id='plugin.video.youtube';            Source='kodi';     Datadir='https://mirrors.kodi.tv/addons/omega'; FolderStyle=$true },
    @{ Id='script.module.requests';          Source='local';    LocalZip='script.module.requests-2.31.0.zip' },
    @{ Id='script.module.certifi';           Source='local';    LocalZip='script.module.certifi-2023.5.7.zip' },
    @{ Id='script.module.chardet';           Source='local';    LocalZip='script.module.chardet-5.1.0.zip' },
    @{ Id='script.module.idna';              Source='local';    LocalZip='script.module.idna-3.4.0.zip' },
    @{ Id='script.module.urllib3';           Source='local';    LocalZip='script.module.urllib3-1.26.16+matrix.1.zip' }
)

function Get-NodeXml([string]$sourceName, [string]$id) {
    switch ($sourceName) {
        'crew' { return (($crew.addons.addon | Where-Object { $_.id -eq $id } | Select-Object -First 1).OuterXml) }
        'unhinged' { return (($unhinged.addons.addon | Where-Object { $_.id -eq $id } | Select-Object -First 1).OuterXml) }
        'kodi' { return (($kodi.addons.addon | Where-Object { $_.id -eq $id } | Select-Object -First 1).OuterXml) }
        default { return $null }
    }
}

# Clean mirrored payload but keep repo addon folder and feed files.
Get-ChildItem -LiteralPath $repo | ForEach-Object {
    if ($_.Name -eq $repoId -or $_.Name -eq 'addons.xml' -or $_.Name -eq 'addons.xml.md5') {
        return
    }
    Remove-Item -LiteralPath $_.FullName -Recurse -Force
}

$addonBlocks = New-Object System.Collections.Generic.List[string]

foreach ($p in $plan) {
    $id = [string]$p.Id
    $source = [string]$p.Source
    $zipName = $null
    $nodeXml = $null

    if ($source -eq 'local') {
        $zipPath = [string]$p.LocalZip
        Require-File $zipPath
        $zipName = Split-Path $zipPath -Leaf

        $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $zipPath))
        try {
            $entry = $zip.Entries | Where-Object { $_.FullName -eq ($id + '/addon.xml') } | Select-Object -First 1
            if (-not $entry) {
                throw "addon.xml not found in zip for $id"
            }
            $reader = New-Object IO.StreamReader($entry.Open())
            $fullXml = $reader.ReadToEnd()
            $reader.Close()

            [xml]$doc = $fullXml
            $nodeXml = $doc.addon.OuterXml
        }
        finally {
            $zip.Dispose()
        }

        Copy-Item -LiteralPath $zipPath -Destination (Join-Path $repo $zipName) -Force
    }
    else {
        $nodeXml = Get-NodeXml $source $id
        if ([string]::IsNullOrWhiteSpace($nodeXml)) {
            throw "Missing addon metadata for $id from $source"
        }

        [xml]$nodeDoc = $nodeXml
        $ver = [string]$nodeDoc.addon.version
        if ([string]::IsNullOrWhiteSpace($ver)) {
            throw "Missing version for $id from $source"
        }
        $zipName = "$id-$ver.zip"

        $datadir = [string]$p.Datadir
        $candidates = @()
        if ($p.FolderStyle) {
            $candidates += ($datadir.TrimEnd('/') + '/' + $id + '/' + $zipName)
            $candidates += ($datadir.TrimEnd('/') + '/' + $zipName)
        }
        else {
            $candidates += ($datadir.TrimEnd('/') + '/' + $zipName)
            $candidates += ($datadir.TrimEnd('/') + '/' + $id + '/' + $zipName)
        }

        $downloadUrl = $null
        foreach ($u in $candidates) {
            try {
                $h = Invoke-WebRequest -UseBasicParsing -Method Head -Uri $u -TimeoutSec 30
                if ($h.StatusCode -ge 200 -and $h.StatusCode -lt 400) {
                    $downloadUrl = $u
                    break
                }
            }
            catch {
            }
        }

        if (-not $downloadUrl) {
            throw "Could not resolve zip URL for $id"
        }

        Invoke-WebRequest -UseBasicParsing -Uri $downloadUrl -OutFile (Join-Path $repo $zipName) -TimeoutSec 180
    }

    $addonDir = Join-Path $repo $id
    New-Item -ItemType Directory -Path $addonDir -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $repo $zipName) -Destination (Join-Path $addonDir $zipName) -Force

    $addonBlocks.Add($nodeXml)
    Write-Output ("MIRRORED $id -> $zipName")
}

$addonsXml = "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?>`n<addons>`n$repoAddonBody`n$($addonBlocks -join "`n")`n</addons>`n"
Set-Content -LiteralPath (Join-Path $repo 'addons.xml') -Value $addonsXml -Encoding UTF8

$content = Get-Content -LiteralPath (Join-Path $repo 'addons.xml') -Raw
$lf = $content -replace "`r`n", "`n"
$bytes = [System.Text.Encoding]::UTF8.GetBytes($lf)
$md5 = ([BitConverter]::ToString([System.Security.Cryptography.MD5]::Create().ComputeHash($bytes)) -replace '-', '').ToLower()
Set-Content -LiteralPath (Join-Path $repo 'addons.xml.md5') -Value $md5 -NoNewline

powershell -NoProfile -ExecutionPolicy Bypass -File '.\tools\validate-repo.ps1' -RepoRoot '.\repo_thecrew'
Write-Output ("THECREW_STANDALONE_BUILD_OK MD5=$md5")
