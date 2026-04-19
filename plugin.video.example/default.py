"""
Kodi Video Addon Template - default.py
=======================================
This is the main entry point for the Kodi video addon.
Kodi calls this script each time the plugin is invoked (e.g. when a user
opens the addon or selects an item in a listing).

URL routing is handled by parsing sys.argv:
  sys.argv[0]  - the plugin base URL  (e.g. plugin://plugin.video.example/)
  sys.argv[1]  - the handle           (integer, used by xbmcplugin calls)
  sys.argv[2]  - the query string     (e.g. ?action=listing&category=movies)
  sys.argv[3]  - 'resume:true' when Kodi wants to resume a previously started
                 playback (optional, Kodi 18+)
"""

import sys
from urllib.parse import urlencode, parse_qsl, urlparse

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# ---------------------------------------------------------------------------
# Addon globals
# ---------------------------------------------------------------------------
# Retrieve the running addon instance so we can read settings and info.
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')           # e.g. 'plugin.video.example'
ADDON_NAME = ADDON.getAddonInfo('name')       # e.g. 'Example Video Addon'
ADDON_PATH = ADDON.getAddonInfo('path')       # filesystem path to the addon folder

# The handle is used in every xbmcplugin call so Kodi knows which addon/request
# is being answered.
HANDLE = int(sys.argv[1])

# The full base URL of this plugin (e.g. plugin://plugin.video.example/)
BASE_URL = sys.argv[0]


# ---------------------------------------------------------------------------
# Helper: build a plugin URL with optional query parameters
# ---------------------------------------------------------------------------
def build_url(params: dict) -> str:
    """Return a plugin:// URL with the given query parameters.

    Example::

        build_url({'action': 'listing', 'category': 'movies'})
        # -> 'plugin://plugin.video.example/?action=listing&category=movies'
    """
    return '{0}?{1}'.format(BASE_URL, urlencode(params))


# ---------------------------------------------------------------------------
# Helper: parse the query string from sys.argv[2]
# ---------------------------------------------------------------------------
def get_params() -> dict:
    """Parse and return the query-string parameters passed to this invocation."""
    return dict(parse_qsl(urlparse(sys.argv[2]).query))


# ---------------------------------------------------------------------------
# Content: main menu
# ---------------------------------------------------------------------------
CATEGORIES = [
    {'title': 'Movies',    'action': 'listing', 'category': 'movies'},
    {'title': 'TV Shows',  'action': 'listing', 'category': 'tvshows'},
    {'title': 'Settings',  'action': 'settings'},
]


def list_categories():
    """Build the main menu listing."""
    # Tell Kodi what type of content this directory contains.
    # Common values: 'movies', 'tvshows', 'episodes', 'musicvideos', 'files'
    xbmcplugin.setContent(HANDLE, 'files')

    for entry in CATEGORIES:
        # Create a list item with a display label.
        list_item = xbmcgui.ListItem(label=entry['title'])

        # Set additional metadata (art, info, etc.) for the item.
        list_item.setArt({
            # 'icon':   'path/to/icon.png',   # small square icon
            # 'thumb':  'path/to/thumb.png',  # thumbnail (used in list/grid views)
            # 'fanart': 'path/to/fanart.jpg', # full-screen background image
        })

        # Build the URL that Kodi will call when this item is selected.
        url = build_url({k: v for k, v in entry.items() if k != 'title'})

        # is_folder=True means this item opens another directory level;
        # is_folder=False means it plays a media item directly.
        is_folder = entry.get('action') != 'settings'
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    # Sort items by label (other options: xbmcplugin.SORT_METHOD_DATE, etc.)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    # Signal that we have finished populating the directory.
    xbmcplugin.endOfDirectory(HANDLE)


# ---------------------------------------------------------------------------
# Content: video listing for a category
# ---------------------------------------------------------------------------
def list_videos(category: str):
    """Build a listing of playable videos for *category*.

    Replace the VIDEOS dict with real data (API calls, scraping, local files,
    etc.) for your own addon.
    """
    # Example hard-coded video data - replace with your own data source.
    VIDEOS = {
        'movies': [
            {
                'title': 'Big Buck Bunny',
                'url': 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                'thumb': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/320px-Camponotus_flavomarginatus_ant.jpg',
                'plot': 'A short animated film about a big rabbit.',
                'year': 2008,
            },
            {
                'title': 'Elephant Dream',
                'url': 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantDream.mp4',
                'thumb': '',
                'plot': 'The first open-source animated film.',
                'year': 2006,
            },
        ],
        'tvshows': [
            {
                'title': 'Sample Episode',
                'url': 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4',
                'thumb': '',
                'plot': 'A sample TV show episode.',
                'year': 2020,
            },
        ],
    }

    xbmcplugin.setContent(HANDLE, category)  # 'movies', 'tvshows', etc.

    for video in VIDEOS.get(category, []):
        list_item = xbmcgui.ListItem(label=video['title'])

        # Set the media info so Kodi can display it in the info dialog.
        list_item.setInfo('video', {
            'title':  video['title'],
            'plot':   video['plot'],
            'year':   video['year'],
            'mediatype': 'movie' if category == 'movies' else 'episode',
        })

        list_item.setArt({'thumb': video['thumb']})

        # Mark this as a playable item (not a sub-folder).
        list_item.setProperty('IsPlayable', 'true')

        url = build_url({'action': 'play', 'video': video['url']})
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, False)

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


# ---------------------------------------------------------------------------
# Playback
# ---------------------------------------------------------------------------
def play_video(url: str):
    """Pass *url* to Kodi for playback."""
    play_item = xbmcgui.ListItem(path=url)
    # Resolve the URL: Kodi will start playback of this item.
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def open_settings():
    """Open the addon settings dialog."""
    ADDON.openSettings()


# ---------------------------------------------------------------------------
# Router - dispatch based on the 'action' query parameter
# ---------------------------------------------------------------------------
def router(params: dict):
    """Route the plugin call to the appropriate function.

    Add new ``elif`` branches here to support additional actions/pages in
    your addon.
    """
    action = params.get('action')

    if not action:
        # No action → show the main menu.
        list_categories()

    elif action == 'listing':
        category = params.get('category', 'movies')
        list_videos(category)

    elif action == 'play':
        video_url = params.get('video')
        if video_url:
            play_video(video_url)
        else:
            xbmc.log('{0}: "play" action called without a video URL'.format(ADDON_ID),
                     xbmc.LOGERROR)

    elif action == 'settings':
        open_settings()

    else:
        # Unknown action - log a warning and show the main menu as a fallback.
        xbmc.log('{0}: unknown action "{1}"'.format(ADDON_ID, action), xbmc.LOGWARNING)
        list_categories()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # Parse the query string and hand off to the router.
    router(get_params())
