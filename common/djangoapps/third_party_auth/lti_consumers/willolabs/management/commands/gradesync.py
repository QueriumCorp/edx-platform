import datetime
import pytz
from django.conf import settings
from django.core.management.base import BaseCommand
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.grades.api.v2.views import InternalCourseGradeView

from common.djangoapps.third_party_auth.lti_consumers.willolabs.utils import (
    get_ext_wl_outcome_service_url,
    get_lti_user_id,
    get_lti_cached_result_date,
    willo_activity_id_from_string,
    willo_id_from_url,
    willo_date,
    willo_api_post_grade,
    willo_api_create_column
    )

utc=pytz.UTC

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

u"""
  Willo Labs Grade Sync.
  Process all assignment grades from all students enrolled in course_id

  https://dev.roverbyopenstax.org/grades_api/v2/courses/course-v1:ABC+OS9471721_9626+01/

  Run from the command line like this:
  cd /edx/app/edxapp/edx-platform
  sudo -u www-data /edx/bin/python.edxapp ./manage.py lms --settings aws gradesync course-v1:ABC+OS9471721_9626+01

"""
class Command(BaseCommand):
    help = u"Willo Labs Grade Sync. Post all assignment grades from all students enrolled in course_id."
    course_key = None
    course_id = None

    def add_arguments(self, parser):
        parser.add_argument('course_id', 
            type=str,
            help=u'A string representation of a CourseKey. Example: course-v1:ABC+OS9471721_9626+01'
            )

    def handle(self, *args, **kwargs):
        self.course_id = kwargs['course_id']
        self.course_key = self.set_coursekey()
        if not self.course_key: 
            return None

        self.write_console_banner()
        self.iterate_students()

        self.stdout.write(self.style.SUCCESS(u'gradesync.py - Done! course_id: {course_id}.'.format(
            course_id=self.course_id
        )))
        self.write_console_banner()


    def iterate_students(self):
        """
         Iterate thru collection of students enrolled in course_id.
         Post grades to Willo Labs api.
        """
        students = CourseEnrollment.objects.users_enrolled_in(self.course_key)
        for student in students:
            msg = u'iterate_students() - retrieving username: {username}.'.format(
                username=student.username
            )
            msg = color.BOLD + color.PURPLE + msg + color.END + color.END
            self.stdout.write(msg)
            self.post_student_grades(student)

        return None

    def post_student_grades(self, student):
        """
         Retrieve a json object of grade data for student.
         Iterate through chapters / assignments for the course.
         Post each assignment grade to Willo Labs api.
        """

        results = InternalCourseGradeView().get(course_id=self.course_id, username=student.username)
        self.stdout.write(u'post_student_grades() - retrieved grades for {username} / {course_id}'.format(
            username=student.username,
            course_id=self.course_id
        ))

        # only process the course if courses have actually begun.
        enrollment_start = results.get('course_enrollment_start')
        if not enrollment_start < utc.localize(datetime.datetime.now()):
            self.stdout.write(
                self.style.NOTICE(u'post_student_grades() - Skipping {course_id}. Course has not begun.'.format(
                course_id=self.course_id,
                )))
            return None

        # iterate the chapters and sections of the course, post
        # assignments to Willo Labs Grade sync if the assignment meets all criteria.
        #
        # chapters and chapter sections are both stored as dictionaries of key/value pairs,
        # with the "value" itself being a dictionary.
        for key, chapter in results['course_chapters'].items():
            for key, section in chapter['chapter_sections'].items():
                if self.should_gradesync_assignment(section):
                    self.prepare_and_post_column(section)
                    self.prepare_and_post_grade(student, section)
    
    def prepare_and_post_grade(self, student, section):
        """
         Transform the section grade data into a Willo Labs grade sync payload dictionary, then post the grade.
        """
        section_grade = section.get('section_grade')
        section_completed_date = section.get('section_completed_date')
        if section_completed_date is None: section_completed_date = section.get('section_due_date')
            
        url = get_ext_wl_outcome_service_url(self.course_id)
        data = {
            "type": "result",
            "id": willo_id_from_url(section.get('section_url')),
            "activity_id": willo_activity_id_from_string(section.get('section_display_name')),
            "user_id": get_lti_user_id(self.course_id, student.username),
            "result_date": willo_date(section_completed_date),
            "score": section_grade.get('section_grade_earned'),
            "points_possible": section_grade.get('section_grade_possible')
        }
        retval = willo_api_post_grade(ext_wl_outcome_service_url=url, data=data)
        if 200 <= retval <= 299:
            result_string = u'  prepare_and_post_grade() - SUCCESS! syncd grade for {user} / {assignment}'.format(
                user=student.username,
                assignment=section.get('section_display_name')
            )
            self.stdout.write(self.style.SUCCESS(result_string))
        else:
            result_string = u'  prepare_and_post_grade() - HTTP Error {http_response} returned. did not sync grade for {user} / {assignment}'.format(
                user=student.username,
                assignment=section.get('section_display_name'),
                http_response=retval
            )
            self.stdout.write(self.style.SUCCESS(result_string))

        return (200 <= retval <= 299)

    def prepare_and_post_column(self, section):
        """
         Transform the section grade data into a Willo Labs Column payload dictionary, then post the column.
        """
        section_grade = section.get('section_grade')

        url = get_ext_wl_outcome_service_url(self.course_id)
        data = {
            "type": "activity",
            "id": willo_activity_id_from_string(section.get('section_display_name')),
            "title": section.get('section_display_name'),
            "description": section.get('section_display_name'),
            "due_date": willo_date(section.get('section_due_date')),
            "points_possible": section_grade.get('section_grade_possible')
        }
        retval = willo_api_create_column(ext_wl_outcome_service_url=url, data=data)
        if 200 <= retval <= 299:
            result_string = u'  prepare_and_post_column() - SUCCESS! syncd column for {assignment}'.format(
                assignment=section.get('section_display_name')
            )
            self.stdout.write(self.style.SUCCESS(result_string))
        else:
            result_string = u'  prepare_and_post_column() - HTTP Error {http_response} returned. did not sync column {assignment}'.format(
                assignment=section.get('section_display_name'),
                http_response=retval
            )
            self.stdout.write(self.style.SUCCESS(result_string))

        return (200 <= retval <= 299)

    def should_gradesync_assignment(self, section):
        """
         Rover homework assignments that should be sync'd should meet any of the following
         criteria:
          - assignments due date has passed.
          - student has attempted at least one problem in the assignment.
        """
        section_display_name = section.get('section_display_name')
        self.stdout.write(u'\n\r  should_gradesync_assignment() - Assignment: {section_display_name}.'.format(
            section_display_name=section_display_name,
        ))

        # evaluate section due date
        try:
            due_date = section.get('section_due_date')
            if due_date is not None:
                if due_date < utc.localize(datetime.datetime.now()): 
                    self.stdout.write(u'    - Yes. Section Due date has passed.')
                    return True
            else:
                self.stdout.write(u'    - Due date not set! Moving to next test...')
        except Exception as err:
            self.stdout.write(self.style.ERROR(u'    - Exception with Section Due date value: {due_date}. {err}'.format(
                due_date=due_date,
                err=err
            )))
            pass

        # evaluate whether the assignment has been graded yet.
        try:
            section_graded = section.get('section_graded')
            if type(section_graded) == bool: 
                if section_graded: 
                    self.stdout.write(u'    - Yes. Section has been graded.')
                    return True
                else:
                    self.stdout.write(u'    - Section has not yet been graded. Moving to next test...')
        except Exception as err:
            self.stdout.write(self.style.ERROR(u'    - Exception with section_graded value: {section_graded}. {err}'.format(
                section_graded=section_graded,
                err=err
            )))
            pass

        # evaluate whether the student has attempted any graded problems in this assignment.
        try:
            section_grade = section.get('section_grade')
            section_attempted_graded = section_grade.get('section_attempted_graded')
            if section_attempted_graded:
                self.stdout.write(u'    - Yes. Found at least one graded problem in this assignment.')
                return True
            else:
                self.stdout.write(u'    - Student has not yet attempted any problems in this assignment.')
        except Exception as err:
            self.stdout.write(self.style.ERROR(u'    - Exception with section grade earned: {section_attempted_graded}. {err}'.format(
                section_attempted_graded=section_attempted_graded,
                err=err
            )))
            pass

        self.stdout.write(self.style.NOTICE(u'    - NO. No criteria was met. Skipping this assignment.'))
        return False

    def set_coursekey(self):
        try:
            key = CourseKey.from_string(self.course_id)
            return key
        except Exception as err:
            self.stdout.write(self.style.ERROR(u'set_coursekey() - Not a valid course_id: {course_id}. {err}'.format(
                course_id=self.course_id,
                err=err
            )))
            return False
    
    def write_console_banner(self):

        msg = u'\r\n============================================================================\r\n'
        msg += color.BOLD
        msg += u'     Willo Labs Grade Sync API.\r\n'
        msg += color.END
        msg += u'\r\n'
        msg += color.RED + color.BOLD
        msg += u'     BE AWARE:\r\n'
        msg += u'     YOU ARE TRANSMITTING LIVE GRADE DATA FROM ROVER TO WILLO LABS.\r\n'
        msg += u'     THIS OPERATION WILL POTENTIALLY MODIFY STUDENT GRADES IN A REMOTE LMS.\r\n'
        msg += u'     MODIFICATIONS TO STUDENT DATA TAKE EFFECT IMMEDIATELY AND CAN BE VIEWED AT\r\n'
        msg += u'     https://willowlabs.instructure.com/.\r\n'
        msg += color.END + color.END
        msg += u'\r\n'
        msg += u'\r\n'
        msg += color.BOLD
        msg += u'     Using Willo Labs api token: ' + color.DARKCYAN + settings.WILLO_API_AUTHORIZATION_TOKEN + color.END
        msg += u'\r\n'
        msg += u'\r\n'
        msg += u'     This api token is provided directly by Willo Labs staff. It is\n\r'
        msg += u'     referenced in the source code as\n\r'
        msg += u'              WILLO_API_AUTHORIZATION_TOKEN\n\r'
        msg += u'     and is stored in the following two Python settings files:\n\r'
        msg += u'     /edx/app/edxapp/edx-platform/lms/envs/aws.py\n\r'
        msg += u'     /edx/app/edxapp/edx-platform/cms/envs/aws.py\n\r'
        msg += color.END
        msg += u'\r\n'
        msg += u'\r\n'
        msg += u'     Willo Labs technical contact:       Rover technical contact:\r\n'
        msg += u'     ----------------------------        ------------------------\r\n'
        msg += u'     Matt Hanger                         Kent Fuka\r\n'
        msg += u'     matt.hanger@willolabs.com           kent@querium.com\r\n'
        msg += u'\r\n'
        msg += u'============================================================================\r\n'
        msg += u'\r\n'

        self.stdout.write(msg)

