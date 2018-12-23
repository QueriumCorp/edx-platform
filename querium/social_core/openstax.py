"""
Written by:     McDaniel
Date:           December 11, 2018

Usage: OpenStax OAuth2 backend, docs at:
    https://python-social-auth-docs.readthedocs.io/en/latest/configuration/django.html

Example implementation at:
    (this module was cloned from source at this URL)
    https://github.com/openstax/openstax-cms/blob/master/accounts/backend.py

OpenStax Identity Server setup at:
    https://github.com/openstax/openstax-cms/blob/master/openstax/settings/dev.py#L29-L36
"""
import json
from urllib.parse import urlencode
from urllib.request import urlopen
#from django.conf import settings
from social.backends.oauth import BaseOAuth2


class OpenStaxOAuth2(BaseOAuth2):

    """openstax OAuth authentication backend"""
    name = 'openstax-oauth2'
    ID_KEY = 'c64b279699b23925419a639d8df495a84a5465eff1935c0f4542d5be38581ae4'
    AUTHORIZATION_URL = 'https://accounts-dev.openstax.org/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://accounts-dev.openstax.org/oauth/token'
    USER_QUERY = 'https://accounts-dev.openstax.org/api/user?'
    REQUEST_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('id', 'id'),
    ]

    def get_user_details(self, response):
        """Return user details from openstax account's"""
        contact_infos = response.get('contact_infos')
        try:
            email = contact_infos[0]['value']
        except IndexError:
            email = "none@openstax.org"
        return {'username': str(response.get('id')),
                'email': email,
                'first_name': response.get('first_name'),
                'last_name': response.get('last_name'),
                'full_name': response.get('full_name'), }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = self.USER_QUERY + urlencode({
            'access_token': access_token
        })
        try:
            return json.loads(self.urlopen(url))
        except ValueError:
            return None

    def urlopen(self, url):
        with urlopen(url) as f:
            response = f.read()
        return response.decode("utf-8")
