# dude2714/zugg

Repository feeds hosted from this repository.

## Split Repositories (Active)

### POV

- Repository zip:
	- https://raw.githubusercontent.com/dude2714/zugg/master/repository.pov-1.0.9.zip
- Feed XML:
	- https://dude2714.github.io/zugg/repo_pov/addons.xml
- Data directory:
	- https://dude2714.github.io/zugg/repo_pov/

### Fen Fork

- Repository zip:
	- https://github.com/dude2714/zugg/raw/master/repo_fenfork/repository.fenfork-1.0.9.zip
- Feed XML:
	- https://dude2714.github.io/zugg/repo_fenfork/addons.xml
- Data directory:
	- https://dude2714.github.io/zugg/repo_fenfork/

## Kodi Setup (Split Repos)

1. Open Kodi and go to Add-ons.
2. Choose Install from zip file.
3. Install one or both repository zips above:
	- `repository.pov-1.0.9.zip`
	- `repository.fenfork-1.0.9.zip`
4. Open Install from repository.
5. Install POV from POV Repo, and/or Fen Fork from Fen Fork Repo.

## Maintenance

- Rebuild split repo artifacts:
	- `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build-split-repos.ps1`
- Run split health checks:
	- `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\check-split-repos.ps1`
