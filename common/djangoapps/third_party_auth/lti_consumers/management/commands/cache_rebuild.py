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
from django.core.management.base import BaseCommand
from common.djangoapps.third_party_auth.lti_consumers.gradesync import LTIGradeSync

class Command(BaseCommand):
    help = u"LTI Grade Sync. Sync Rover grades to LTI Consumer for all students, all assignments. Includes all active Willo Labs Grade Sync-supported courses."

    def add_arguments(self, parser):
        parser.add_argument(
            u'-c',
            u'--course_id',
            type=str,
            help=u'A string representation of a CourseKey. Example: course-v1:ABC+OS9471721_9626+01'
            )


    def handle(self, *args, **kwargs):
        """
          Create a LTIGradeSync object for the course_id
        """
        print('course_id: {course_id}'.format(
            course_id=kwargs['course_id']
        ))

        if kwargs['course_id']: grade_sync = LTIGradeSync(kwargs['course_id'])
        else: grade_sync = LTIGradeSync()

        print('I AM NOT YET IMPLEMENTED :/')
        #grade_sync.write_console_banner()
        #grade_sync.iterate_courses()
        #grade_sync.write_console_banner()
