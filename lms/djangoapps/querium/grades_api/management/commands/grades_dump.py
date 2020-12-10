"""
  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Dec-2020

  Dump raw Open edX grade data to console

  Run from the command line like this:
    sudo -H -u edxapp bash
    cd ~
    source edxapp_env
    source venvs/edxapp/bin/activate
    cd edx-platform
    python manage.py lms grades_dump -c course-v1:KU+OS9471721_2955+Fall2020_Master_Shell_Weiland -u 091bacd864ee84f91e24611c54867a -a d79c1e0244ff4db180c7bdfce53d9dd8

"""
# django stuff
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

# open edx stuff
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

# rover stuff
from lms.djangoapps.querium.grades_api.v1.views import SectionGradeViewUser


User = get_user_model()

class Command(BaseCommand):
    help = u"Dump raw problem-level grade data to the console."

    def add_arguments(self, parser):
        parser.add_argument(
            u'-c',
            u'--course_id',
            type=str,
            help=u'A string representation of a CourseKey. Example: course-v1:CalStateLA+MATH1081_2513+Fall2020_Chavez_TTR1050-1205'
            )
        parser.add_argument(
            u'-u',
            u'--username',
            type=str,
            help=u'A Rover username. Example: 091bacd864ee84f91e24611c54867a'
            )
        parser.add_argument(
            u'-a',
            u'--assignment',
            type=str,
            help=u'Unique identifier of assignment key. Example: d79c1e0244ff4db180c7bdfce53d9dd8'
            )


    def handle(self, *args, **kwargs):

        course_id = kwargs['course_id']
        username = kwargs['username']
        assignment = kwargs['assignment']

        course = None
        user = None

        course_key = CourseKey.from_string(course_id)
        if course_id: course = CourseOverview.objects.filter(id=course_key)
        if username: user = User.objects.get(username=username)

        print(course_key)
        print(course)

        grades = SectionGradeViewUser()
        grades_dict = grades.get(request=None, course_id=course_id, chapter_id=None, section_id=assignment, grade_user=username)
        