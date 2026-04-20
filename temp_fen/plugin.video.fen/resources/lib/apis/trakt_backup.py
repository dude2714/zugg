# -*- coding: utf-8 -*-
import requests
import time
from modules.settings_reader import get_setting, set_setting
from modules.kodi_utils import translate_path, notification, sleep, ok_dialog, progressDialog, show_text
from modules.utils import jsondate_to_datetime

trakt_icon = translate_path('special://home/addons/plugin.video.fen/resources/media/trakt.png')

class Trakt():
	def __init__(self):
		self.api_endpoint = 'https://api-v2launch.trakt.tv/%s'
		self.client_id = get_setting('trakt.client_id') # 'd4161a7a106424551add171e5470112e4afdaf2438e6ef2fe0548edc75924868'
		self.client_secret = get_setting('trakt.client_secret') # 'b5fcd7cb5d9bb963784d11bbf8535bc0d25d46225016191eb48e50792d2155c0'
		self.expires_at = get_setting('trakt.expires')
		self.token = get_setting('trakt.token')

	def call(self, path, data=None, with_auth=True, method=None, return_str=False, suppress_error_notification=False):
		try:
			def error_notification(line1, error):
				if suppress_error_notification: return
				return notification('%s: %s' % (line1, error), icon=trakt_icon)
			def send_query():
				resp = None
				if with_auth:
					try:
						if time.time() > self.expires_at: self.refresh_token()
					except: pass
					headers['Authorization'] = 'Bearer ' + self.token
				try:
					if data is not None: resp = requests.post(self.api_endpoint % path, json=data, headers=headers, timeout=timeout)
					else: resp = requests.get(self.api_endpoint % path, headers=headers, timeout=timeout)
				except requests.exceptions.RequestException as e:
					error_notification('Trakt Error', str(e))
				except Exception as e:
					error_notification('', str(e))
				return resp
			timeout = 15.0
			headers = {'Content-Type': 'application/json', 'trakt-api-version': '2', 'trakt-api-key': self.client_id}
			response = send_query()
			response.encoding = 'utf-8'
			if return_str: return response
			try: result = response.json()
			except: result = None
			return result
		except:
			self.error()

	def get_device_code(self):
		data = {'client_id': self.client_id}
		return self.call("oauth/device/code", data=data, with_auth=False)

	def get_device_token(self, device_codes):
		try:
			data = {"code": device_codes["device_code"],
					"client_id": self.client_id,
					"client_secret": self.client_secret}
			start = time.time()
			expires_in = device_codes['expires_in']
			verification_url = ('1) Open this link in a browser : [COLOR skyblue]%s[/COLOR]' % str(device_codes['verification_url']))
			user_code = ('2) When prompted enter : [COLOR skyblue]%s[/COLOR]' % str(device_codes['user_code']))
			progress_line = '%s[CR]%s[CR]%s'
			progressDialog.create('[B]TRAKT[/B] : Authorize', progress_line % (verification_url, user_code, ''))
			try:
				time_passed = 0
				while not progressDialog.iscanceled() and time_passed < expires_in:
					try:
						response = self.call("oauth/device/token", data=data, with_auth=False, suppress_error_notification=True)
					except requests.HTTPError as e:
#						log_utils.log('Request Error: %s' % str(e), __name__, control.LOGDEBUG)
						if e.response.status_code != 400: raise e
						progress = int(100 * time_passed / expires_in)
						progressDialog.update(progress)
						sleep(max(device_codes['interval'], 1)*1000)
					else:
						if not response: continue
						else: return response
					time_passed = time.time() - start
			finally:
				progressDialog.close()
			return None
		except:
			self.error()

	def refresh_token(self):
		traktToken = None
		traktRefresh = None
		traktExpires = None
		data = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
			"grant_type": "refresh_token",
			"refresh_token": get_setting('trakt.refresh')
		}

		response = self.call("oauth/token", data=data, with_auth=False, return_str=True)
		try: code = str(response[1])
		except: code = ''

		if code.startswith('5') or (response and isinstance(response, str) and '<html' in response) or not response: # covers Maintenance html responses ["Bad Gateway", "We're sorry, but something went wrong (500)"])
#			log_utils.log('Temporary Trakt Server Problems', level=control.LOGNOTICE)
			notification('Temporary Trakt Server Problems', icon=trakt_icon)
			return False
		elif response and code in ['423']:
#			log_utils.log('Locked User Account - Contact Trakt Support: %s' % str(response[0]), level=control.LOGWARNING)
			notification('Locked User Account', icon=trakt_icon)
			return False

		if response and code not in ['401', '405']:
			try:
				response = response.json()
			except:
				self.error()
				return False
			if 'error' in response and response['error'] == 'invalid_grant':
#				log_utils.log('Please Re-Authorize your Trakt Account: %s' % response['error'], __name__, level=control.LOGWARNING)
				notification('Please Re-Authorize your Trakt Account', icon=trakt_icon)
				return False

			traktToken = response["access_token"]
			traktRefresh = response["refresh_token"]
			traktExpires = time.time() + 7776000
			set_setting('trakt.token', traktToken)
			set_setting('trakt.refresh', traktRefresh)
			set_setting('trakt.expires', str(traktExpires))
		self.token = traktToken

	def auth(self):
		try:
			code = self.get_device_code()
			token = self.get_device_token(code)
			if token:
				expires_at = time.time() + 7776000
				set_setting('trakt.expires', str(expires_at))
				set_setting('trakt.token', token["access_token"])
				set_setting('trakt.refresh', token["refresh_token"])
				self.expires_at = expires_at
				self.token = token["access_token"]
				sleep(1000)
				try:
					user = self.call("users/me", with_auth=True)
