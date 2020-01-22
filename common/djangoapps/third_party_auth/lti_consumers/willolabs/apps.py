"""
  Willo Labs Grade Sync.

  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020
"""
from django.apps import AppConfig
import logging
log = logging.getLogger(__name__)


class LTIWilloLabsConfig(AppConfig):
    name = 'common.djangoapps.third_party_auth.lti_consumers.willolabs'
    verbose_name = "LTI Willo Labs Grade Sync"

    def ready(self):
        #log.info("LTIWilloLabsConfig - initialized.")
        return None