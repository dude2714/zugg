# -*- coding: utf-8 -*-
from threading import Thread
from apis.torbox_api import TorBoxAPI
from modules import source_utils
from modules.utils import clean_file_name, normalize
from modules.settings import enabled_debrids_check, filter_by_name

TorBox = TorBoxAPI()
extensions = source_utils.supported_video_extensions()
internal_results = source_utils.internal_results
check_title, clean_title = source_utils.check_title, source_utils.clean_title
get_file_info, release_info_format, seas_ep_filter = source_utils.get_file_info, source_utils.release_info_format, source_utils.seas_ep_filter


class source:
	def __init__(self):
		self.scrape_provider = 'tb_cloud'
		self.sources = []

	def results(self, info):
		try:
			if not enabled_debrids_check('tb'):
				return internal_results(self.scrape_provider, self.sources)
			self.folder_results, self.scrape_results = [], []
			title_filter = filter_by_name(self.scrape_provider)
			self.media_type, title = info.get('media_type'), info.get('title')
			self.year, self.season, self.episode = int(info.get('year')), info.get('season'), info.get('episode')
			if self.media_type == 'episode':
				self.seas_ep_query_list = source_utils.seas_ep_query_list(self.season, self.episode)
			self.folder_query = clean_title(normalize(title))
			self._scrape_cloud()
			if not self.scrape_results:
				return internal_results(self.scrape_provider, self.sources)
			self.aliases = source_utils.get_aliases_titles(info.get('aliases', []))

			def _process():
				for item in self.scrape_results:
					try:
						file_name = normalize(item['filename'])
						if title_filter and not check_title(title, file_name, self.aliases, self.year, self.season, self.episode):
							continue
						file_dl = item['link']
						size = round(float(int(item.get('size', 0))) / 1073741824, 2)
						url_name = clean_file_name(file_name).replace('html', ' ').replace('+', ' ').replace('-', ' ')
						video_quality, details = get_file_info(name_info=release_info_format(file_name))
						source_item = {
							'name': file_name,
							'title': file_name,
							'URLName': url_name,
							'quality': video_quality,
							'size': size,
							'size_label': '%.2f GB' % size,
							'extraInfo': details,
							'url_dl': file_dl,
							'id': file_dl,
							'downloads': False,
							'direct': True,
							'source': self.scrape_provider,
							'scrape_provider': self.scrape_provider
						}
						yield source_item
					except Exception:
						pass

			self.sources = list(_process())
		except Exception as e:
			from modules.kodi_utils import logger
			logger('FEN torbox scraper Exception', e)
		internal_results(self.scrape_provider, self.sources)
		return self.sources

	def _scrape_cloud(self):
		try:
			threads = []
			append = threads.append
			my_cloud_files = TorBox.user_cloud(completed=True)
			for item in my_cloud_files:
				normalized = normalize(item.get('name', ''))
				folder_name = clean_title(normalized)
				if self.folder_query in folder_name or not folder_name:
					self.folder_results.append(item)
			if not self.folder_results:
				return self.sources
			for item in self.folder_results:
				append(Thread(target=self._scrape_folder, args=(item,)))
			[i.start() for i in threads]
			[i.join() for i in threads]
		except Exception:
			pass

	def _scrape_folder(self, folder_item):
		try:
			torrent_id = folder_item.get('id')
			for entry in folder_item.get('files', []):
				filename = entry.get('short_name', '')
				if not filename.lower().endswith(tuple(extensions)):
					continue
				normalized = normalize(filename)
				cleaned = clean_title(normalized)
				match = False
				if self.media_type == 'movie':
					if any(x in cleaned for x in self._year_query_list()) and self.folder_query in cleaned:
						match = True
				elif seas_ep_filter(self.season, self.episode, normalized):
					match = True
				if not match:
					continue
				entry = dict(entry)
				entry.update({
					'filename': filename,
					'link': '%s,%s' % (torrent_id, entry.get('id'))
				})
				self.scrape_results.append(entry)
		except Exception:
			return

	def _year_query_list(self):
		return (str(self.year), str(self.year + 1), str(self.year - 1))