#					control.setSetting('trakt.username', str(user['username']))
					set_setting('trakt_user', str(user['username']))
				except: pass
				notification('Trakt Successfully Authorized', icon=trakt_icon)
				return True
			notification('Trakt Error Authorizing', icon=trakt_icon)
			return False
		except:
			self.error()

	def revoke(self):
		data = {"token": get_setting('trakt.token')}
		try: self.call("oauth/revoke", data=data, with_auth=False)
		except: pass
#		control.setSetting('trakt.username', '')
		set_setting('trakt_user', '')
		set_setting('trakt.expires', '')
		set_setting('trakt.token', '')
		set_setting('trakt.refresh', '')
		ok_dialog(heading='Trakt', text='Auth Revoked')

	def account_info(self):
		response = self.call("users/me", with_auth=True)
		return response

	def extended_account_info(self):
		account_info = self.call("users/settings", with_auth=True)
		stats = self.call("users/%s/stats" % account_info['user']['ids']['slug'], with_auth=True)
		return account_info, stats

	def account_info_to_dialog(self):
		from datetime import datetime, timedelta
		try:
			account_info, stats = self.extended_account_info()
			username = account_info['user']['username']
			timezone = account_info['account']['timezone']
			joined = jsondate_to_datetime(account_info['user']['joined_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
			private = account_info['user']['private']
			vip = account_info['user']['vip']
			if vip: vip = '%s Years' % str(account_info['user']['vip_years'])
			total_given_ratings = stats['ratings']['total']
			movies_collected = stats['movies']['collected']
			movies_watched = stats['movies']['watched']
			movie_minutes = stats['movies']['minutes']
			if movie_minutes == 0: movies_watched_minutes = ['0 days', '0:00:00']
			elif movie_minutes < 1440: movies_watched_minutes = ['0 days', "{:0>8}".format(str(timedelta(minutes=movie_minutes)))]
			else: movies_watched_minutes = ("{:0>8}".format(str(timedelta(minutes=movie_minutes)))).split(', ')
			movies_watched_minutes = ('%s %s hours %s minutes' % (movies_watched_minutes[0], movies_watched_minutes[1].split(':')[0], movies_watched_minutes[1].split(':')[1]))
			shows_collected = stats['shows']['collected']
			shows_watched = stats['shows']['watched']
			episodes_watched = stats['episodes']['watched']
			episode_minutes = stats['episodes']['minutes']
			if episode_minutes == 0: episodes_watched_minutes = ['0 days', '0:00:00']
			elif episode_minutes < 1440: episodes_watched_minutes = ['0 days', "{:0>8}".format(str(timedelta(minutes=episode_minutes)))]
			else: episodes_watched_minutes = ("{:0>8}".format(str(timedelta(minutes=episode_minutes)))).split(', ')
			episodes_watched_minutes = ('%s %s hours %s minutes' % (episodes_watched_minutes[0], episodes_watched_minutes[1].split(':')[0], episodes_watched_minutes[1].split(':')[1]))
			heading = 'Trakt'
			items = []
			items += ['[B]Username:[/B] %s' % username]
			items += ['[B]Timezone:[/B] %s' % timezone]
			items += ['[B]Joined:[/B] %s' % joined]
			items += ['[B]Private:[/B] %s' % private]
			items += ['[B]VIP Status:[/B] %s' % vip]
			items += ['[B]Ratings Given:[/B] %s' % str(total_given_ratings)]
			items += ['[B]Movies:[/B] [B]%s[/B] Collected, [B]%s[/B] Watched for [B]%s[/B]' % (movies_collected, movies_watched, movies_watched_minutes)]
			items += ['[B]Shows:[/B] [B]%s[/B] Collected, [B]%s[/B] Watched' % (shows_collected, shows_watched)]
			items += ['[B]Episodes:[/B] [B]%s[/B] Watched for [B]%s[/B]' % (episodes_watched, episodes_watched_minutes)]
			return show_text(heading.upper(), '\n\n'.join(items), font_size='large')
		except:
			self.error()
			return

	def error(self, message=None, exception=True):
		LOGERROR = 3
		try:
			import sys
			if exception:
				type, value, traceback = sys.exc_info()
				addon = 'plugin.video.fen'
				filename = (traceback.tb_frame.f_code.co_filename)
				filename = filename.split(addon)[1]
				name = traceback.tb_frame.f_code.co_name
				linenumber = traceback.tb_lineno
				errortype = type.__name__
				errormessage = value or value.message
				if str(errormessage) == '': return
				if message: message += ' -> '
				else: message = ''
				message += str(errortype) + ' -> ' + str(errormessage)
				caller = [filename, name, linenumber]
			else:
				caller = None
			del(type, value, traceback) # So we don't leave our local labels/objects dangling
	#		log(msg=message, caller=caller, level=LOGERROR)
		except Exception as e:
			import xbmc
			xbmc.log('[ plugin.video.fen ] log_utils.error() Logging Failure: %s' % (e), LOGERROR)

