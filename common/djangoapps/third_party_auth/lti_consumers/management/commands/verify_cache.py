"""
  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Sep-2020

  LTI Grade Sync
  Rebuild the LTI Grade Sync cache data from lms grade factory.

  Run from the command line like this:
    sudo -H -u edxapp bash
    cd ~
    source edxapp_env
    source venvs/edxapp/bin/activate
    cd edx-platform
    python manage.py lms verify_cache -c course-v1:KU+OS9471721_2955+Fall2020_Master_Shell_Weiland

"""
# django stuff
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

# open edx stuff
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

# rover stuff
from common.djangoapps.third_party_auth.lti_consumers.cache import LTICacheManager
from ...utils import get_lti_courses

User = get_user_model()

class Command(BaseCommand):
    help = u"LTI Grade Sync. Verify LTI cache records for all courses/enrollments/assignments/grades."

    def add_arguments(self, parser):
        parser.add_argument(
            u'-c',
            u'--course_id',
            type=str,
            help=u'A string representation of a CourseKey. Example: course-v1:ABC+OS9471721_9626+01'
            )
        parser.add_argument(
            u'-u',
            u'--username',
            type=str,
            help=u'A Rover username'
            )
        parser.add_argument(
            u'-q',
            u'--quiet',
            action='store_true',
            help=u'True if you want to suppress console output'
            )


    def handle(self, *args, **kwargs):

        course_id = kwargs['course_id']
        username = kwargs['username']
        quiet = kwargs['quiet']

        course = None
        user = None
        lti_internal_courses = None

        course_key = CourseKey.from_string(course_id)
        if course_id: course = CourseOverview.objects.filter(id=course_key)
        if username: user = User.objects.get(username=username)

        print(course_key)
        print(course)
        lti_internal_courses = get_lti_courses(course)
        if lti_internal_courses is None:
            print('No LTIInternalCourses found. Exiting.')
            return None

        for lti_internal_course in lti_internal_courses:
            course_id = str(lti_internal_course.course_fk.id)
            lti_cache = LTICacheManager(course_id=course_id, user=user)
            try:
                lti_cache.verify(quiet)
            except:
                pass

