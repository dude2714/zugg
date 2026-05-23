# Split Repository Publish Commands

Run these commands from:

C:/Users/johns/OneDrive/Desktop/123Venom.github.io

## 1) Verify local feed validity

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-repo.ps1 -RepoRoot .
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-repo.ps1 -RepoRoot .\repo_pov
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-repo.ps1 -RepoRoot .\repo_fenfork
```

## 2) Commit split-feed prep in current repo

```powershell
git add -- addons.xml addons.xml.md5 repo_pov repo_fenfork tools/build-split-repos.ps1 SPLIT_REPO_PUBLISH.md
git commit -m "Split POV and Fen Fork into dedicated feeds"
git push origin master
```

## 3) Publish split feeds to GitHub Pages branch in this repository

GitHub Pages for this repo is currently served from `main`, so after updating split repo files on `master`, mirror the same split changes onto `main`.

## 4) Publish POV feed to its own repository (recommended)

Create a separate GitHub repo, then from this workspace run:

```powershell
git subtree split --prefix repo_pov -b temp-repo-pov
git push <POV_REMOTE_URL> temp-repo-pov:main
git branch -D temp-repo-pov
```

## 5) Publish Fen Fork feed to its own repository (recommended)

```powershell
git subtree split --prefix repo_fenfork -b temp-repo-fenfork
git push <FENFORK_REMOTE_URL> temp-repo-fenfork:main
git branch -D temp-repo-fenfork
```

## 6) Update feed URLs after separate repos are live

If you publish into separate repos, replace URLs in these files:

- repo_pov/addons.xml
- repo_pov/repository.pov/addon.xml
- repo_fenfork/addons.xml
- repo_fenfork/repository.fenfork/addon.xml

Then rebuild checksums and repo zips:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build-split-repos.ps1
```
