# -*- coding: utf-8 -*-
from sys import argv
from apis.torbox_api import TorBoxAPI
from modules import kodi_utils
from modules.source_utils import supported_video_extensions
from modules.utils import clean_file_name, normalize

ls = kodi_utils.local_string
build_url = kodi_utils.build_url
make_listitem = kodi_utils.make_listitem
default_tb_icon = kodi_utils.translate_path('special://home/addons/plugin.video.fenjr/resources/media/premiumize.png')
fanart = kodi_utils.translate_path('special://home/addons/plugin.video.fenjr/fanart.png')
folder_str, file_str, down_str = ls(32742).upper(), ls(32743).upper(), ls(32747)
extensions = supported_video_extensions()
TorBox = TorBoxAPI()


def _cloud_items():
	raw_items = TorBox.user_cloud() or []
	if isinstance(raw_items, dict):
		raw_items = raw_items.get('data') or raw_items.get('results') or raw_items.get('torrents') or []
	if not isinstance(raw_items, list):
		return []
	return raw_items


def tb_torrent_cloud():
	def _builder():
		for count, item in enumerate(cloud_items, 1):
			try:
				transfer_id = item.get('id') or item.get('torrent_id')
				if not transfer_id:
					continue
				files = TorBox._file_list(item)
				if not any(TorBox._video_file(entry) for entry in files):
					continue
				folder_name = item.get('name') or item.get('title') or item.get('hash') or str(transfer_id)
				display = '%02d | [B]%s[/B] | [I]%s [/I]' % (count, folder_str, clean_file_name(normalize(folder_name)).upper())
				url = build_url({'mode': 'torbox.browse_tb_cloud', 'id': transfer_id})
				listitem = make_listitem()
				listitem.setLabel(display)
				listitem.setArt({'icon': default_tb_icon, 'poster': default_tb_icon, 'thumb': default_tb_icon, 'fanart': fanart, 'banner': default_tb_icon})
				yield (url, listitem, True)
			except:
				pass
	cloud_items = _cloud_items()
	__handle__ = int(argv[1])
	kodi_utils.add_items(__handle__, list(_builder()))
	kodi_utils.set_content(__handle__, 'files')
	kodi_utils.end_directory(__handle__)
	kodi_utils.set_view_mode('view.premium')


def browse_tb_cloud(transfer_id):
	def _builder():
		for count, item in enumerate(files, 1):
			try:
				name = clean_file_name(normalize(TorBox._file_name(item))).upper()
				if not name.lower().endswith(tuple(extensions)):
					continue
				file_id = item.get('id') or item.get('file_id') or 0
				url_link = '%s:%s' % (transfer_id, file_id)
				size = float(item.get('size', 0) or 0) / 1073741824
				display = '%02d | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, file_str, size, name)
				url = build_url({'mode': 'torbox.resolve_tb', 'url': url_link, 'play': 'true'})
				down_file_params = {'mode': 'downloader', 'name': name, 'url': url_link, 'action': 'cloud.torbox', 'image': default_tb_icon}
				listitem = make_listitem()
				listitem.setLabel(display)
				listitem.addContextMenuItems([(down_str, 'RunPlugin(%s)' % build_url(down_file_params))])
				listitem.setArt({'icon': default_tb_icon, 'poster': default_tb_icon, 'thumb': default_tb_icon, 'fanart': fanart, 'banner': default_tb_icon})
				listitem.setInfo('video', {})
				yield (url, listitem, False)
			except:
				pass
	transfer_info = TorBox.list_transfer(transfer_id)
	files = [item for item in TorBox._file_list(transfer_info) if TorBox._video_file(item)]
	__handle__ = int(argv[1])
	kodi_utils.add_items(__handle__, list(_builder()))
	kodi_utils.set_content(__handle__, 'files')
	kodi_utils.end_directory(__handle__)
	kodi_utils.set_view_mode('view.premium')


def resolve_tb(params):
	url = params['url']
	resolved_link = TorBox.unrestrict_link(url)
	if params.get('play', 'false') != 'true':
		return resolved_link
	from modules.player import FenPlayer
	FenPlayer().run(resolved_link, 'video')


def tb_account_info():
	try:
		kodi_utils.show_busy_dialog()
		account_info = TorBox.account_info()
		body = []
		append = body.append
		if account_info.get('email'):
			append(ls(32758) % account_info['email'])
		if account_info.get('username'):
			append(ls(32755) % account_info['username'])
		account_id = account_info.get('auth_id') or account_info.get('id') or account_info.get('customer_id') or account_info.get('sub')
		if account_id:
			append('%s: %s' % (ls(32056), account_id))
		status = account_info.get('plan') or account_info.get('type') or account_info.get('status')
		if status:
			append(ls(32757) % status)
		if not body:
			append(str(account_info))
		kodi_utils.hide_busy_dialog()
		return kodi_utils.show_text('TORBOX', '\n\n'.join(body), font_size='large')
	except:
		kodi_utils.hide_busy_dialog()