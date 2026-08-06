# -*- coding: utf-8 -*-
import sys
from modules.router import routing
from modules.kodi_utils import external_browse, get_infolabel
from modules.settings_reader import get_setting

routing(sys.argv[2])

if get_setting('reuse_language_invoker', 'true') == 'true' and external_browse():
	if 'fen' not in get_infolabel('Container.PluginName'):
		sys.exit(1)

