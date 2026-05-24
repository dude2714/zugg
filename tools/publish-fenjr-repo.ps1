$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'

powershell -NoProfile -ExecutionPolicy Bypass -File 'tools\build-fenjr-repo.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File 'tools\validate-fenjr-repo.ps1'
git add -- repo_fenjr tools\build-fenjr-repo.ps1 tools\validate-fenjr-repo.ps1 tools\publish-fenjr-repo.ps1 .vscode\tasks.json
$staged = git diff --cached --name-only
if ($staged) {
    git commit -m 'Fen Jr: add one-click publish and validation tasks'
    git push origin master
}
else {
    Write-Host 'No staged changes to commit.'
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
