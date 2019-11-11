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

from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.authentication import JwtAuthentication
from enrollment import data as enrollment_data
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser
)
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from student.models import CourseEnrollment

# mcdaniel nov-2019
# additional stuff that we need for V2
import json
from django.contrib.auth.decorators import login_required
from django.conf import settings
from lms.djangoapps.grades.course_grade import CourseGrade
from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.subsection_grade_factory import SubsectionGradeFactory

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
    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)
    required_scopes = ['grades:read']

    course_id = None
    chapter_id = None
    section_id = None
    username = None
    user = None
    grade_user = None
    course_key = None
    course_data = None
    course_grade = None
    course_url = None

    def get(self, request, course_id=None, chapter_id=None, section_id=None):

        # set and validate username
        #---------------------------------------------------------
        if 'username' in request.GET:
            self.username = request.GET.get('username')
        else:
            self.username = request.user.username

        if not self.username:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='Username is required for this view.',
                error_code='missing_username'
            )

        try:
            self.grade_user = USER_MODEL.objects.get(username=self.username)
            self.user = self.grade_user
        except USER_MODEL.DoesNotExist:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The requested user does not exist.',
                error_code='user_does_not_exist'
            )

        # set and validate course_id
        #---------------------------------------------------------
        if course_id:
            self.course_id = course_id
        else:
            self.course_id = request.GET.get('course_id')


        # set and validate chapter_id
        #---------------------------------------------------------
        if chapter_id:
            self.chapter_id = chapter_id
        else:
            self.chapter_id = request.GET.get('chapter_id')

        # set and validate section_id
        #---------------------------------------------------------
        if section_id:
            self.section_id = section_id
        else:
            self.section_id = request.GET.get('section_id')


        # ID validations
        #---------------------------------------------------------
        if not self.course_id and not self.chapter_id and not self.section_id:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='You must provide at least one of course_id, chapter_id, section_id for this view.',
                error_code='missing_id'
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

        if not CourseOverview.get_from_id_if_exists(self.course_key):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="Requested grade for unknown course {course}".format(course=self.course_id),
                error_code='course_does_not_exist'
            )

        if not enrollment_data.get_course_enrollment(self.username, str(self.course_key)):
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
        # in turn contain several prebuilt methods to return grade data at
        # varying levels of detail.
        self.course_data = CourseData(user=self.grade_user, course=None, collected_block_structure=None, structure=None, course_key=self.course_key)
        self.course_grade = CourseGradeFactory().read(self.grade_user, course_key=self.course_key)

        return

    def test_response(self, course_id=None, chapter_id=None):
        return  {
            'key': 'success!',
            'course_id': str(course_id),
            'chapter_id': str(chapter_id)
        }
    def _calc_grade_percentage(self, earned, possible):
        """
            calculate the floating point percentage grade score based on the
            integer parameters "earned" and "possible"
        """
        f_grade = float(0)
        if possible != 0:
            f_grade = float(earned) / float(possible)
        return f_grade


    def get_chapter_tuple(self, chapter):
        """
            returns one chapter tuple, with an array of sections.
        """

        sections = []
        for section in chapter['sections']:
            sections.append(
                self.get_section_tuple(chapter, section)
            )

        return (
                    chapter['url_name'],
                    {
                    'chapter_url': self.course_url + chapter['url_name'],
                    'chapter_display_name': chapter['display_name'],
                    'chapter_sections': sections,
                    }
                )

    def get_section_tuple(self, chapter, section):
        """
            returns a tuple dictionary of grade data for one subsection of a chapter.

            * note: subsections are identifyable as "Sections" in the LMS UI.
        """
        grades_factory = SubsectionGradeFactory(student=self.grade_user, course=None, course_structure=None, course_data=self.course_data)
        subsection_grades = grades_factory.create(subsection=section, read_only=True)
        problems = []
        for problem_key_BlockUsageLocator, problem_ProblemScore in subsection_grades.problem_scores.items():
            problems.append(
                self.get_problem_tuple(
                    problem_key_BlockUsageLocator,
                    problem_ProblemScore
                ))

        return (
            section.url_name,
            {
            'section_url': self.course_url + chapter['url_name'] + '/' + section.url_name,
            'section_location': str(section.location),
            'section_display_name': section.display_name,
            'section_earned': section.all_total.earned,
            'section_possible': section.all_total.possible,
            'section_due_date': None,
            'section_completed_date': None,
            'section_attempted': None,
            'section_problems': problems,
            'section_grade_percentage':  self._calc_grade_percentage(
                                    section.all_total.earned,
                                    section.all_total.possible
                                    )

            }
                )

    def get_problem_tuple(self, problem_key_BlockUsageLocator, problem_ProblemScore):
        """
            returns an array of tuples of the individual problem grade results from a subsection of a chapter.

            * note: subsections are identifyable as "Sections" in the LMS UI.
        """
        return (
                str(problem_key_BlockUsageLocator),
                {
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
                )



class CourseGradeView(AbstractGradesView):

    def get(self, request, course_id=None):
        super(CourseGradeView, self).get(request, course_id, chapter_id=None, section_id=None)

        chapters = []
        for chapter in self.course_grade.chapter_grades.itervalues():
            chapters.append(self.get_chapter_tuple(chapter))

        return Response({
                        'username': self.grade_user.username,
                        'course_url': self.course_url,
                        'course_id': self.course_id,
                        'chapters': chapters
                        })

class ChapterGradeView(AbstractGradesView):
    def get(self, request, course_id=None, chapter_id=None):
        log.info('ChapterGradeView: course_id={course_id}, chapter_id={chapter_id}'.format(
            course_id=course_id,
            chapter_id=chapter_id
        ))
        super(ChapterGradeView, self).get(request, course_id, chapter_id, section_id=None)

        return Response(self.test_response(course_id=course_id, chapter_id=chapter_id))


class SectionGradeView(AbstractGradesView):
    def get(self, request, course_id=None, chapter_id=None, section_id=None):
        log.info('ChapterGradeView: course_id={course_id}, chapter_id={chapter_id}, section_id={section_id}'.format(
            course_id=course_id,
            chapter_id=chapter_id,
            section_id=section_id
        ))
        super(SectionGradeView, self).get(request, course_id, chapter_id, section_id)

        #o = self.course_grade.problem_scores()
        #log.info('SubsectionGradesView - retval: {}'.format(o))
        return Response(self.test_response())
