# ThePromise Publish Checklist

## 1) Set the GitHub publish target

Run this from PowerShell:

powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\set-publish-target.ps1 -Owner dude2714 -Repo zugg -Branch master

Adjust Owner/Repo/Branch to match your real remote.

## 2) Confirm required files exist

Expected files at repository root:
- repository.thepromise-1.0.0.zip
- plugin.video.thepromise-22.4.29.zip
- script.module.promisescrapers-22.4.29.zip
- addons.xml
- addons.xml.md5

## 3) Optional quick local checks

- Open addons.xml and verify addon ids:
  - repository.thepromise
  - plugin.video.thepromise
  - script.module.promisescrapers
- Recompute checksum and compare with addons.xml.md5.

## 4) Publish to GitHub

1. Create a new repo (or use an existing one).
2. Upload all files/folders from this thepromise directory to the repo root.
3. Push to the branch used in set-publish-target.ps1.

## 5) Validate live URLs

After pushing, check:
- https://<owner>.github.io/<repo>/addons.xml
- https://<owner>.github.io/<repo>/addons.xml.md5
- https://<owner>.github.io/<repo>/repository.thepromise-1.0.0.zip

All should return HTTP 200.

## 6) Install in Kodi

1. Install from zip: repository.thepromise-1.0.0.zip
2. Install ThePromise from ThePromise Repository
3. Confirm PromiseScrapers module auto-installs as dependency

## Notes

- If versions change, rebuild/add new zip names and update addons.xml entries.
- Keep addons.xml.md5 synchronized every time addons.xml changes.

