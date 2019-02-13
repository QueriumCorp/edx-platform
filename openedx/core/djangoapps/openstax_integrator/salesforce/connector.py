u"""
  used a reference module provided by the team at openstax for this.
  https://raw.githubusercontent.com/openstax/openstax-cms/master/salesforce/salesforce.py
"""
from __future__ import absolute_import
from pprint import PrettyPrinter
from django.core import serializers

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore

from simple_salesforce import Salesforce

from .models import Configuration


class Connection(Salesforce):
    _default_session_key = 0

    def __init__(self, *args, **kwargs):
        try:
            #FIX NOTE: not the greatest way to determine our running enviroment.
            if settings.DEBUG:
                sf_config = Configuration.objects.get(type=u'dev')
            else:
                sf_config = Configuration.objects.get(type=u'prod')

        except Configuration.DoesNotExist:
            raise ValueError(u'No Django configuration found for Openstax salesforce api.')

        session_store = SessionStore(session_key=self._default_session_key)
        if u'sf_instance' in session_store.keys() and u'sf_session_id' in session_store.keys():
            try:
                super(Connection, self).__init__(instance=session_store[u'sf_instance'],
                                                 session_id=session_store[u'sf_session_id'])
            except:
                raise RuntimeError(u"salesforce api session failed.")
        else:
            try:
                super(Connection, self).__init__(username=sf_config.username,
                                                 password=sf_config.password,
                                                 security_token=sf_config.security_token,
                                                 sandbox=sf_config.sandbox)
            except AttributeError:
                super(Connection, self).__init__(*args, **kwargs)
            except TypeError:
                raise RuntimeError(u"salesforce init failed")
            session_store[u'sf_instance'] = self.sf_instance
            session_store[u'sf_session_id'] = self.session_id
            session_store.save()
            self.update_session_key(session_store.session_key)

    @classmethod
    def update_session_key(cls, key):
        cls._default_session_key = key

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if not exc == (None, None, None):
            session_store = SessionStore(session_key=self._default_session_key)
            session_store.delete()
            self.update_session_key(None)
        return False
