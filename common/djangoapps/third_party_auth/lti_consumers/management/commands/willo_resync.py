u"""
  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Sep-2020

  LTI Grade Sync
  Repost all cached grade data to Willo Labs.

  Run from the command line like this:
  sudo -H -u edxapp bash
    cd ~
    source edxapp_env
    source venvs/edxapp/bin/activate
    cd edx-platform
    python manage.py lms --settings production willo_resync --dry-run --course_id course-v1:edX+DemoX+Demo_Course


"""
from django.conf import settings
from django.core.management.base import BaseCommand
from common.djangoapps.third_party_auth.lti_consumers.tasks import post_grades
from common.djangoapps.third_party_auth.lti_consumers.models import (
    LTIInternalCourse,
    LTIExternalCourse,
    LTIExternalCourseEnrollment,
    LTIExternalCourseAssignments,
    LTIExternalCourseEnrollmentGrades
)

# open edx stuff
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from ...utils import get_lti_courses

VERBOSE = False
DEBUG = settings.ROVER_DEBUG

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class style:
    SUCCESS = color.GREEN
    NOTICE = color.RED
    ERROR = color.RED
    END = color.END
    BOLD = color.BOLD
    UNDERLINE = color.UNDERLINE

class Command(BaseCommand):
    help = u"LTI Willo Labs Grade Re-sync. Iterates cached grade data for the course_id and re-posts all student assignment grades to Willo Labs api."

    def add_arguments(self, parser):
        parser.add_argument(
            u'-c',
            u'--course_id',
            type=str,
            help=u'Optional: A string representation of a CourseKey. Example: course-v1:ABC+OS9471721_9626+01'
            )
        parser.add_argument(
            '--dry-run',
            dest='dry_run',
            action='store_true',
            help='Optional: Iterates cache data and produces console output but does not push grades to Willo Labs.')


    def handle(self, *args, **kwargs):

        course_id=kwargs['course_id']
        dry_run=kwargs['dry_run']


        course = CourseOverview.objects.filter(id=course_id)
        lti_internal_courses = get_lti_courses(course)
        if lti_internal_courses is None:
            print('No LTIInternalCourses found for course_id. Exiting.')
            return None

        for lti_internal_course in lti_internal_courses:
            course_id = str(lti_internal_course.course_fk.id)
            lti_cache = LTICacheManager(course_id=course_id, user=user)
            try:
                self.resync_course(str(lti_internal_course.course_id), dry_run)
            except:
                pass


    def resync_course(self, course_id, dry_run):
        lti_internal_course = LTIInternalCourse.objects.filter(course_id=course_id).first()
        course = LTIExternalCourse.objects.filter(course_id=lti_internal_course).first()
        if not course:
            self.console_output('No LTIExternalCourse record found for {course_id}, exiting.'.format(course_id=course_id))
            return

        enrollments = LTIExternalCourseEnrollment.objects.filter(course=course)
        if not enrollments:
            self.console_output('No enrollments found for {course_id}, exiting.'.format(course_id=course_id))
            return

        assignments = LTIExternalCourseAssignments.objects.filter(course=course)
        if not assignments:
            self.console_output('No assignments found for {course_id}, exiting.'.format(course_id=course_id))
            return

        self.course_id=course_id
        self.context_id=course.context_id
        self.assignments=assignments.count()
        self.enrollments=enrollments.count()
        self.write_console_banner()

        for enrollment in enrollments:
            for assignment in assignments:
                username=enrollment.user.username
                grade = LTIExternalCourseEnrollmentGrades.objects.filter(
                    course_enrollment=enrollment,
                    course_assignment=assignment
                ).first()

                if grade:
                    usage_id=str(grade.usage_key)
                    self.console_output('Queueing course_id: {course_id}, username: {username}, usage_id: {usage_id}'.format(
                        course_id=course_id,
                        username=enrollment.user.username,
                        usage_id=usage_id
                    ))

                    # send this grade to Celery
                    if not dry_run: post_grades(username=username, course_id=course_id, usage_id=usage_id)
                    else: self.console_output('DRY RUN: Grade data was not sent to Willo Labs.')
                else:
                    print('No cached grade found for user {username}, assignment {display_name}'.format(
                        username=username,
                        display_name=assignment.display_name
                    ))

    def write_console_banner(self):

        msg = color.BOLD + u'\r\n'
        msg += '=' * 80
        msg += '\r\n' + color.END
        msg += u'     ' + color.BOLD + color.UNDERLINE + 'Willo Labs Grade Sync API.\r\n'
        msg += color.END + color.END
        msg += u'\r\n'
        msg += color.RED + color.BOLD
        msg += u'     BE AWARE:\r\n'
        msg += u'     YOU ARE TRANSMITTING LIVE GRADE DATA FROM ROVER TO AN LTI CONSUMER.\r\n'
        msg += u'     THIS OPERATION WILL POTENTIALLY MODIFY STUDENT GRADES IN A REMOTE LMS.\r\n'
        msg += u'     MODIFICATIONS TO STUDENT DATA TAKE EFFECT IMMEDIATELY AND CAN BE VIEWED AT\r\n'
        msg += u'     https://apps.willowlabs.com/.\r\n'
        msg += color.END
        msg += u'\r\n'
        msg += u'\r\n'
        msg += color.BOLD
        msg += u'     Using Willo Labs api token: ' + color.DARKCYAN + settings.LTI_CONSUMER_API_AUTHORIZATION_TOKEN + color.END
        msg += u'\r\n'
        msg += u'\r\n'
        msg += u'\r\n'
        msg += u'     course_id: ' + color.DARKCYAN + self.course_id + color.END
        msg += u'\r\n'
        msg += u'     context_id: ' + color.DARKCYAN + self.context_id + color.END
        msg += u'\r\n'
        msg += u'     enrollments: ' + color.DARKCYAN + str(self.enrollments) + color.END
        msg += u'\r\n'
        msg += u'     assignments: ' + color.DARKCYAN + str(self.assignments) + color.END
        msg += u'\r\n'
        msg += u'\r\n'
        msg += u'\r\n'
        msg += u'     This api token is provided directly by Willo Labs staff. It is\n\r'
        msg += u'     referenced in the source code as\n\r'
        msg += u'              LTI_CONSUMER_API_AUTHORIZATION_TOKEN\n\r'
        msg += u'     and is stored in the following two Python settings files:\n\r'
        msg += u'     /edx/app/edxapp/edx-platform/lms/envs/roversecrets.py\n\r'
        msg += u'     /edx/app/edxapp/edx-platform/cms/envs/roversecrets.py\n\r'
        msg += u'\r\n'
        msg += u'     * roversecrets.py is installled by the Provisioner from s3://secrets.roverbyopenstax.org'
        msg += u'\r\n'
        msg += color.END
        msg += u'\r\n'
        msg += u'\r\n'
        msg += u'     Willo Labs technical contact:       Rover technical contact:\r\n'
        msg += u'     ----------------------------        ------------------------\r\n'
        msg += u'     Matt Hanger                         Kent Fuka\r\n'
        msg += u'     matt.hanger@willolabs.com           kent@querium.com\r\n'
        msg += u'\r\n' + color.BOLD
        msg += '=' * 80
        msg += '\r\n' + color.END

        #msg += u'\r\n'

        self.console_output(msg)



    def console_output(self, msg, text_style=None, important=True):
        """
         Simulates BaseCommand "style" method.
        """
        if text_style is not None: msg = text_style + msg + style.END
        if VERBOSE or important:
            print(msg)
