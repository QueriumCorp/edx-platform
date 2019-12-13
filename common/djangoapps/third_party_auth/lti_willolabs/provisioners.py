"""
    mcdaniel nov-2019

    Description:
    =============
    LTI authentications include a JSON paramater in the body response with the key "tpi_lti_params"
    which contains the value "context_id", that uniquely identifies the course from the host LMS which the student's
    session originated.

    1. The LTI consumer is not assumed to have any knowledge of the courseware available on Rover, which presents a
    conundrum with respect to establishing a map of context_id's to Rover's corresponding course_id's. The only
    real-world independent connection between a context_id and a course_id is the instructor teaching the course.
    Therefore, when this instructor authenticates via LTI we can poll for the instructor's course(s) in Rover and
    then draw some logical conclusions about what do about mapping the instructor's context_id to a course_id in Rover.

    2. Moreover, students authenticating via LTI will need to be automatically enrolled in the Rover course
    corresponding to the context_id contained in the tpi_lti_params dictionary of their authentication http
    response body.

    We extend LTI authentication to form a relationship between the LTI consumer (the host LMS) and
    the LTI provider (us, a course hosted on this Rover platform).

    this module provides methods to administer these relationships:

    create()
        in cases where the LTI user is "faculty_confirmed" and the "context_id" they've provided
        has not yet been persisted on this Rover platform.

    find()
        returns the course_id related to a context_id. this is a 1:1 relationship.


    example source: ./sample_data/tpa_lti_params.json
"""
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from common.djangoapps.third_party_auth.lti_willolabs.models import LTIContextCourse
from common.djangoapps.third_party_auth.lti_willolabs.exceptions import LTIBusinessRuleError

from cms.djangoapps.contenstore.views.course import get_courses_accessible_to_user, _process_courses_list
from common.djangoapps.student.models import is_faculty, CourseEnrollment

from django.http import HttpRequest
from django.conf import settings

import logging
log = logging.getLogger(__name__)


class LTIProvisioningTools(Object):

    def __init__(self, strategy, lti_params):
        log.info('LTIProvisioningTools - __init__()')
        # stuff that seems important...
        # ----------------------------------------------------
        self.stragegy = strategy            # this originates from BaseAuth
        self.request = strategy.request
        self.lti_params = lti_params        # originates from the http response body from LTI auth

        # stuff that really is important ...
        # ----------------------------------------------------
        self.user = strategy.request.user
        self.context_id = getattr(lti_params, 'context_id', None)
        self.roles = getattr(lti_params, 'roles', '')
        self.course_id = None
        self.is_faculty = is_faculty(self.user)

        # cached local values of class properties....
        # ----------------------------------------------------
        self._instructor_courses = None

        # local cached instance of LTIContextCourse
        self._context_course = None

        # local cached instance of the student course enrollment for the Rover
        # course corresponding to the context_id in the lti_params of their
        # authentication.
        self._enrollment = None

    def check_enrollment(self):
        """
        For students.

        Verify that the student is enrolled in the Rover course corresponding to the context_id
        in lti_params. If not, then automatically enroll the student in the course.
        """
        log.info('LTIProvisioningTools - check_enrollment()')

        # if the user is faculty (ie the user is not a student) then we don't
        # need to be here.
        if self.is_faculty:
            return

        if not self.course_id:
            log.error('LTIProvisioningTools.check_enrollment() - Student {username} context_id {context_id} is not mapped to a Rover course.'.format(
                context_id=self.context_id,
                username=self.user.username
            ))
            raise LTIBusinessRuleError("Student context_id is not mapped to a Rover course.")

        # This is our expected (ie hoped-for) case.
        return self.enrollment if self.enrollment is not none

        # Student is not yet enrolled in the Rover course corresponding to the
        # context_id in their lti_params. So, lets get them enrolled!
        self.enrollment = CourseEnrollment.enroll(self.user, self.course_id)
        return self.enrollment

    def check_context_link(self):
        """
        For instructors.

        Look for a relationship between the context_id in the lti_params and a course_id
        on this Rover instance. If we don't find one, then try to create one.

        """
        log.info('LTIProvisioningTools - check_context_link()')
        # case 1: the current user is not an instructor, so don't do anything.
        return None if not self.is_faculty

        # case 2: verify that the context_id is really missing.
        # if a context_course map record already exists then there's nothing
        # more to do.
        #
        # also check other cases where there's nothing to do: the instructor has
        # no Rover courses.
        return if self.context_course
        return None if not self.instructor_courses
        return None if self.instructor_courses.count == 0

        # case 3: there's only one course, so create the 1:1 relationship and exit
        if self.instructor_courses.count == 1:
            # if there is exactly 1 course then we'll assume that this is the
            # Rover course that corresponds with the context_id provided in the
            # insructor's LTI params.
            course = self.instructor_courses[0]
            self.course_id = unicode(course.location.course_key)
            self.save()
            return None

        #case 4: there are multiple courses, so put up a page with a pick list
        #        so that the user can choose which course to associate with this
        #        LTI integration.
        #
        # The instructor has multiple courses saved on Rover, so we don't have any means of
        # automatically determining which of these courses should be related to
        # the context_id from lti_params
        for course in self.instructor_courses:
            # perform some magic
            log.info('LTIProvisioningTools check_context_link() - multiple courses encountered for this instructor.')

        return None

    def is_valid_course_id(self, course_id):
        log.info('LTIProvisioningTools - is_valid_course_id()')

        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            # malformed course key
            pass
            return False

        if not CourseOverview.get_from_id(course_key):
            # no course with this course key
            return False

        return True

    def save(self):
        self._context_course = LTIContextCourse(user=self.user, context_id=context_id, course_id=course_id)
        self._context_course.save()

    @property
    def enrollment(self):
        log.info('LTIProvisioningTools - enrollment() get')
        return self._enrollment if self._enrollment is not None

        if CourseEnrollment.is_enrolled(self.user, self.course_id):
            self._enrollment = CourseEnrollment.get_enrollment(self.user, self.course_id)
            return self._enrollment
        else:
            return None

    @enrollment.setter
    def enrollment(self, enrollment):
        log.info('LTIProvisioningTools - enrollment() set')
        self._enrollment = enrollment
        return None

    @property
    def context_course(self):
        log.info('LTIProvisioningTools - context_course() get')
        if self._context_course:
            return self._context_course

        self._context_course  = LTIContextCourse(context_id=self.context_id)

        return self._context_course

    @property
    def course_id(self):
        log.info('LTIProvisioningTools - course_id() get')
        if self.context_course:
            return self.context_course.course_id

        return None

    @course_id.setter
    def course_id(self, course_id):
        log.info('LTIProvisioningTools - course_id() set')
        if self.context_course and self.context_course.course_id == course_id:
            # nothing to do.
            return None

        if not self.is_valid_course_id(course_id):
            # Raise Hell
            return None

        self._course_id = course_id


    @property
    def instructor_courses(self):
        log.info('LTIProvisioningTools - instructor_courses() set')
        if not self.is_faculty:
            self._instructor_courses = []

        if not self._instructor_courses:
            # this probablyt doesn't work bc the settings comes from cms.
            split_archived = settings.FEATURES.get(u'ENABLE_SEPARATE_ARCHIVED_COURSES', True)

            courses, in_process_course_actions = get_courses_accessible_to_user(request, org=None)
            active_courses, archived_courses = _process_courses_list(courses_iter, in_process_course_actions, split_archived)

            self._instructor_courses = active_courses

        return self._instructor_courses
