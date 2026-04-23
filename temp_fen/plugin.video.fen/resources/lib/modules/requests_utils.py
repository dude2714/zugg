# -*- coding: utf-8 -*-
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# from modules.kodi_utils import logger

def make_session(url='https://'):
	session = requests.Session()
	retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504], allowed_methods=['GET', 'POST'])
	adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=retry)
	session.mount(url, adapter)
	return session

def make_requests():
	return requests

