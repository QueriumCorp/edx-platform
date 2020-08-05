"""
  LTI Grade Sync

  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020
"""
from django.apps import AppConfig


class LTIGradeSyncConfig(AppConfig):
    name = 'common.djangoapps.third_party_auth.lti_consumers'
    verbose_name = "Querium LTI Grade Sync"
