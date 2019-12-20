from django.apps import AppConfig
import logging
log = logging.getLogger(__name__)


class LTIWilloLabsConfig(AppConfig):
    name = 'common.djangoapps.third_party_auth.lti_consumers.willolabs'
    verbose_name = "LTI Willo Labs"

    def ready(self):
        #log.info("LTIWilloLabsConfig - initialized.")
        return None