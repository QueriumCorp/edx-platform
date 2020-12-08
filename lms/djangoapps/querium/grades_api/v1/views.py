"""
API v2 views.

written by:     mcdaniel
date:           nov-2019

usage:          created as a generic set of grade data apis to be used to provide
                grade synch services to external LMS' via LTI, and more
                specifically, via Willo Labs LTI integration services.
"""
import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from openedx.core.lib.api.permissions import IsStaffOrOwner
from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.djangoapps.enrollments import data as enrollment_data
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from student.models import CourseEnrollment

# mcdaniel nov-2019
# additional stuff that we need for V2
import json
from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.conf import settings
from lms.djangoapps.grades.course_grade import CourseGrade
from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.subsection_grade_factory import SubsectionGradeFactory
#from openedx.core.djangoapps.models.course_details import CourseDetails

# LTI integration stuff
from common.djangoapps.third_party_auth.lti_consumers.models import (
    LTIInternalCourse,
    LTIExternalCourse
)
from student.models import CourseEnrollment


log = logging.getLogger(__name__)
USER_MODEL = get_user_model()



class AbstractGradesView(GenericAPIView, DeveloperErrorViewMixin):
    """
      mcdaniel nov-2019

      new abstract class so that we can quickly create a set of more granular
      grade data classes to provide to the grades api.

      1. take care of common initializations as well as a bunch of
      tedious parameter initializations.

      2. In the interest of keeping things compact we'll try to keep most/all
      of our parameter validations here in the abstract class so that our
      deployable classes only have to deal with grabbing and packaging data.
    """
    host = settings.SITE_NAME
    scheme = u"https" if settings.HTTPS == "on" else u"http"

    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    # mcdaniel dec-2020: adding IsStaffOrOwner to restrict use of this api.
    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS, IsStaffOrOwner,)
    required_scopes = ['grades:read']

    course_id = None
    chapter_id = None
    section_id = None
    grade_user = None
    course_key = None
    course_data = None
    course_grade = None
    course_url = None


    def get(self, request=None, course_id=None, chapter_id=None, section_id=None, grade_user=None):
        """
         Abstract getter.
         Mostly deals with initializations needed by child objects.

         Default usage as part of a REST api, but can also be called internally
         for reports, large grade dumps, manage.py utility apps, etcetera.

         Notes:
         mcdaniel dec-2020: revisit and correct this soon.
         - For REST api: request is required, and grade_user (if provided) is ignored.
         - For internal use: request is ignored, and grade_user is required.
        """
        # business rule enforcement
        #---------------------------------------------------------
        if request is None:
            if grade_user is None:
                raise Exception('grade_user is required if a request object is not provided.')

            if course_id is None:
                raise Exception('course_id is required if a request object is not provided.')


        # set and validate grade_user
        #---------------------------------------------------------
        if grade_user is not None:
            self.grade_user = grade_user
        else:
            self.grade_user = request.GET.get('grade_user')

        try:
            self.grade_user = USER_MODEL.objects.get(username=self.grade_user)
        except USER_MODEL.DoesNotExist:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The requested user does not exist.',
                error_code='user_does_not_exist'
            )

        # set course_id
        #---------------------------------------------------------
        if course_id:
            self.course_id = course_id
        else:
            self.course_id = request.GET.get('course_id')


        # set chapter_id
        #---------------------------------------------------------
        if chapter_id:
            self.chapter_id = chapter_id
        else:
            if request is not None: self.chapter_id = request.GET.get('chapter_id')

        # set section_id
        #---------------------------------------------------------
        if section_id:
            self.section_id = section_id
        else:
            if request is not None: self.section_id = request.GET.get('section_id')


        # ID validations
        #---------------------------------------------------------
        if not self.course_id:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='You must provide a course_id for this view.',
                error_code='missing_course_id'
            )

        # Validate course exists with provided course_id
        try:
            self.course_key = CourseKey.from_string(self.course_id)
        except InvalidKeyError:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The provided course key cannot be parsed.',
                error_code='invalid_course_key'
            )


        if not CourseOverview.get_from_id(self.course_key):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="Requested grade for unknown course {course}".format(course=self.course_id),
                error_code='course_does_not_exist'
            )


        if not enrollment_data.get_course_enrollment(self.grade_user, str(self.course_key)):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The user is not enrolled in this course',
                error_code='user_not_enrolled'
            )


        self.course_url = u'{scheme}://{host}/{url_prefix}/{course_id}/courseware/'.format(
                scheme = self.scheme,
                host=self.host,
                url_prefix='courses',
                course_id=self.course_id
                )

        # use our validated user and course_key to create a CourseData object.
        # then use the CourseData object to create a CourseGrade object, which
        # in turn contains several prebuilt methods to return grade data at
        # varying levels of detail.
        self.course_data = CourseData(user=self.grade_user, course=None, collected_block_structure=None, structure=None, course_key=self.course_key)
        self.course_grade = CourseGradeFactory().read(self.grade_user, course_key=self.course_key)

        return

    def _calc_grade_percentage(self, earned, possible):
        """
            calculate the floating point percentage grade score based on the
            integer parameters "earned" and "possible"
        """
        f_grade = float(0)
        if possible != 0:
            f_grade = float(earned) / float(possible)
        return f_grade

    def get_course_dict(self):
        return {
            'student': {
                'username': self.grade_user.username,
                'email': self.grade_user.email,
                'first_name': self.grade_user.first_name,
                'last_name': self.grade_user.last_name,
            },
            'course_grade': {
                'course_passed': self.course_grade.passed,
                'course_grade_percent': self.course_grade.percent,
                'course_grade_letter': self.course_grade.letter_grade,
            },
            # course identifiers
            'course_id': self.course_id,
            'course': CourseKey.from_string(self.course_id).course,
            'organization': CourseKey.from_string(self.course_id).org,
            'course_run': CourseKey.from_string(self.course_id).run,
            'course_url': self.course_url,
            'course_name': CourseOverview.get_from_id(self.course_key).display_name,

            # course details
            'course_version': CourseOverview.get_from_id(self.course_key).version,
            'course_image_url': CourseOverview.get_from_id(self.course_key).course_image_url,
            'course_start_date': CourseOverview.get_from_id(self.course_key).start,
            'course_end': CourseOverview.get_from_id(self.course_key).end,
            'course_has_started': CourseOverview.get_from_id(self.course_key).has_started(),
            'course_has_ended': CourseOverview.get_from_id(self.course_key).has_ended(),
            'course_lowest_passing_grade': CourseOverview.get_from_id(self.course_key).lowest_passing_grade,
            'course_enrollment_start': CourseOverview.get_from_id(self.course_key).enrollment_start,
            'course_enrollment_end': CourseOverview.get_from_id(self.course_key).enrollment_end,
            'course_prerequisites': CourseOverview.get_from_id(self.course_key)._pre_requisite_courses_json,
            'course_description': CourseOverview.get_from_id(self.course_key).short_description,
            'course_effort': CourseOverview.get_from_id(self.course_key).effort,
            'course_self_paced': CourseOverview.get_from_id(self.course_key).self_paced,
            'course_marketing_url': CourseOverview.get_from_id(self.course_key).marketing_url,
            'course_eligible_for_financial_aid': CourseOverview.get_from_id(self.course_key).eligible_for_financial_aid,
            'course_language': CourseOverview.get_from_id(self.course_key).closest_released_language,
            }

    def get_chapter_dict(self, chapter):
        """
            returns one chapter tuple, with an array of sections.
        """

        sections = {}
        for section in chapter['sections']:
            if section.attempted_graded or section.due is not None:
                # build a dictionary containing any graded assignments which the student
                # has attempted, or, have an assigned due date.
                sections[section.url_name] = self.get_section_dict(chapter, section)

        return {
                    'chapter_url': self.course_url + chapter['url_name'],
                    'chapter_display_name': chapter['display_name'],
                    'chapter_sections': sections,
                }

    def get_section_dict(self, chapter, section):
        """
            returns a tuple dictionary of grade data for one subsection of a chapter.

            * note: subsections are identifyable as "Sections" in the LMS UI.
        """
        grades_factory = SubsectionGradeFactory(student=self.grade_user, course=None, course_structure=None, course_data=self.course_data)
        subsection_grades = grades_factory.create(subsection=section, read_only=True)
        problems = {}
        for problem_key_BlockUsageLocator, problem_ProblemScore in subsection_grades.problem_scores.items():
            problems[str(problem_key_BlockUsageLocator)] = self.get_problem_dict(
                                                            problem_key_BlockUsageLocator,
                                                            problem_ProblemScore
                                                            )

        return {
            'section_url': self.course_url + chapter['url_name'] + '/' + section.url_name,
            'section_location': str(section.location),
            'section_display_name': section.display_name,
            'section_due_date': section.due,
            'section_completed_date': None,
            'section_problems': problems,
            'section_course_version': str(section.course_version),
            'section_format': section.format,
            'section_graded': section.graded,
            'section_show_correctness': section.show_correctness,
            'section_subtree_edited_timestamp': section.subtree_edited_timestamp,
            'section_grade': {
                'section_attempted_graded': section.attempted_graded,
                'section_grade_earned': section.all_total.earned,
                'section_grade_possible': section.all_total.possible,
                'section_grade_percent':  self._calc_grade_percentage(
                                        section.all_total.earned,
                                        section.all_total.possible
                                        ),
                },
            }

    def get_problem_dict(self, problem_key_BlockUsageLocator, problem_ProblemScore):
        """
            returns an array of tuples of the individual problem grade results from a subsection of a chapter.

            * note: subsections are identifyable as "Sections" in the LMS UI.
        """
        return {
                'problem_raw_earned': problem_ProblemScore.raw_earned,
                'problem_raw_possible': problem_ProblemScore.raw_possible,
                'problem_earned': problem_ProblemScore.earned,
                'problem_possible': problem_ProblemScore.possible,
                'problem_weight': problem_ProblemScore.weight,
                'problem_grade_percentage': self._calc_grade_percentage(
                                        problem_ProblemScore.earned,
                                        problem_ProblemScore.possible
                                        )
                }
