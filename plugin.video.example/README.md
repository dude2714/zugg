# plugin.video.example — Kodi Addon Template

A minimal, well-commented starter template for building **Kodi video addons** with Python.

---

## Directory Structure

```
plugin.video.example/
├── addon.xml                   # Addon metadata (id, name, version, dependencies)
├── default.py                  # Main entry-point script (all plugin logic lives here)
├── LICENSE.txt                 # MIT License
├── README.md                   # This file
└── resources/
    └── settings.xml            # User-configurable settings (shown in addon dialog)
```

Optional assets you may want to add:

```
resources/
├── icon.png          # Square addon icon  (256 × 256 px recommended)
├── fanart.jpg        # Full-screen background image  (1280 × 720 px minimum)
└── language/
    └── English/
        └── strings.po    # Localised strings
```

---

## Quick Start

### 1. Copy & rename the template

```bash
cp -r plugin.video.example  plugin.video.yourname
```

### 2. Update `addon.xml`

| Attribute / Element | What to change |
|---|---|
| `id` | `plugin.video.yourname` (must match the directory name) |
| `name` | Human-readable addon name |
| `version` | Start at `1.0.0`; increment following [Semantic Versioning](https://semver.org/) |
| `provider-name` | Your name or team name |
| `<summary>` / `<description>` | Short and long descriptions shown in the addon browser |
| `<source>` | URL of your source repository |

### 3. Edit `default.py`

The file is heavily commented to guide you through the key concepts:

* **`CATEGORIES`** — edit or extend the main-menu entries.
* **`list_videos()`** — replace the hard-coded `VIDEOS` dict with a real data
  source (web API, local files, scraping, etc.).
* **`router()`** — add new `elif action == '…'` branches for additional pages.

### 4. Configure `resources/settings.xml`

Add, remove, or edit `<setting>` elements to match the options your addon needs.
Read them in Python with:

```python
import xbmcaddon
ADDON = xbmcaddon.Addon()
api_key = ADDON.getSetting('api_key')
enable_hd = ADDON.getSettingBool('enable_hd')   # returns bool (Kodi 18+)
```

### 5. Install for testing

1. Zip the **entire** `plugin.video.example` directory (the zip must contain the
   folder itself, not just its contents):
   ```bash
   zip -r plugin.video.example.zip plugin.video.example/
   ```
2. In Kodi: **Settings → Add-ons → Install from zip file** → select the zip.
3. The addon will appear under **Videos → Add-ons**.

---

## Development Tips

* **Logging** — use `xbmc.log()` for debug output visible in the Kodi log
  (`~/.kodi/temp/kodi.log` on Linux):
  ```python
  import xbmc
  xbmc.log('My debug message', xbmc.LOGDEBUG)
  ```
* **Reload without restart** — most code changes take effect when you re-open
  the addon; a full Kodi restart is only needed for `addon.xml` changes.
* **Kodi add-on development docs** — <https://kodi.wiki/view/Add-on_development>
* **Official Python API reference** — <https://codedocs.xyz/xbmc/xbmc/>

---

## License

This template is released under the [MIT License](LICENSE.txt).
Feel free to use it as the basis for your own addons without restriction.
