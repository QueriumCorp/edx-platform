u"""
  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020

  LTI Grade Sync
  Rebuild the LTI Grade Sync cache data from lms grade factory.

  https://dev.roverbyopenstax.org/grades_api/v2/courses/course-v1:ABC+OS9471721_9626+01/

  Run from the command line like this:
  cd /edx/app/edxapp/edx-platform
  sudo -u www-data /edx/bin/python.edxapp ./manage.py lms --settings aws cache_rebuild course-v1:ABC+OS9471721_9626+01

"""
# django stuff
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


# open edx stuff
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

# rover stuff
from common.djangoapps.third_party_auth.lti_consumers.models import LTIInternalCourse
from common.djangoapps.third_party_auth.lti_consumers.cache import LTICacheManager

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


    def handle(self, *args, **kwargs):

        course_id = kwargs['course_id']
        username = kwargs['username']

        course = None
        user = None
        lti_internal_courses = None

        if course_id: course = CourseOverview.objects.filter(id=course_id)
        if username: user = User.objects.get(username=username)

        lti_internal_courses = self.get_lti_courses(course, user)
        if lti_internal_courses is None:
            print('No LTIInternalCourses found for course_id/username. Exiting.')
            return None

        for lti_internal_course in lti_internal_courses:
            course_id = str(lti_internal_course.course_fk.id)
            print('course_id: ' + course_id)
            lti_cache = LTICacheManager(course_id=course_id, user=user)
            lti_cache.verify()

    def get_lti_courses(self, course, user):
        """evaluate course / user (both are optional) and query LTIInternalCourse

        Args:
            course: CourseOverview or None
            user Django User object or None

        Returns: list of LTIInternalCourse records
        """

        if (LTIInternalCourse.objects.count() == 0):
            print('LTIInternalCourses table is empty.')
            return None

        if course is None and user is None:
            return LTIInternalCourse.objects.all()

        if course is not None and user is not None:
            print('PLEASE IMPLEMENT ME :/')
            return None

        if course is not None:
            return LTIInternalCourse.objects.filter(course_fk__in=course)

        if user is not None:
            print('PLEASE IMPLEMENT ME :/')
            return None
