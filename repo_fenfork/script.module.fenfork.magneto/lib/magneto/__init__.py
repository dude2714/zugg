from magneto.sources_magneto.torrents.torrentio import source as torrentio_source
from magneto.sources_magneto.torrents.piratebay import source as piratebay_source


def sources(specified_folders=None, ret_all=False):
    # Legacy external scraper API fallback used by Fen/Fen Fork.
    providers = [("torrentio", torrentio_source), ("piratebay", piratebay_source)]
    if ret_all:
        return providers

    try:
        import xbmcaddon

        enabled = []
        for addon_id in ("script.module.fenfork.magneto", "script.module.magneto"):
            try:
                addon = xbmcaddon.Addon(addon_id)
                enabled = [
                    (name, cls)
                    for name, cls in providers
                    if addon.getSetting("provider.%s" % name) == "true"
                ]
                break
            except Exception:
                continue
        return enabled or providers
    except Exception:
        return providers
