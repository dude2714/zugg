$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'

$repo = 'repo_ally'
$repoId = 'repository.ally'
$repoVersion = '1.0.0'
$addonId = 'plugin.program.rdbridge'

New-Item -ItemType Directory -Path $repo -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $repo $repoId) -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $repo $addonId) -Force | Out-Null

[xml]$allyAddon = Get-Content -LiteralPath (Join-Path $addonId 'addon.xml')
$allyVersion = [string]$allyAddon.addon.version
if ([string]::IsNullOrWhiteSpace($allyVersion)) {
    throw 'Missing plugin.program.rdbridge version in addon.xml'
}
$allyZipName = "$addonId-$allyVersion.zip"

# Build addon zip with required top-level addon-id folder.
if (Test-Path $allyZipName) { Remove-Item -Force $allyZipName }
tar.exe -a -c -f $allyZipName $addonId

$repoAddonXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<addon id="repository.ally" name="[B][COLOR red]Ally[/COLOR] Repo[/B]" version="1.0.0" provider-name="johns">
  <requires>
    <import addon="xbmc.python" version="3.0.0" />
  </requires>
  <extension point="xbmc.addon.repository" name="Ally Repo">
    <dir>
      <info compressed="false">https://raw.githubusercontent.com/dude2714/zugg/master/repo_ally/addons.xml</info>
      <checksum>https://raw.githubusercontent.com/dude2714/zugg/master/repo_ally/addons.xml.md5</checksum>
      <datadir zip="true">https://raw.githubusercontent.com/dude2714/zugg/master/repo_ally/</datadir>
    </dir>
    <dir>
      <info compressed="false">https://dude2714.github.io/zugg/repo_ally/addons.xml</info>
      <checksum>https://dude2714.github.io/zugg/repo_ally/addons.xml.md5</checksum>
      <datadir zip="true">https://dude2714.github.io/zugg/repo_ally/</datadir>
    </dir>
  </extension>
  <extension point="xbmc.addon.metadata">
    <summary lang="en">Ally repository</summary>
    <description lang="en">Repository package for Ally only.</description>
    <platform>all</platform>
    <license>GNU GENERAL PUBLIC LICENSE. Version 3, 29 June 2007</license>
    <assets>
      <icon>icon.png</icon>
      <fanart>fanart.jpg</fanart>
    </assets>
  </extension>
</addon>
"@
Set-Content -LiteralPath (Join-Path $repo (Join-Path $repoId 'addon.xml')) -Value $repoAddonXml -Encoding UTF8 -NoNewline

Copy-Item -LiteralPath 'icon.png' -Destination (Join-Path $repo (Join-Path $repoId 'icon.png')) -Force
Copy-Item -LiteralPath 'fanart.jpg' -Destination (Join-Path $repo (Join-Path $repoId 'fanart.jpg')) -Force

$repoZipName = "$repoId-$repoVersion.zip"
$stage = '_ally_repo_stage'
Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $stage $repoId) -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repo (Join-Path $repoId 'addon.xml')) -Destination (Join-Path $stage (Join-Path $repoId 'addon.xml')) -Force
Copy-Item -LiteralPath (Join-Path $repo (Join-Path $repoId 'icon.png')) -Destination (Join-Path $stage (Join-Path $repoId 'icon.png')) -Force
Copy-Item -LiteralPath (Join-Path $repo (Join-Path $repoId 'fanart.jpg')) -Destination (Join-Path $stage (Join-Path $repoId 'fanart.jpg')) -Force

Push-Location $stage
if (Test-Path $repoZipName) { Remove-Item -Force $repoZipName }
tar.exe -a -c -f $repoZipName $repoId
Pop-Location

Copy-Item -LiteralPath (Join-Path $stage $repoZipName) -Destination (Join-Path $repo $repoZipName) -Force
Copy-Item -LiteralPath (Join-Path $stage $repoZipName) -Destination (Join-Path $repo (Join-Path $repoId $repoZipName)) -Force
Copy-Item -LiteralPath $allyZipName -Destination (Join-Path $repo $allyZipName) -Force
Copy-Item -LiteralPath $allyZipName -Destination (Join-Path $repo (Join-Path $addonId $allyZipName)) -Force

$repoAddonBody = (Get-Content -LiteralPath (Join-Path $repo (Join-Path $repoId 'addon.xml')) -Raw) -replace '^\s*<\?xml[^\n]*\?>\s*', ''
$allyAddonBody = (Get-Content -LiteralPath (Join-Path $addonId 'addon.xml') -Raw) -replace '^\s*<\?xml[^\n]*\?>\s*', ''
$addonsXml = "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?>`n<addons>`n$repoAddonBody`n$allyAddonBody`n</addons>`n"
Set-Content -LiteralPath (Join-Path $repo 'addons.xml') -Value $addonsXml -Encoding UTF8

$content = Get-Content -LiteralPath (Join-Path $repo 'addons.xml') -Raw
$lf = $content -replace "`r`n", "`n"
$bytes = [System.Text.Encoding]::UTF8.GetBytes($lf)
$md5 = ([BitConverter]::ToString([System.Security.Cryptography.MD5]::Create().ComputeHash($bytes)) -replace '-', '').ToLower()
Set-Content -LiteralPath (Join-Path $repo 'addons.xml.md5') -Value $md5 -NoNewline

if (Test-Path 'L:\') {
    Copy-Item -LiteralPath (Join-Path $repo $repoZipName) -Destination (Join-Path 'L:\' $repoZipName) -Force
    Copy-Item -LiteralPath (Join-Path $repo $allyZipName) -Destination (Join-Path 'L:\' $allyZipName) -Force
}

Write-Output ("ALLY_REPO_BUILT repo_zip={0} addon_zip={1} md5={2}" -f $repoZipName, $allyZipName, $md5)
