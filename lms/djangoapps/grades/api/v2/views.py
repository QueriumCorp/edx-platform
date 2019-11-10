""" API v2 views. """
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

log = logging.getLogger(__name__)
USER_MODEL = get_user_model()

# mcdaniel nov-2019
# additional stuff that we need for V2
from django.contrib.auth.decorators import login_required
from lms.djangoapps.grades.course_grade import CourseGrade
from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.subsection_grade_factory import SubsectionGradeFactory
import json
from django.conf import settings

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

    # to be assign in get() but made available to the class
    course_id = None
    username = None
    user = None             # for the decorator
    grade_user = None
    course_key = None
    course_data = None
    course_grade = None
    course_url = None

    #@login_required
    def get(self, request, course_id=None):

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

        if course_id:
            self.course_id = course_id
        else:
            self.course_id = request.GET.get('course_id')

        if not self.course_id:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='course_id is required for this view.',
                error_code='missing_course_id'
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

        #log.info('AbstractGradesView - get() - course_data effective_structure: {}'.format(self.course_data.effective_structure))
        #log.info('AbstractGradesView - get() - course_data full_string: {}'.format(self.course_data.full_string()))
        #log.info('AbstractGradesView - get() - course_data location: {}'.format(self.course_data.location))

        return

    def test_response(self):
        return {
            'username': 'Tom Sawyer',
            'email': 'not yet invented',
            'course_id': 'No time for schooling.',
        }
    def _make_grade_response(self, user, course_key, course_grade):
        """
        Serialize a single grade to dict to use in Responses
        """
        return {
            'username': user.username,
            'email': user.email,
            'course_id': str(course_key),
            'passed': course_grade.passed,
            'percent': course_grade.percent,
            'letter_grade': course_grade.letter_grade,
        }


class CourseGradeView(AbstractGradesView):
    """
    **Use Case**
        * Get course grades of the current user, if enrolled in the course.
    **Example Request**
        GET /api/grades/v1/courses/{course_id}/?username={username}          - Get grades for specific user in course
        GET /api/grades/v1/courses/?course_id={course_id}&username={username}- Get grades for specific user in course
    **GET Parameters**
        A GET request may include the following parameters.
        * course_id: (required) A string representation of a Course ID.
        * username:  (required) A string representation of a user's username.
    **GET Response Values**
        If the request for information about the course grade
        is successful, an HTTP 200 "OK" response is returned.
        The HTTP 200 response has the following values.
        * username: A string representation of a user's username passed in the request.
        * email: A string representation of a user's email.
        * course_id: A string representation of a Course ID.
        * passed: Boolean representing whether the course has been
                  passed according to the course's grading policy.
        * percent: A float representing the overall grade for the course
        * letter_grade: A letter grade as defined in grading policy (e.g. 'A' 'B' 'C' for 6.002x) or None
    **Example GET Response**
        {
            "username": "fred",
            "email": "fred@example.com",
            "course_id": "course-v1:edX+DemoX+Demo_Course",
            "passed": true,
            "percent": 0.83,
            "letter_grade": "B",
        }
    """

    def get(self, request, course_id=None):
        super(CourseGradeView, self).get(request, course_id)
        """
        Gets a course progress status.
        Args:
            request (Request): Django request object.
            course_id (string): URI element specifying the course location.
                                Can also be passed as a GET parameter instead.
        Return:
            A JSON serialized representation of the requesting user's current grade status.
        """

        try:
            return Response(self._make_grade_response(self.grade_user, self.course_key, self.course_grade))
        except:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='An unhandled exception ocurred in CourseGradeView.get()',
                error_code='unhandled_exception'
            )


class SubsectionGradesView(AbstractGradesView):
    def get(self, request, course_id=None):
        # do some assignments and valiations...
        super(SubsectionGradesView, self).get(request, course_id)

        #o = self.course_grade.subsection_grades()
        #log.info('SubsectionGradesView - retval: {}'.format(o))

        return Response(self.test_response())

class ChapterGradesView(AbstractGradesView):

    def get(self, request, course_id=None):
        # do some assignments and valiations...
        super(ChapterGradesView, self).get(request, course_id)

        grades = []
        for chapter in self.course_grade.chapter_grades.itervalues():
            for subsection_grade in chapter['sections']:
                grades_factory = SubsectionGradeFactory(student=self.grade_user, course=None, course_structure=None, course_data=self.course_data)
                subsection_grades = grades_factory.create(subsection=subsection_grade, read_only=True)

                #log.info('subsection grades: {}'.format(
                #    subsection_grades.problem_scores
                #))

                problems = []
                for problem_key_BlockUsageLocator, problem_ProblemScore in subsection_grades.problem_scores.items():

                    problems.append(
                        (
                        str(problem_key_BlockUsageLocator),
                        {
                        'raw_earned': problem_ProblemScore.raw_earned,
                        'raw_possible': problem_ProblemScore.raw_possible,
                        'earned': problem_ProblemScore.earned,
                        'possible': problem_ProblemScore.possible,
                        'weight': problem_ProblemScore.weight
                        }
                        )
                    )

                grades.append(
                    {
                    'username': self.grade_user.username,
                    'url': self.course_url + chapter['url_name'] + '/' + subsection_grade.url_name,
                    'chapter_url': chapter['url_name'],
                    'subsection_url': subsection_grade.url_name,
                    'course_id': self.course_id,
                    'chapter_display_name': chapter['display_name'],
                    'subsection_display_name': subsection_grade.display_name,
                    'earned': subsection_grade.all_total.earned,
                    'possible': subsection_grade.all_total.possible,
                    'due_date': None,
                    'completed_date': None,
                    'attempted': None,
                    'location': str(subsection_grade.location),
                    'subsection_grades': problems
                    }
                )

        return Response(grades)

class ProblemGradeView(AbstractGradesView):
    def get(self, request, course_id=None):
        # do some assignments and valiations...
        super(ProblemGradeView, self).get(request, course_id)

        #o = self.course_grade.problem_scores()
        #log.info('SubsectionGradesView - retval: {}'.format(o))
        return Response(self.test_response())
