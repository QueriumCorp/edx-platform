# -*- coding: utf-8 -*-
"""
Lawrence McDaniel
lpm0073@gmail.com
https://lawrencemcdaniel.com

"""
from __future__ import absolute_import
import traceback
import datetime
import pytz
from django.conf import settings
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.grades.api.v2.views import InternalCourseGradeView
from common.djangoapps.third_party_auth.lti_consumers.willolabs.exceptions import LTIBusinessRuleError
from common.djangoapps.third_party_auth.lti_consumers.willolabs.models import LTIExternalCourse

from common.djangoapps.third_party_auth.lti_consumers.willolabs.utils import (
    get_ext_wl_outcome_service_url,
    get_lti_user_id,
    get_lti_cached_result_date,
    willo_activity_id_from_string,
    willo_id_from_url,
    is_lti_cached_user,
    willo_date,
    willo_api_post_grade,
    willo_api_create_column
    )

utc=pytz.UTC
VERBOSE=False

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

class LTIGradeSync:
    """
    Willo Labs LTI.

    Manages bulk grade sync (ie, all students / all assignments in a course).
    Currently this is only called from manage.py, but it could be used elsewhere.
    """
    course_id = None        # a string. Example: course-v1:ABC+OS9471721_9626+01
    course_key = None       # a opaque_keys.edx.keys.CourseKey
    context_id = None       # Willo Labs course identifier. Only used in cases where course_id is not unique. Example: e14751571da04dd3a2c71a311dda2e1b

    def __init__(self, course_id=None):
        if course_id is not None:
            self.course_id = course_id
            self.course_key = self.set_coursekey()
    
    def iterate_courses(self):
        """
         Iterate thru all LTI cached courses.
         Run grade sync on each course.
        """

        courses = LTIExternalCourse.objects.all()
        for course in courses:
            """
            set course_id and course_key from the CourseKey object in LTIExternalCourse
            
            You can read more here about why the syntax below works:
            https://github.com/edx/edx-platform/wiki/Opaque-Keys-(Locators)

            Note: we'll skip calling set_coursekey() bc in this case we're beginning 
            with a CourseKey from a confirmed Willo Labs LTI supported course
            (since the course came directly from the LTI course cache.)
            """
            course_id = "{}".format(course.course_id)
            self.context_id = course.context_id
            self.course_id = course_id
            self.course_key = course.course_id
            self.iterate_students()


    def iterate_students(self):
        """
         Iterate thru collection of students enrolled in course_id.
         Post grades to Willo Labs api.
        """
        if not self.course_key: raise LTIBusinessRuleError("course_id has not been set.")

        students = CourseEnrollment.objects.users_enrolled_in(self.course_key)
        for student in students:
            msg = u'iterate_students() - course_id: {course_id} Retrieving username: {username}.'.format(
                course_id=self.course_id,
                username=student.username
            )
            msg = color.BOLD + color.PURPLE + msg + color.END + color.END
            self.console_output(msg)
            self.post_student_grades(student)

        msg = u'iterate_students.py - Done! course_id: {course_id}.'.format(
            course_id=self.course_id
        )
        self.console_output(msg, text_style=style.SUCCESS)

        return None

    def post_student_grades(self, student):
        """
         Retrieve a json object of grade data for student.
         Iterate through chapters / assignments for the course.
         Post each assignment grade to Willo Labs api.
        """

        if not self.course_key: raise LTIBusinessRuleError("CourseKey has not been set.")
        """
         Prior to calling InternalCourseGradeView().get() we should to a sanity check on the 
         LTI cache data to see if this Rover user has ever authenticated via LTI. If not then
         we should just exit since we won't know the LTI user credentials.
        """
        if not is_lti_cached_user(student):
            self.console_output(u'    No LTI cache data for this user. Skipping.')
            return None
        
        results = InternalCourseGradeView().get(course_id=self.course_id, username=student.username)
        self.console_output(u'post_student_grades() - retrieved grades for {username} / {course_id}'.format(
            username=student.username,
            course_id=self.course_id
        ))

        # only process the course if courses have actually begun.
        enrollment_start = results.get('course_enrollment_start')
        if not enrollment_start < utc.localize(datetime.datetime.now()):
            msg = u'post_student_grades() - Skipping {course_id}. Course has not begun.'.format(
                course_id=self.course_id,
                )
            self.console_output(msg, text_style=style.NOTICE)
            return None

        # iterate the chapters and sections of the course, post
        # assignments to Willo Labs Grade sync if the assignment meets all criteria.
        #
        # chapters and chapter sections are both stored as dictionaries of key/value pairs,
        # with the "value" itself being a dictionary.
        for key, chapter in results['course_chapters'].items():
            for key, section in chapter['chapter_sections'].items():
                if self.should_gradesync_assignment(section):
                    try:
                        self.prepare_and_post_column(section)
                        self.prepare_and_post_grade(student, section)
                    except Exception as err:
                        msg='Exception encountered while processing Rover student {username}. Error: {err}.\r\n{traceback}'.format(
                            username=student.username,
                            err=err,
                            traceback=traceback.format_exc()
                        )
                        self.console_output(msg, text_style=style.ERROR)

    
    def prepare_and_post_grade(self, student, section):
        """
         Transform the section grade data into a Willo Labs grade sync payload dictionary, then post the grade.
        """
        section_grade = section.get('section_grade')
        url = get_ext_wl_outcome_service_url(self.course_id, self.context_id)
        lti_user_id = get_lti_user_id(
            course_id=self.course_id, 
            username=student.username, 
            context_id=self.context_id
            )
        if lti_user_id is None: raise LTIBusinessRuleError('Did not find a cached LTI user_id for Rover user {username}.'.format(
            username=student.username
        ))
        
        result_date = get_lti_cached_result_date(
            course_id=self.course_id,
            username=student.username,
            section_url=section.get('section_url'),
            section_completed_date=section.get('section_completed_date'), 
            section_due_date=section.get('section_due_date')
        )

        data = {
            "type": "result",
            "id": willo_id_from_url(section.get('section_url')),
            "activity_id": willo_activity_id_from_string(section.get('section_display_name')),
            "user_id": lti_user_id,
            "result_date": willo_date(result_date),
            "score": section_grade.get('section_grade_earned'),
            "points_possible": section_grade.get('section_grade_possible')
        }
        retval = willo_api_post_grade(ext_wl_outcome_service_url=url, data=data)
        if 200 <= retval <= 299:
            result_string = u'  prepare_and_post_grade() - SUCCESS! syncd grade for {user} / {assignment}'.format(
                user=student.username,
                assignment=section.get('section_display_name')
            )
            self.console_output(result_string, text_style=style.SUCCESS)
        else:
            result_string = u'  prepare_and_post_grade() - HTTP Error {http_response} returned. did not sync grade for {user} / {assignment}. section_completed_date: {section_completed_date} / section_due_date: {section_due_date}'.format(
                user=student.username,
                assignment=section.get('section_display_name'),
                http_response=retval,
                section_completed_date=section.get('section_completed_date'),
                section_due_date=section.get('section_due_date')
            )
            self.console_output(result_string, text_style=style.ERROR)

        return (200 <= retval <= 299)

    def prepare_and_post_column(self, section):
        """
         Transform the section grade data into a Willo Labs Column payload dictionary, then post the column.
        """
        section_grade = section.get('section_grade')

        url = get_ext_wl_outcome_service_url(self.course_id, self.context_id)
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
            self.console_output(result_string, text_style=style.SUCCESS)
        else:
            result_string = u'  prepare_and_post_column() - HTTP Error {http_response} returned. did not sync column {assignment}'.format(
                assignment=section.get('section_display_name'),
                http_response=retval
            )
            self.console_output(result_string, text_style=style.ERROR)

        return (200 <= retval <= 299)

    def should_gradesync_assignment(self, section):
        """
         Rover homework assignments that should be sync'd should meet any of the following
         criteria:
          - assignments due date has passed.
          - student has attempted at least one problem in the assignment.
        """
        section_display_name = section.get('section_display_name')
        msg=u'\n\r  should_gradesync_assignment() - Assignment: {section_display_name}.'.format(
            section_display_name=section_display_name,
        )
        self.console_output(msg, important=False)

        # evaluate section due date
        try:
            due_date = section.get('section_due_date')
            if due_date is not None:
                if due_date < utc.localize(datetime.datetime.now()): 
                    self.console_output(u'    - Yes. Section Due date has passed.', important=False)
                    return True
            else:
                self.console_output(u'    - Due date not set! Moving to next test...', important=False)
        except Exception as err:
            msg = u'    - Exception with Section Due date value: {due_date}. {err}'.format(
                due_date=due_date,
                err=err
            )
            self.console_output(msg, text_style=style.ERROR)
            pass

        # evaluate whether the assignment has been graded yet.
        try:
            section_graded = section.get('section_graded')
            if type(section_graded) == bool: 
                if section_graded: 
                    self.console_output(u'    - Yes. Section has been graded.', important=False)
                    return True
                else:
                    self.console_output(u'    - Section has not yet been graded. Moving to next test...', important=False)
        except Exception as err:
            msg = u'    - Exception with section_graded value: {section_graded}. {err}'.format(
                section_graded=section_graded,
                err=err
            )
            self.console_output(msg, text_style=style.ERROR)
            pass

        # evaluate whether the student has attempted any graded problems in this assignment.
        try:
            section_grade = section.get('section_grade')
            section_attempted_graded = section_grade.get('section_attempted_graded')
            if section_attempted_graded:
                self.console_output(u'    - Yes. Found at least one graded problem in this assignment.', important=False)
                return True
            else:
                self.console_output(u'    - Student has not yet attempted any problems in this assignment.', important=False)
        except Exception as err:
            msg = u'    - Exception with section grade earned: {section_attempted_graded}. {err}'.format(
                section_attempted_graded=section_attempted_graded,
                err=err
            )
            self.console_output(msg, text_style=style.ERROR)
            pass

        msg = u'    - NO. No criteria was met. Skipping this assignment.'
        self.console_output(msg, text_style=style.NOTICE, important=False)
        return False

    def set_coursekey(self):
        """
          Set the CourseKey based on the course_id provided.
          Verify that the course supports Willo Labs LTI Grade Sync.
        """
        # validate the course_id provided
        try:
            key = CourseKey.from_string(self.course_id)
        except Exception as err:
            msg = u'set_coursekey() - Not a valid course_id: {course_id}. {err}'.format(
                course_id=self.course_id,
                err=err
            )
            self.console_output(msg, text_style=style.ERROR)
            return False

        # verify that the course is a Willo Labs LTI course. If its a valid Willo Labs LTI course then
        # we'll find a cached course record.
        course = LTIExternalCourse.objects.filter(
            course_id=key
        )
        if course is not None: return key

        # didn't find the course in the LTI cache, so raise an error.
        raise LTIBusinessRuleError('The course_id provided is a valid Rover course identifier. However, this course does not support Willo Labs LTI Grade Sync.')

    def write_console_banner(self):

        msg = u'\r\n============================================================================\r\n'
        msg += u'     ' + color.BOLD + color.UNDERLINE + 'Willo Labs Grade Sync API.\r\n'
        msg += color.END + color.END
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

        self.console_output(msg)

    def console_output(self, msg, text_style=None, important=True):
        """
         Simulates BaseCommand "style" method.
        """
        if text_style is not None: msg = text_style + msg + style.END
        if VERBOSE or important:
            print(msg)
