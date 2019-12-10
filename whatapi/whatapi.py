try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser # py3k support
import requests
import time

headers = {
    'Content-type': 'application/x-www-form-urlencoded',
    'Accept-Charset': 'utf-8',
    'User-Agent': 'whatapi [isaaczafuta]'
    }

class LoginException(Exception):
    pass


class RequestException(Exception):
    pass


class WhatAPI:
    def __init__(self, config_file=None, username=None, password=None, cookies=None,
                 server="https://ssl.what.cd"):
        self.session = requests.Session()
        self.session.headers = headers
        self.authkey = None
        self.passkey = None
        self.server = server
        if config_file:
            config = ConfigParser()
            config.read(config_file)
            self.username = config.get('login', 'username')
            self.password = config.get('login', 'password')
        else:
            self.username = username
            self.password = password
        if cookies:
            self.session.cookies = cookies
            try:
                self._auth()
            except RequestException:
                self._login()
        else:
            self._login()

    def _auth(self):
        '''Gets auth key from server'''
        accountinfo = self.request("index")
        self.authkey = accountinfo["response"]["authkey"]
        self.passkey = accountinfo["response"]["passkey"]

    def _login(self):
        '''Logs in user'''
        loginpage = self.server + '/login.php'
        data = {'username': self.username,
                'password': self.password,
                'keeplogged': 1,
                'login': 'Login'
        }
        r = self.session.post(loginpage, data=data, allow_redirects=False)
        if r.status_code != 302:
            raise LoginException
        self._auth()

    def get_torrent(self, torrent_id, full_response=False):
        '''Downloads and returns the torrent file at torrent_id
        
        full_response: Returns the full response object (including headers) instead of a torrent file
        '''
        torrentpage = self.server + '/torrents.php'
        params = {'action': 'download', 'id': torrent_id}
        if self.authkey:
            params['authkey'] = self.authkey
            params['torrent_pass'] = self.passkey
        r = self.session.get(torrentpage, params=params, allow_redirects=False)
        time.sleep(2)
        if r.status_code == 200 and 'application/x-bittorrent' in r.headers['content-type']:
            return r if full_response else r.content
        return None

    def logout(self):
        '''Logs out user'''
        logoutpage = self.server + '/logout.php'
        params = {'auth': self.authkey}
        self.session.get(logoutpage, params=params, allow_redirects=False)

    def request(self, action, **kwargs):
        '''Makes an AJAX request at a given action page'''
        ajaxpage = self.server + '/ajax.php'
        params = {'action': action}
        if self.authkey:
            params['auth'] = self.authkey
        params.update(kwargs)

        r = self.session.get(ajaxpage, params=params, allow_redirects=False)
        time.sleep(2)
        try:
            json_response = r.json()
            if json_response["status"] != "success":
                raise RequestException
            return json_response
        except ValueError:
            raise RequestException
