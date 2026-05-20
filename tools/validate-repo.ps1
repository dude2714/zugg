param(
    [string]$RepoRoot = "."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$repoPath = (Resolve-Path $RepoRoot).Path
$addonsXmlPath = Join-Path $repoPath "addons.xml"
$md5Path = Join-Path $repoPath "addons.xml.md5"

if (-not (Test-Path $addonsXmlPath)) {
    throw "addons.xml not found at $addonsXmlPath"
}

[xml]$doc = Get-Content $addonsXmlPath -Raw
$addons = @($doc.addons.addon)
if ($addons.Count -eq 0) {
    throw "No addon entries found in addons.xml"
}

$errors = New-Object System.Collections.Generic.List[string]

foreach ($addon in $addons) {
    $id = [string]$addon.id
    $version = [string]$addon.version

    if ([string]::IsNullOrWhiteSpace($id) -or [string]::IsNullOrWhiteSpace($version)) {
        $errors.Add("Invalid addon entry with missing id/version")
        continue
    }

    if ($id -eq "repository.venom") {
        $zipPath = Join-Path $repoPath ("repository.venom-{0}.zip" -f $version)
    }
    else {
        $zipPath = Join-Path $repoPath ("{0}-{1}.zip" -f $id, $version)
    }

    if (-not (Test-Path $zipPath)) {
        $errors.Add("Missing zip for ${id} ${version}: $(Split-Path $zipPath -Leaf)")
        continue
    }

    try {
        $zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
        $expectedAddonXmlEntry = "$id/addon.xml"
        $entry = $zip.Entries | Where-Object { $_.FullName.Replace('\', '/') -eq $expectedAddonXmlEntry } | Select-Object -First 1

        if (-not $entry) {
            $errors.Add("$($id)-$($version).zip missing $expectedAddonXmlEntry")
            $zip.Dispose()
            continue
        }

        $reader = New-Object System.IO.StreamReader($entry.Open())
        $embeddedXml = $reader.ReadToEnd()
        $reader.Close()
        $zip.Dispose()

        [xml]$embeddedDoc = $embeddedXml
        $embeddedVersion = [string]$embeddedDoc.addon.version

        if ($embeddedVersion -ne $version) {
            $errors.Add("Version mismatch for ${id}: addons.xml=$version, zip addon.xml=$embeddedVersion")
        }
    }
    catch {
        $errors.Add("Could not validate zip for ${id} ${version}: $($_.Exception.Message)")
    }
}

$content = Get-Content $addonsXmlPath -Raw
$lf = $content -replace "`r`n", "`n"
$bytes = [System.Text.Encoding]::UTF8.GetBytes($lf)
$md5 = [System.Security.Cryptography.MD5]::Create()
$hash = ([BitConverter]::ToString($md5.ComputeHash($bytes)) -replace '-', '').ToLower()

if (Test-Path $md5Path) {
    $current = (Get-Content $md5Path -Raw).Trim()
    if ($current -ne $hash) {
        $errors.Add("addons.xml.md5 mismatch: file=$current expected=$hash")
    }
}
else {
    $errors.Add("addons.xml.md5 missing")
}

if ($errors.Count -gt 0) {
    Write-Host "Validation FAILED:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "Validation PASSED" -ForegroundColor Green
Write-Host "Addons checked: $($addons.Count)"
Write-Host "addons.xml.md5: $hash"