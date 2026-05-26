param(
    [string]$Owner = "dude2714",
    [string]$Repo = "zugg",
    [string]$Branch = "HEAD"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$repoAddonXmlPath = Join-Path $root "repository.thepromise\addon.xml"
$addonsXmlPath = Join-Path $root "addons.xml"
$addonsMd5Path = Join-Path $root "addons.xml.md5"

if (-not (Test-Path $repoAddonXmlPath)) {
    throw "Missing repository addon xml: $repoAddonXmlPath"
}
if (-not (Test-Path $addonsXmlPath)) {
    throw "Missing addons.xml: $addonsXmlPath"
}

$base = "https://raw.githubusercontent.com/$Owner/$Repo/$Branch"
$infoUrl = "$base/addons.xml"
$checksumUrl = "$base/addons.xml.md5"
$datadirUrl = "$base/"

# Update URLs in repository addon.xml and addons.xml
$pathsToUpdate = @($repoAddonXmlPath, $addonsXmlPath)
foreach ($path in $pathsToUpdate) {
    $content = Get-Content -LiteralPath $path -Raw

    $infoReplacement = '<info compressed="false">{0}</info>' -f $infoUrl
    $checksumReplacement = '<checksum>{0}</checksum>' -f $checksumUrl
    $datadirReplacement = '<datadir zip="true">{0}</datadir>' -f $datadirUrl

    $content = [regex]::Replace(
        $content,
        '<info compressed="false">https://raw\.githubusercontent\.com/[^<]+/addons\.xml</info>',
        $infoReplacement
    )
    $content = [regex]::Replace(
        $content,
        '<checksum>https://raw\.githubusercontent\.com/[^<]+/addons\.xml\.md5</checksum>',
        $checksumReplacement
    )
    $content = [regex]::Replace(
        $content,
        '<datadir zip="true">https://raw\.githubusercontent\.com/[^<]+/</datadir>',
        $datadirReplacement
    )

    if ($path -like '*addons.xml') {
        if ($content.Length -gt 0 -and [int][char]$content[0] -eq 0xFEFF) {
            $content = $content.Substring(1)
        }
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
    } else {
        Set-Content -LiteralPath $path -Value $content -Encoding UTF8
    }
}

# Refresh addons.xml.md5
$hash = (Get-FileHash -Algorithm MD5 $addonsXmlPath).Hash.ToLower()
Set-Content -LiteralPath $addonsMd5Path -Value $hash -NoNewline

Write-Output "Updated publish target to $Owner/$Repo@$Branch"
Write-Output "info     : $infoUrl"
Write-Output "checksum : $checksumUrl"
Write-Output "datadir  : $datadirUrl"
Write-Output "addons.md5: $hash"
