# -*- coding: utf-8 -*-
import time
from modules.settings_reader import get_setting, set_setting
from modules.kodi_utils import translate_path, notification, sleep, ok_dialog, progressDialog, show_text
from modules.requests_utils import make_session
from modules.utils import jsondate_to_datetime

trakt_icon = translate_path('special://home/addons/plugin.video.fenjr/resources/media/trakt.png')
_session = make_session('https://api.trakt.tv')

class Trakt():
	def __init__(self):
		self.api_endpoint = 'https://api.trakt.tv/%s'
		self.client_id = get_setting('trakt.client_id') or '5dd9e3603df7cb000a249219447e7bf1581cbf9577f25fbc2b73ebd2a8cc22a8'
		self.client_secret = get_setting('trakt.client_secret') or '6bd3cc8d726b0b8090628d559ffe87b4ffbdcbd636ad24dd788003ced3a8298a'
		try: self.expires_at = float(get_setting('trakt.expires'))
		except: self.expires_at = 0.0
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
					if data is not None: resp = _session.post(self.api_endpoint % path, json=data, headers=headers, timeout=timeout)
					else: resp = _session.get(self.api_endpoint % path, headers=headers, timeout=timeout)
				except Exception as e:
					error_notification('Trakt Error', str(e))
				return resp
			timeout = 15.0
			headers = {'Content-Type': 'application/json', 'trakt-api-version': '2', 'trakt-api-key': self.client_id}
			response = send_query()
			if response is None: return None
			response.encoding = 'utf-8'
			if return_str: return response
			try: result = response.json()
			except: result = None
			if response.status_code in (303, 403):
				if isinstance(result, dict):
					result['status_code'] = response.status_code
					return result
				return {'error': 'request_rejected', 'status_code': response.status_code}
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
					response = self.call("oauth/device/token", data=data, with_auth=False, suppress_error_notification=True)
					if response and isinstance(response, dict) and 'access_token' in response:
						return response
					if response and isinstance(response, dict):
						status_code = response.get('status_code', 400)
						if status_code in (303, 403):
							notification('Trakt authorization blocked (%s). Re-authorize and try again.' % status_code, icon=trakt_icon)
							return None
					progress = int(100 * time_passed / expires_in)
					progressDialog.update(progress)
					sleep(max(device_codes['interval'], 1)*1000)
					time_passed = time.time() - start
			finally:
				progressDialog.close()
			return None
		except:
			self.error()

	def refresh_token(self):
		data = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
			"grant_type": "refresh_token",
			"refresh_token": get_setting('trakt.refresh')
		}

		response = self.call("oauth/token", data=data, with_auth=False, return_str=True)
		if not response:
			notification('Temporary Trakt Server Problems', icon=trakt_icon)
			return False
		code = str(response.status_code)

		if code.startswith('5'): # covers temporary server responses
#			log_utils.log('Temporary Trakt Server Problems', level=control.LOGNOTICE)
			notification('Temporary Trakt Server Problems', icon=trakt_icon)
			return False
		elif code in ['423']:
#			log_utils.log('Locked User Account - Contact Trakt Support: %s' % str(response[0]), level=control.LOGWARNING)
			notification('Locked User Account', icon=trakt_icon)
			return False
		elif code in ['303', '403']:
			notification('Trakt token request rejected (%s). Please re-authorize.' % code, icon=trakt_icon)
			return False

		if code not in ['401', '405']:
			try:
				response = response.json()
			except:
				self.error()
				return False
			if 'error' in response and response['error'] == 'invalid_grant':
#				log_utils.log('Please Re-Authorize your Trakt Account: %s' % response['error'], __name__, level=control.LOGWARNING)
				notification('Please Re-Authorize your Trakt Account', icon=trakt_icon)
				return False

			trakt_token = response.get("access_token")
			trakt_refresh = response.get("refresh_token")
			if not trakt_token or not trakt_refresh: return False
			trakt_expires = time.time() + 7776000
			set_setting('trakt.token', trakt_token)
			set_setting('trakt.refresh', trakt_refresh)
			set_setting('trakt.expires', str(trakt_expires))
			self.token = trakt_token
			self.expires_at = trakt_expires
			return True
		return False

	def auth(self):
		try:
			code = self.get_device_code()
			if not code or not isinstance(code, dict) or 'device_code' not in code:
				status_code = code.get('status_code') if isinstance(code, dict) else None
				if status_code in (303, 403):
					notification('Trakt device code request rejected (%s). Please try again later.' % status_code, icon=trakt_icon)
				else:
					notification('Trakt Error Authorizing', icon=trakt_icon)
				return False
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
				addon = 'plugin.video.fenjr'
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
			xbmc.log('[ plugin.video.fenjr ] log_utils.error() Logging Failure: %s' % (e), LOGERROR)