class InternalLTICourses(AbstractGradesView):
    """Used for requests from manage.py

    Returns:
        json dict of LTI-enabled courses
    """
    def get(self):

        courses_list = []
        courses = LTIInternalCourse.objects.all()
        for course in courses:
            course = course.course_fk

            course_dict = {}
            course_dict.course_id = str(course.course_id)

            enrollments = CourseEnrollment.objects.filter(
                course=course
            )

            courses_enrollments = []
            for enrollment in enrollments:
                courses_enrollments.append(enrollment.user.username)

            course_dict.enrollments = courses_enrollments
            courses_list.append(course_dict)

        return courses_list

class InternalCourseGradeView(AbstractGradesView):
    """
     Used for requests from manage.py
     Returns a json dict
    """
    def get(self, course_id, grade_user):
        super(InternalCourseGradeView, self).get(course_id=course_id, grade_user=grade_user)

        chapters = {}
        for chapter in self.course_grade.chapter_grades.values():
            chapters[chapter['url_name']] = self.get_chapter_dict(chapter)

        course_dict = self.get_course_dict()
        course_dict['course_chapters'] = chapters

        return course_dict

class CourseGradeView(AbstractGradesView):
    """
     api view - entire course
    """
    def get(self, request=None, course_id=None):
        super(CourseGradeView, self).get(request=request, course_id=course_id, chapter_id=None, section_id=None)

        chapters = {}
        if not self.course_grade or not self.course_grade.chapter_grades:
            return Response({})

        for chapter in self.course_grade.chapter_grades.values():
            chapters[chapter['url_name']] = self.get_chapter_dict(chapter)

        course_dict = self.get_course_dict()
        course_dict['course_chapters'] = chapters

        return Response(course_dict)

