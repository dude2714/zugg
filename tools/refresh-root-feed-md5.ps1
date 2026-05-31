$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'

$content = Get-Content -LiteralPath 'addons.xml' -Raw
$lf = $content -replace "`r`n", "`n"
$bytes = [System.Text.Encoding]::UTF8.GetBytes($lf)
$md5 = ([BitConverter]::ToString([System.Security.Cryptography.MD5]::Create().ComputeHash($bytes)) -replace '-', '').ToLower()
Set-Content -LiteralPath 'addons.xml.md5' -Value $md5 -NoNewline

if (!(Test-Path 'repository.ally-1.0.0.zip')) {
    Copy-Item -LiteralPath 'repo_ally\repository.ally-1.0.0.zip' -Destination 'repository.ally-1.0.0.zip' -Force
}

Write-Output ("ROOT_ADDONS_MD5={0}" -f $md5)
Get-Item -LiteralPath 'repository.ally-1.0.0.zip' | Select-Object Name, Length | Format-Table -AutoSize
