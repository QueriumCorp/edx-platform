from django.apps import AppConfig
from django.conf import settings
import logging
log = logging.getLogger(__name__)


class LTIWilloLabsConfig(AppConfig):
    name = 'common.djangoapps.third_party_auth.lti_consumers.willolabs'
    verbose_name = "LTI Willo Labs"

    def ready(self):
        # To override the settings before loading social_django.
        log.info("LTIWilloLabsConfig - initialized.")