class ChapterGradeView(AbstractGradesView):
    """
     api view - course chapter
    """
    def get(self, request=None, course_id=None, chapter_id=None):
        log.info('ChapterGradeView: course_id={course_id}, chapter_id={chapter_id}'.format(
            course_id=course_id,
            chapter_id=chapter_id
        ))
        super(ChapterGradeView, self).get(request=request, course_id=course_id, chapter_id=chapter_id, section_id=None)
        for chapter in self.course_grade.chapter_grades.values():
            if chapter['url_name'] == chapter_id:
                return Response(self.get_chapter_dict(chapter))

        return HttpResponseNotFound("HTTP Error 404: Requested chapter_id {chapter_id} not found.".format(
            chapter_id=self.chapter_id
            ))

class SectionGradeView(AbstractGradesView):
    """
     api view - section of a chapter
    """
    def get(self, request=None, course_id=None, chapter_id=None, section_id=None):
        log.info('ChapterGradeView: course_id={course_id}, chapter_id={chapter_id}, section_id={section_id}'.format(
            course_id=course_id,
            chapter_id=chapter_id,
            section_id=section_id
        ))
        super(SectionGradeView, self).get(request=request, course_id=course_id, chapter_id=chapter_id, section_id=section_id)
        for chapter in self.course_grade.chapter_grades.values():
            if chapter['url_name'] == chapter_id:
                for section in chapter['sections']:
                    if section.url_name == section_id:
                        return Response(self.get_section_dict(chapter, section))

        return HttpResponseNotFound("HTTP Error 404: Requested chapter_id/section_id {chapter_id}/{section_id} not found.".format(
            chapter_id=self.chapter_id,
            section_id=self.section_id
            ))

class SectionGradeViewUser(AbstractGradesView):
    """
     api view - section of a chapter for specified user
     currently being used within manage.py rather than as a RESTapi view.
    """
    def get(self, request=None, course_id=None, chapter_id=None, section_id=None, grade_user=None):
        log.info('SectionGradeViewUser: course_id={course_id}, chapter_id={chapter_id}, section_id={section_id}, grade_user={grade_user}'.format(
            course_id=course_id,
            chapter_id=chapter_id,
            section_id=section_id,
            grade_user=grade_user
        ))
        super(SectionGradeViewUser, self).get(request=request, course_id=course_id, chapter_id=chapter_id, section_id=section_id, grade_user=grade_user)
        for chapter in self.course_grade.chapter_grades.values():
            if chapter['url_name'] == chapter_id:
                for section in chapter['sections']:
                    if section.url_name == section_id:
                        return self.get_section_dict(chapter, section)

       print("Requested chapter_id/section_id/grade_user {chapter_id}/{section_id}/{grade_user} not found.".format(
            chapter_id=self.chapter_id,
            section_id=self.section_id,
            grade_user=grade_user
            ))