"""
    self.stdout.write(self.style.ERROR('error - A major error.'))
    self.stdout.write(self.style.NOTICE('notice - A minor error.'))
    self.stdout.write(self.style.SUCCESS('success - A success.'))
    self.stdout.write(self.style.WARNING('warning - A warning.'))
    self.stdout.write(self.style.SQL_FIELD('sql_field - The name of a model field in SQL.'))
    self.stdout.write(self.style.SQL_COLTYPE('sql_coltype - The type of a model field in SQL.'))
    self.stdout.write(self.style.SQL_KEYWORD('sql_keyword - An SQL keyword.'))
    self.stdout.write(self.style.SQL_TABLE('sql_table - The name of a model in SQL.'))
    self.stdout.write(self.style.HTTP_INFO('http_info - A 1XX HTTP Informational server response.'))
    self.stdout.write(self.style.HTTP_SUCCESS('http_success - A 2XX HTTP Success server response.'))
    self.stdout.write(self.style.HTTP_NOT_MODIFIED('http_not_modified - A 304 HTTP Not Modified server response.'))
    self.stdout.write(self.style.HTTP_REDIRECT('http_redirect - A 3XX HTTP Redirect server response other than 304.'))
    self.stdout.write(self.style.HTTP_NOT_FOUND('http_not_found - A 404 HTTP Not Found server response.'))
    self.stdout.write(self.style.HTTP_BAD_REQUEST('http_bad_request - A 4XX HTTP Bad Request server response other than 404.'))
    self.stdout.write(self.style.HTTP_SERVER_ERROR('http_server_error - A 5XX HTTP Server Error response.'))
    self.stdout.write(self.style.MIGRATE_HEADING('migrate_heading - A heading in a migrations management command.'))
    self.stdout.write(self.style.MIGRATE_LABEL('migrate_label - A migration name.'))

"""