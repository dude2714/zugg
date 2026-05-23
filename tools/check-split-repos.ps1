$ErrorActionPreference = 'Stop'

$base = 'C:\Users\johns\OneDrive\Desktop\123Venom.github.io'
$validateScript = Join-Path $base 'tools\validate-repo.ps1'

$repos = @(
    @{ Name = 'Root'; Path = $base },
    @{ Name = 'POV'; Path = (Join-Path $base 'repo_pov') },
    @{ Name = 'FenFork'; Path = (Join-Path $base 'repo_fenfork') }
)

Write-Output '=== Local Feed Validation ==='
foreach ($repo in $repos) {
    Write-Output ("-- {0}" -f $repo.Name)
    & powershell -NoProfile -ExecutionPolicy Bypass -File $validateScript -RepoRoot $repo.Path
}

$urls = @(
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_pov/addons.xml',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_pov/addons.xml.md5',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_pov/repository.pov-1.0.0.zip',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_pov/plugin.video.pov-6.05.11.zip',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenfork/addons.xml',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenfork/addons.xml.md5',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenfork/repository.fenfork-1.0.0.zip',
    'https://raw.githubusercontent.com/dude2714/zugg/master/repo_fenfork/plugin.video.fenfork-3.5.08.zip'
)

Write-Output '=== Remote URL Checks ==='
foreach ($url in $urls) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $url -Method Head -TimeoutSec 30
        Write-Output ("OK  {0} STATUS={1} LEN={2}" -f $url, $response.StatusCode, $response.Headers.'Content-Length')
    }
    catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code) {
            Write-Output ("ERR {0} STATUS={1}" -f $url, $code)
        }
        else {
            Write-Output ("ERR {0} MSG={1}" -f $url, $_.Exception.Message)
        }
        exit 1
    }
}

Write-Output 'SPLIT_REPO_CHECKS_PASSED'
