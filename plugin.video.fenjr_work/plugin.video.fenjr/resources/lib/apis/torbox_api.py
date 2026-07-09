# -*- coding: utf-8 -*-
import re
from sys import exit as sysexit
from caches.main_cache import cache_object
from modules.requests_utils import make_session
from modules.settings_reader import get_setting, set_setting
from modules import kodi_utils

base_url = 'https://api.torbox.app/v1/api/'
timeout = 20.0
session = make_session(base_url)

class TorBoxAPI:
	def __init__(self):
		self.token = get_setting('tb.token') or get_setting('tb.api_key')
		self.break_auth_loop = False

	def _headers(self):
		if not self.token:
			return {}
		return {'Authorization': 'Bearer %s' % self.token}

	def _get(self, endpoint, params=None, auth=True):
		result = None
		try:
			if auth and not self.token:
				return None
			url = base_url + endpoint
			headers = self._headers() if auth else None
			result = session.get(url, params=params or {}, headers=headers, timeout=timeout).json()
		except:
			pass
		return result

	def _post(self, endpoint, params=None, data=None, auth=True):
		result = None
		try:
			if auth and not self.token:
				return None
			url = base_url + endpoint
			headers = self._headers() if auth else None
			result = session.post(url, params=params or {}, json=data or {}, headers=headers, timeout=timeout).json()
		except:
			pass
		return result

	def _parse_data(self, response):
		if not response:
			return None
		if isinstance(response, dict):
			if 'data' in response and response.get('data') is not None:
				return response['data']
			if 'results' in response and response.get('results') is not None:
				return response['results']
		return response

	def _video_file(self, item):
		from modules.source_utils import supported_video_extensions
		extensions = supported_video_extensions()
		name = item.get('name') or item.get('short_name') or item.get('file_name') or ''
		name = name.lower()
		if not name:
			return False
		return any(name.endswith(ext) for ext in extensions)

	def auth_loop(self):
		kodi_utils.sleep(5000)
		response = self._post('user/auth/device/token', data={'device_code': self.device_code}, auth=False)
		if not response:
			return
		data = self._parse_data(response)
		if not data:
			if response.get('detail') in ('not_authorized', 'authorization_pending'):
				return
			if response.get('error'):
				self.token = 'failed'
				return kodi_utils.ok_dialog(text=32574, top_space=True)
			return
		token = data.get('token') or data.get('access_token') or data.get('api_key') or data.get('apikey')
		if token:
			try:
				kodi_utils.progressDialog.close()
			except:
				pass
			self.token = str(token)
			set_setting('tb.token', self.token)
			set_setting('tb.api_key', self.token)

	def auth(self):
		self.token = ''
		response = self._get('user/auth/device/start', params={'app': 'Fen Jr Kodi'}, auth=False)
		data = self._parse_data(response)
		if not data:
			return kodi_utils.ok_dialog(text=32574, top_space=True)
		verify_url = data.get('verification_url') or data.get('verification_uri') or data.get('url') or 'https://torbox.app/device'
		user_code = data.get('user_code') or data.get('code') or ''
		self.device_code = data.get('device_code')
		if not self.device_code:
			return kodi_utils.ok_dialog(text=32574, top_space=True)
		line = '%s[CR]%s[CR]%s'
		kodi_utils.progressDialog.create('Fen', '')
		kodi_utils.progressDialog.update(0, line % (kodi_utils.local_string(32517), kodi_utils.local_string(32700) % verify_url, kodi_utils.local_string(32701) % user_code))
		while not self.token:
			if self.break_auth_loop:
				break
			if kodi_utils.progressDialog.iscanceled():
				kodi_utils.progressDialog.close()
				break
			self.auth_loop()
		if self.token in (None, '', 'failed'):
			return
		account_info = self.account_info()
		if account_info:
			account_id = account_info.get('email') or account_info.get('username') or account_info.get('auth_id') or account_info.get('id')
			if account_id:
				set_setting('tb.account_id', str(account_id))
		kodi_utils.ok_dialog(text=32576, top_space=True)

	def account_info(self):
		response = self._get('user/me')
		result = self._parse_data(response)
		if isinstance(result, dict):
			return result
		return {}

	def check_cache(self, hashes):
		response = self._post('torrents/checkcached', params={'format': 'list'}, data={'hashes': hashes})
		result = self._parse_data(response)
		if isinstance(result, dict):
			return result
		if isinstance(result, list):
			return {'cached': result}
		return {'cached': []}

	def _extract_cached_hashes(self, cache_response):
		if not cache_response:
			return []
		cached = cache_response.get('cached') if isinstance(cache_response, dict) else cache_response
		if isinstance(cached, dict):
			if all(isinstance(v, (bool, int)) for v in cached.values()):
				cached = [k for k, v in cached.items() if bool(v)]
			else:
				cached = list(cached.keys())
		if not isinstance(cached, list):
			return []
		normalized = []
		for item in cached:
			if isinstance(item, str):
				normalized.append(item.lower())
			elif isinstance(item, dict):
				item_hash = item.get('hash') or item.get('info_hash') or item.get('btih')
				if isinstance(item_hash, str):
					normalized.append(item_hash.lower())
		return normalized

	def user_cloud(self):
		url = 'torrents/mylist'
		string = 'fen_tb_user_cloud'
		return cache_object(self._get, string, url, False, 0.5)

	def list_transfer(self, transfer_id):
		response = self._get('torrents/mylist', params={'id': transfer_id, 'limit': 1})
		data = self._parse_data(response)
		if isinstance(data, list) and data:
			return data[0]
		if isinstance(data, dict):
			if 'torrents' in data and data['torrents']:
				return data['torrents'][0]
			return data
		return {}

	def _request_download(self, torrent_id, file_id=0):
		params = {'token': self.token, 'torrent_id': int(torrent_id), 'file_id': int(file_id or 0), 'redirect': False}
		response = self._get('torrents/requestdl', params=params, auth=False)
		data = self._parse_data(response)
		if isinstance(data, dict):
			return data.get('link') or data.get('url') or data.get('download_url')
		if isinstance(response, dict):
			return response.get('link') or response.get('url') or response.get('download_url')
		return None

	def unrestrict_link(self, link):
		if isinstance(link, str) and link.startswith('http'):
			return link
		try:
			parts = str(link).split(':')
			if len(parts) == 2:
				torrent_id, file_id = parts
				return self._request_download(torrent_id, file_id)
		except:
			pass
		return None

	def create_transfer(self, magnet):
		response = self._post('torrents/createtorrent', data={'magnet': magnet, 'seed': 1, 'allow_zip': True})
		data = self._parse_data(response)
		if isinstance(data, dict):
			for key in ('torrent_id', 'id'):
				if key in data:
					return data[key]
		if isinstance(data, list) and data:
			item = data[0]
			if isinstance(item, dict):
				return item.get('torrent_id') or item.get('id')
		return ''

	def delete_transfer(self, transfer_id):
		response = self._post('torrents/controltorrent', data={'operation': 'delete', 'torrent_id': int(transfer_id)})
		if isinstance(response, dict):
			return response.get('success', False)
		return False

	def _file_list(self, transfer_info):
		files = transfer_info.get('files') or transfer_info.get('file_list') or []
		if isinstance(files, dict):
			files = files.get('files', [])
		if not isinstance(files, list):
			files = []
		return files

	def resolve_magnet(self, magnet_url, info_hash, store_to_cloud, title, season, episode):
		from modules.source_utils import seas_ep_filter, extras_filter
		try:
			transfer_id = self.create_transfer(magnet_url)
			if not transfer_id:
				return None
			transfer_info = self.list_transfer(transfer_id)
			files = [i for i in self._file_list(transfer_info) if self._video_file(i)]
			if not files:
				if not store_to_cloud:
					self.delete_transfer(transfer_id)
				return None
			chosen = None
			if season:
				episode_title = re.sub(r'[^A-Za-z0-9-]+', '.', title.replace("'", '').replace('&', 'and').replace('%', '.percent')).lower()
				matched = [i for i in files if seas_ep_filter(season, episode, i.get('name', ''))]
				if matched:
					for item in matched:
						compare_link = seas_ep_filter(season, episode, item.get('name', ''), split=True)
						compare_link = re.sub(episode_title, '', compare_link)
						if not any(x in compare_link for x in extras_filter()):
							chosen = item
							break
			else:
				chosen = max(files, key=lambda x: float(x.get('size', 0) or 0))
			if not chosen:
				if not store_to_cloud:
					self.delete_transfer(transfer_id)
				return None
			file_id = chosen.get('id') or chosen.get('file_id') or 0
			file_url = self._request_download(transfer_id, file_id)
			if not store_to_cloud:
				self.delete_transfer(transfer_id)
			return file_url
		except:
			try:
				if transfer_id:
					self.delete_transfer(transfer_id)
			except:
				pass
			return None

	def display_magnet_pack(self, magnet_url, info_hash):
		try:
			transfer_id = self.create_transfer(magnet_url)
			if not transfer_id:
				return None
			transfer_info = self.list_transfer(transfer_id)
			end_results = []
			append = end_results.append
			for item in self._file_list(transfer_info):
				if self._video_file(item):
					file_id = item.get('id') or item.get('file_id') or 0
					append({'link': '%s:%s' % (transfer_id, file_id), 'filename': item.get('name', ''), 'size': item.get('size', 0)})
			self.delete_transfer(transfer_id)
			return end_results
		except:
			try:
				if transfer_id:
					self.delete_transfer(transfer_id)
			except:
				pass
			return None

	def add_uncached_torrent(self, magnet_url, pack=False):
		from modules.kodi_utils import show_busy_dialog, hide_busy_dialog
		def _return_failed(message=32574, cancelled=False):
			try:
				kodi_utils.progressDialog.close()
			except Exception:
				pass
			hide_busy_dialog()
			kodi_utils.sleep(500)
			if cancelled:
				if kodi_utils.confirm_dialog(text=32044, top_space=True):
					kodi_utils.ok_dialog(heading=32733, text=kodi_utils.local_string(32732) % 'TorBox', top_space=True)
				else:
					self.delete_transfer(transfer_id)
			else:
				kodi_utils.ok_dialog(heading=32733, text=message)
			return False
		show_busy_dialog()
		transfer_id = self.create_transfer(magnet_url)
		if not transfer_id:
			return _return_failed()
		transfer_info = self.list_transfer(transfer_id)
		if not transfer_info:
			return _return_failed()
		if pack:
			self.clear_cache()
			hide_busy_dialog()
			kodi_utils.ok_dialog(text=kodi_utils.local_string(32732) % 'TorBox')
			return True
		interval = 5
		line = '%s[CR]%s[CR]%s'
		line1 = '%s...' % (kodi_utils.local_string(32732) % 'TorBox')
		line2 = transfer_info.get('name', 'TorBox')
		line3 = transfer_info.get('download_state') or transfer_info.get('state') or ''
		kodi_utils.progressDialog.create(kodi_utils.local_string(32733), line % (line1, line2, line3))
		while str(transfer_info.get('download_finished', False)).lower() != 'true':
			kodi_utils.sleep(1000 * interval)
			transfer_info = self.list_transfer(transfer_id)
			line2 = transfer_info.get('name', line2)
			line3 = transfer_info.get('download_state') or transfer_info.get('state') or line3
			progress = int(float(transfer_info.get('download_progress', 0) or 0))
			kodi_utils.progressDialog.update(progress, line % (line1, line2, line3))
			if kodi_utils.monitor.abortRequested() == True:
				return sysexit()
			try:
				if kodi_utils.progressDialog.iscanceled():
					return _return_failed(32736, cancelled=True)
			except Exception:
				pass
			if transfer_info.get('download_state') in ('error', 'failed'):
				return _return_failed()
		kodi_utils.sleep(1000 * interval)
		try:
			kodi_utils.progressDialog.close()
		except Exception:
			pass
		hide_busy_dialog()
		return True

	def get_hosts(self):
		string = 'fen_tb_valid_hosts'
		url = 'webdl/hosters'
		hosts_dict = {'TorBox': []}
		hosts = []
		try:
			result = cache_object(self._get, string, url, False, 168)
			data = self._parse_data(result)
			if isinstance(data, list):
				for item in data:
					if isinstance(item, dict):
						domains = item.get('domains') or item.get('domain') or []
						if isinstance(domains, str):
							domains = [domains]
						hosts.extend(domains)
			hosts_dict['TorBox'] = list(set(hosts))
		except:
			pass
		return hosts_dict

	def revoke_auth(self):
		set_setting('tb.account_id', '')
		set_setting('tb.token', '')
		set_setting('tb.api_key', '')
		kodi_utils.ok_dialog(heading='TorBox', text='%s %s' % (kodi_utils.local_string(32059), kodi_utils.local_string(32576)))

	def clear_cache(self):
		try:
			if not kodi_utils.path_exists(kodi_utils.maincache_db):
				return True
			from caches.debrid_cache import debrid_cache
			dbcon = kodi_utils.database.connect(kodi_utils.maincache_db)
			dbcur = dbcon.cursor()
			try:
				dbcur.execute("""DELETE FROM maincache WHERE id=?""", ('fen_tb_user_cloud',))
				kodi_utils.clear_property('fen_tb_user_cloud')
				dbcon.commit()
			except:
				pass
			try:
				dbcur.execute("""DELETE FROM maincache WHERE id=?""", ('fen_tb_valid_hosts',))
				kodi_utils.clear_property('fen_tb_valid_hosts')
				dbcon.commit()
			except:
				pass
			try:
				debrid_cache.clear_debrid_results('tb')
			except:
				pass
			try:
				dbcon.close()
			except:
				pass
		except:
			return False
		return True