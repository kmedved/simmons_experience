
# coding: utf-8

# In[1]:


import requests, bs4
import pandas as pd
from itertools import chain
import requests
from oauth2client.service_account import ServiceAccountCredentials

import json
import time
import webbrowser
from pandas.io.json import json_normalize
from rauth import OAuth1Service
from rauth.utils import parse_utf8_qsl


# In[ ]:


import os
import time

from rauth import OAuth2Service


class ClientKey(object):
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    @classmethod
    def from_file(cls, key_file):
        with open(key_file, "r") as f:
            keys = f.read().splitlines()

        if len(keys) != 2:
            raise RuntimeError("Incorrect number of keys found")

        return cls(*keys)


class Token(object):
    def __init__(self, access_token=None, refresh_token=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiration_time = 0

    @property
    def expires_in(self):
        return self.expiration_time - time.time()

    @property
    def is_expired(self):
        return self.expires_in <= 0

    def get(self, oauth_service):
        if self.refresh_token:
            data = {
                "refresh_token": self.refresh_token,
                "redirect_uri": "oob",
                "grant_type": "refresh_token",
            }
        else:
            data = {
                "code": self._get_code(oauth_service),
                "redirect_uri": "oob",
                "grant_type": "authorization_code",
            }

        self._get_token(oauth_service, data)

    def _get_code(self, oauth_service):
        params = {
            "redirect_uri": "oob",
            "response_type": "code",
        }
        authorize_url = oauth_service.get_authorize_url(**params)

        print ("Sign in here: " + str(authorize_url))
        return input("Enter code: ")

    def _get_token(self, oauth_service, data):
        raw_token = oauth_service.get_raw_access_token(data=data)

        parsed_token = raw_token.json()
        self.access_token = parsed_token["access_token"]
        self.refresh_token = parsed_token["refresh_token"]
        self.expiration_time = time.time() + parsed_token["expires_in"]

    @classmethod
    def from_file(cls, token_file):
        with open(token_file, "r") as f:
            token = f.read().strip()

        if len(token.splitlines()) != 1:
            raise RuntimeError("Incorrect token format")

        return cls(refresh_token=token)

    def save(self, token_file):
        with open(token_file, "w") as f:
            f.write(self.refresh_token)


class YahooAPI(object):
    def __init__(self, keyfile, tokenfile=None,
                 base_url="https://fantasysports.yahooapis.com",
                 request_period=0):

        self.key = ClientKey.from_file(keyfile)

        self.tokenfile = tokenfile
        if self.tokenfile and os.path.exists(self.tokenfile):
            self.token = Token.from_file(self.tokenfile)
        else:
            self.token = Token()

        self.oauth = OAuth2Service(
            client_id=self.key.client_id,
            client_secret=self.key.client_secret,
            name="yahoo",
            authorize_url="https://api.login.yahoo.com/oauth2/request_auth",
            access_token_url="https://api.login.yahoo.com/oauth2/get_token",
            base_url=base_url,
        )

        self.session = None

        self._update_token()

        self.session = self.oauth.get_session(self.token.access_token)

        self.last_request = time.time()
        self.request_period = request_period

    def _update_token(self):
        self.token.get(self.oauth)

        if self.tokenfile:
            self.token.save(self.tokenfile)

        if self.session:
            self.session.access_token = self.token.access_token

    def request(self, request_str, params={}):
        """get json instead of xml like this params={'format': 'json'}"""

        tdiff = max(0, time.time() - self.last_request)
        if tdiff >= 0 and tdiff < self.request_period:
            time.sleep(self.request_period - tdiff)

        self.last_request = time.time()

        # refresh access token 60 seconds before it expires
        if self.token.expires_in < 60:
            self._update_token()

        return self.session.get(url=request_str, params=params)


# In[2]:


app_id="7UtKtr5g"
consumer_key="dj0yJmk9UjV2YTZQQjZ3YmVNJmQ9WVdrOU4xVjBTM1J5TldjbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD05Ng--"
consumer_secret="f4373a8a691565e9df3fc325cceb6ea3e58ab01f"


# In[3]:


credentials = {}
credentials['consumer_key']=consumer_key
credentials['consumer_secret']=consumer_secret
credentials['app_id']=app_id
#credentials=json.dumps(data)
credentials


# In[4]:


oauth = OAuth1Service(consumer_key = credentials['consumer_key'],
                      consumer_secret = credentials['consumer_secret'],
                      name = "yahoo",
                      request_token_url = "https://api.login.yahoo.com/oauth/v2/get_request_token",
                      access_token_url = "https://api.login.yahoo.com/oauth/v2/get_token",
                      authorize_url = "https://api.login.yahoo.com/oauth/v2/request_auth",
                      base_url = "http://fantasysports.yahooapis.com/")


# In[5]:


request_token, request_token_secret = oauth.get_request_token(params={"oauth_callback": "oob"})


# In[7]:


authorize_url = oauth.get_authorize_url(request_token)
webbrowser.open(authorize_url)
verify = input('Enter code: ')


# In[8]:


raw_access = oauth.get_raw_access_token(request_token,
                                        request_token_secret,
                                        params={"oauth_verifier": verify})

parsed_access_token = parse_utf8_qsl(raw_access.content)
access_token = (parsed_access_token['oauth_token'], parsed_access_token['oauth_token_secret'])

start_time = time.time()
end_time = start_time + 3600

credentials['access_token'] = parsed_access_token['oauth_token']
credentials['access_token_secret'] = parsed_access_token['oauth_token_secret']
tokens = (credentials['access_token'], credentials['access_token_secret'])


# In[ ]:


#request_token, request_token_secret = oauth.get_request_token(params={"oauth_callback": "oob"})


# In[9]:


s = oauth.get_session(tokens)


# In[10]:


#https://basketball.fantasysports.yahoo.com/nba/162585/1
url = 'http://fantasysports.yahooapis.com/fantasy/v2/league/nba.l.162585'
r = s.get(url, params={'format': 'json'})
r.status_code


# In[ ]:


r


# In[ ]:


handler=YahooAPI("keyfile.txt")

