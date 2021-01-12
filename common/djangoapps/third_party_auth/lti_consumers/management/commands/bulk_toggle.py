"""
  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020

  LTI Grade Sync.
  Command line tool to bulk enable/disable course-level LTI Grade Sync

  Usage:
    sudo -H -u edxapp bash
    cd ~
    source edxapp_env
    source venvs/edxapp/bin/activate
    cd edx-platform
    python manage.py lms bulk_toggle enable
"""
from django.core.management.base import BaseCommand

# our stuff
from common.djangoapps.third_party_auth.lti_consumers.models import LTIInternalCourse

VALID_COMMANDS = ['enable', 'disable']

class Command(BaseCommand):
    help = u"LTI Grade Sync. Utilities for creating and maintaining LTI Configurations."

    def add_arguments(self, parser):
      parser.add_argument(
            'command',
            type=str,
            help='valid commands: enable, disable'
            )


    def handle(self, *args, **kwargs):
        cmd = kwargs['command'].lower()

        if cmd not in VALID_COMMANDS:
            print('Valid commands include: {commands}'.format(
                commands=json.dumps(VALID_COMMANDS)
            ))
            return

        enabled = cmd == 'enable'

        lti_internal_courses = LTIInternalCourse.objects.all()
        for course in lti_internal_courses:
            print('{cmd} {course_key}'.format(
                cmd=cmd,
                course_key=str(course.course)
            ))
            course.enabled = enabled
            course.save()
