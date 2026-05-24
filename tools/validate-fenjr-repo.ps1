$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'

if (!(Test-Path 'repo_fenjr\addons.xml')) { throw 'Missing repo_fenjr/addons.xml' }
if (!(Test-Path 'repo_fenjr\repository.fenjr\addon.xml')) { throw 'Missing repo_fenjr/repository.fenjr/addon.xml' }
if (!(Test-Path 'repo_fenjr\repository.fenjr-1.0.1.zip')) { throw 'Missing repo_fenjr/repository.fenjr-1.0.1.zip' }

Write-Host 'Repository zip entries:'
tar -tf 'repo_fenjr\repository.fenjr-1.0.1.zip'

$md5 = (Get-FileHash -Algorithm MD5 'repo_fenjr\addons.xml').Hash.ToLower()
$md5File = (Get-Content 'repo_fenjr\addons.xml.md5' -Raw).Trim().ToLower()
if ($md5 -ne $md5File) {
    throw ('MD5 mismatch local: computed=' + $md5 + ' file=' + $md5File)
}

$urls = @(
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenjr/addons.xml',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenjr/addons.xml.md5',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenjr/repository.fenjr-1.0.1.zip'
)

foreach ($u in $urls) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Method Head -Uri $u -TimeoutSec 30
        Write-Host ('OK ' + $r.StatusCode + ' ' + $u)
    }
    catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code) {
            Write-Host ('ERR ' + $code + ' ' + $u)
        }
        else {
            Write-Host ('ERR ' + $_.Exception.Message + ' ' + $u)
        }
    }
}

Write-Host 'FENJR_VALIDATE_DONE'
