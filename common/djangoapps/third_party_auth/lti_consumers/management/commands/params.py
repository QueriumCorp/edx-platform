"""
  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020

  LTI Grade Sync.
  Command line tools for creating and maintaining LTI Configurations

  Usage:
    sudo -H -u edxapp bash
    cd ~
    source edxapp_env
    source venvs/edxapp/bin/activate
    cd edx-platform
    python manage.py lms params initialize "Canvas via Willo for ABC University"
"""
from django.core.management.base import BaseCommand
from common.djangoapps.third_party_auth.lti_consumers.constants import (
    LTI_CACHE_TABLES,
    LTI_PARAMS_DEFAULT_CONFIGURATION
    )
from common.djangoapps.third_party_auth.lti_consumers.models import (
    LTIConfigurations,
    LTIConfigurationParams
    )
from common.djangoapps.third_party_auth.lti_consumers.utils import initialize_lti_configuration

VALID_COMMANDS = ['initialize']

class Command(BaseCommand):
    help = u"LTI Grade Sync. Utilities for creating and maintaining LTI Configurations."

    def add_arguments(self, parser):
      parser.add_argument(
            'command',
            type=str,
            help='LTI Grade Sync commands: initialize'
            )

      parser.add_argument(
            'name',
            type=str,
            help='LTI Grade Sync Configuration name'
            )

    def handle(self, *args, **kwargs):
        cmd = kwargs['command'].lower()
        name = kwargs['name']

        print('Received these parameters. command: {command}, name: {name}'.format(
            command=cmd,
            name=name
        ))

        if cmd not in VALID_COMMANDS:
            print('Valid commands include: {commands}'.format(
                commands=json.dumps(VALID_COMMANDS)
            ))
            return

        if cmd == 'initialize':
            initialize_lti_configuration(name)
            return
