# -*- coding: utf-8 -*-
"""LTI authentications include a JSON paramater in the body response with the key "tpa_lti_params"
which contains the value "context_id", that uniquely identifies the course from the host LMS which the student's
session originated.

1. The LTI consumer is not assumed to have any knowledge of the courseware available on Rover, which presents a
conundrum with respect to establishing a map of context_id's to Rover's corresponding course_id's. The LTI
course relationship to Rover is weak, but can be established by any of the following:
    a.) the course_id query parameter that MIGHT BE embedded in tpa_params.custom_tpa_next URL
    b.) a LTI cache entry, if it exists
    c.) an analysis of the student's enrollment data in Rover, if it exists.

2. Moreover, students authenticating via LTI will need to be automatically enrolled in the Rover course
corresponding to the context_id contained in the tpa_lti_params dictionary of their authentication http
response body.

We extend LTI authentication to form a relationship between the LTI consumer (the host LMS) and
the LTI provider (us, a course hosted on this Rover platform).

this module provides methods to administer these relationships:

check_enrollment()
    queries the cache for information about the Rover course corresponding to context_id
    if found, then checks for and if necessary, enrolls the student in the course.

"""
from __future__ import absolute_import
import logging

from django.contrib.auth import get_user_model
from django.conf import settings

from student.models import is_faculty, CourseEnrollment
from opaque_keys.edx.keys import CourseKey

from .exceptions import LTIBusinessRuleError
from .cache import LTISession
from .lti_params import LTIParams


User = get_user_model()
log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG


class CourseProvisioner(object):
    """Instantiated during LTI authentication. Try to enroll user in a Rover course
    based on information received in the lti_params object from LTI authentication http response.

    Arguments:
        object {object} -- this is required to implement properties.

    Raises:
        LTIBusinessRuleError

    """
    def __init__(self, user, lti_params, course_id=None):
        """Bootstrap the class initialization by validating and setting lti_params
        and then using its contents to set other properties in the class.

        Arguments:
            user {User} -- CourseProvisioner is intended to be called from third_party_auth.pipeline
            at a point where authentication has completed and the User object has been
            assigned.

            lti_params {dict} -- received during LTI authentication.
            see https://readthedocs.roverbyopenstax.org/en/latest/how_to/lti.html#tpa-lti-params

        Keyword Arguments:
            course_id {string} - (default: {None}). course_id can usually be retrieved from the LTI cache
            using context_id. Alternatively, we can also check the user's enrollment data.
        """
        self.init()

        log.info('CourseProvisioner.__init__() initializing. user: {user}, '\
            ' course_id: {course_id}'.format(
                user=user,
                course_id=course_id
            ))

        # Note: lti_params originates from the http response body from LTI auth.
        # the lti_params setter also sets self.context_id and self.course_id
        self.lti_params = lti_params
        self.user = user
        if course_id:
            self.course_id = course_id

        log.info('CourseProvisioner.__init__() initialized. user: {user}, context_id: {context_id}, '\
            ' course_id: {course_id}'.format(
                user=self.user,
                context_id=self.context_id,
                course_id=self.course_id
            ))

    def init(self):
        """Clear the class, and ensure that all of our local class variables exist
        by setting everything to None.
        """
        if DEBUG: log.info('CourseProvisioner.init()')

        self._lti_params  = None
        self._context_id = None
        self._course_id = None
        self._user = None
        self.is_faculty = False

        self._enrollments = None
        self._session = None

    def check_enrollment(self):
        """Verify that the student is enrolled in the Rover course corresponding to the context_id
        in lti_params. If not, then automatically enroll the student in the course.

        Returns:
            [Boolean] -- returns True if the student is (or just became) enrolled
            in course_id
        """
        if DEBUG: log.info('CourseProvisioner.check_enrollment()')
        if self.course_id is None:
            return False

        if DEBUG: log.info('CourseProvisioner.check_enrollment() course_id is set. continuing.')

        try:
            log.info('check_enrollment - course_id: {course_id} {t}'.format(
                course_id=course_id
                t=type(self.course_id)
            ))
            if CourseEnrollment.is_enrolled(self.user, self.course_id): return True
        except Exception as err:
            log.info('CourseProvisioner.check_enrollment() run-time error checking enrollment status of '\
                ' user: {user}, context_id: {context_id}, '\
                ' course_id: {course_id}, '\
                ' error: {err}'.format(
                    user=self.user,
                    context_id=self.context_id,
                    course_id=self.course_id,
                    err=err
                ))
            return False

        # user is not yet enrolled, so lets take care of that now...
        retval = CourseEnrollment.enroll(self.user, self.course_id)
        if not retval:
            log.error('CourseProvisioner.check_enrollment() auto-enrollment failed for '\
                ' user: {user}, context_id: {context_id}, '\
                ' course_id: {course_id}'.format(
                    user=self.user,
                    context_id=self.context_id,
                    course_id=self.course_id
                ))
            return False

        log.info('CourseProvisioner.check_enrollment() automatically enrolled'\
            ' user: {user}, context_id: {context_id}, '\
            ' course_id: {course_id}'.format(
                user=self.user,
                context_id=self.context_id,
                course_id=self.course_id
            ))

        # cache our mappings between
        #   Rover course_id and the LTI context_id
        #   Rover username and LTI user_id
        self.session.register_enrollment()

        return True

    #------------------------------------------------------------------------------------------
    #
    # Property setters & getters
    #
    #------------------------------------------------------------------------------------------
    @property
    def lti_params(self):
        """
        json object of LTI parameters passed from the external system
        connecting to Rover via LTI
        """
        return self._lti_params

    @lti_params.setter
    def lti_params(self, value):
        """ensure that this object is being instantiated with data that originated
        from an LTI authentication.

        Arguments:
            value {dict or LTIParams}

        Raises:
            LTIBusinessRuleError
        """
        if DEBUG: log.info('CourseProvisioner.lti_params() - setter: {value}'.format(
            value=value
        ))
        self.init()
        if value is not None:
            if isinstance(value, dict):
                value = LTIParams(value)

            if not isinstance(value, LTIParams):
                raise LTIBusinessRuleError('CourseProvisioner.lti_params() - expected LTIParams but received'\
                    ' object of type {dtype}.'.format(
                    dtype=type(value)
                ))

            if not value.is_valid:
                raise LTIBusinessRuleError('CourseProvisioner.lti_params() - received invalid lti_params.')
            if not value.is_willolabs:
                raise LTIBusinessRuleError('CourseProvisioner.lti_params() - lti_params did not originate from Willo Labs.')

            self._lti_params = value
        else:
            self._lti_params = None

        # if we're initialized then pre-populate anything that can
        # originate from the lti_params dictionary. note that
        # we we're not calling the setters in order to avoid
        # potential thrashing.
        if self.lti_params:
            self._context_id = self._lti_params.context_id
            self._course_id = self._lti_params.course_id

    @property
    def context_id(self):
        """read-only context_id

        Returns:
            [string]
        """
        return self._context_id

    @context_id.setter
    def context_id(self, value):
        """read-only context_id

        Arguments:
            value {any}

        Raises:
            LTIBusinessRuleError: raises an exception if called
        """
        raise LTIBusinessRuleError("CourseProvisioner.set_context_id() context_id is a read-only field.")

    @property
    def user(self):
        """Rover django user object"""
        return self._user

    @user.setter
    def user(self, value):
        """Verify that value passed is an instace of the User class. The set the value.

        Arguments:
            value {User} -- Modified Django User class from common.student.models

        Raises:
            LTIBusinessRuleError: raises an exception on type mismatch.
        """
        if DEBUG: log.info('CourseProvisioner.set_user()')

        if value == self._user:
            return

        if value is not None and not isinstance(value, User):
            raise LTIBusinessRuleError('CourseProvisioner.set_user() was expecting a User object but received an object of type {dtype}'.format(
                dtype=type(value)
            ))

        # if user is not yet logged in then we'll receive an Anonymous user object type
        # that is not iterable and has no enrollments.
        if value.is_anonymous:
            log.info('CourseProvisioner.user.setter() - received an anonymous user object.')

        self._user = value

        # initialize properties that depend on user
        self.is_faculty = is_faculty(self.user)

        # clear enrollments and the session cache.
        self._enrollments = None
        self._session = None

    @property
    def course_id(self):
        """Lazy-reader implementation. Try to find course_id from the
        student's enrollment information; but only if the student is currently
        enrolled in exactly 1 course. Otherwise look for the course in the LTI cache
        using the LTI context_id.

        Returns:
            [course_id] -- a string representation of a CourseKey
        """
        if self._course_id is not None:
            return self._course_id

        # NOTE: in a normal use case none of these initialization methods will be utilized.
        # course_id is set in __init__() from lti_params. thus, if we find ourselves here
        # then course_id has somehow been set to null since class initialization.
        if DEBUG: log.info('CourseProvisioner.get_course_id() -- trying to self-initialize...')

        # 1.) try to pull a course_id from tpi_params
        if DEBUG: log.info('CourseProvisioner.get_course_id() -- looking in lti_params.custom_tpa_next: {custom_tpa_next}'.format(
            custom_tpa_next=self.lti_params.custom_tpa_next
            ))
        self._course_id = self.lti_params.course_id
        if self._course_id:
            return self._course_id


        # 2.) try to pull a cached course record based on the context_id from the lti_params.
        if DEBUG: log.info('CourseProvisioner.get_course_id() -- looking in the LTI cache. context_id: {context_id}'.format(
            context_id=self.context_id
            ))
        self._course_id = self.lti_params.cached_course_id()
        if self._course_id:
            return self._course_id


        # 3.) this is a fallback option: check student's enrollment data
        enrollments = self.enrollments
        if enrollments is not None:
            if len(enrollments) == 1:
                # student is enrolled in exactly one course (the most common case).
                # return the course_id for this course.
                if DEBUG: log.info('CourseProvisioner.get_course_id() -- found a course_id from self.enrollments')
                self._course_id = enrollments[0].course_id
                return self._course_id
            else:
                if len(enrollments) == 0:
                    if DEBUG: log.error('CourseProvisioner.get_course_id() -- internal error. self.enrollments reports zero enrollments')

                if len(enrollments) > 1:
                    if DEBUG: log.info('CourseProvisioner.get_course_id() -- student is enrolled in multiple courses. no way to disambiguate.')

        # we struck out. didn't find a course_id from any of our possible sources
        return self._course_id

    @course_id.setter
    def course_id(self, value):
        """Alternatively, we can simply set the course_id corresponding to this instances
        context_id, and in this case we only need to validate the course_id passed. Also
        set the LTISession object to None.

        Arguments:
            value {string} -- a string representation of a CourseKey

        Raises:
            LTIBusinessRuleError: raises exception if course_id is not a valid CourseKey.
        """
        if DEBUG: log.info('CourseProvisioner.set_course_id()')
        if value is None:
            self._course_id = None
            self._session = None
            return

        if value == self._course_id:
            return

        if isinstance(value, str):
            value = CourseKey.from_string(value)

        if not isinstance(value, CourseKey):
            raise LTIBusinessRuleError("Course_key provided is not a valid object type. Must be either CourseKey or String.")

        # ensure agreement between data inside of lti_params vs whatever
        # we received.
        lti_params_course_id = self.lti_params.course_id
        if lti_params_course_id and lti_params_course_id != value.course_id:
            raise LTIBusinessRuleError('CourseProvisioner.__init__() - internal error: course_id provided does not equal course_id found in lti_params.')

        self._course_id = value
        self._session = None
        return None

    @property
    def enrollments(self):
        """a list of active Rover courses which the user is currently enrolled.
        Uses common.student.models.CourseEnrollment

        Returns:
            [list] -- List of courses in which the student is currently enrolled.
        """
        if self._enrollments is not None:
            return self._enrollments

        if DEBUG: log.info('CourseProvisioner.get_enrollments() -- trying to self-initialize...')

        # if user is not yet logged in then we'll receive an Anonymous user object type
        # that is not iterable and has no enrollments.
        if self.user.is_anonymous:
            return None

        try:
            self._enrollments = CourseEnrollment.enrollments_for_user(self.user)
            if DEBUG: log.info('CourseProvisioner.get_enrollments() -- returning Open edX CourseEnrollment.enrollments_for_user()')
            return self._enrollments
        except Exception as e:
            log.error('CourseProvisioner.get_enrollments() -- could not get enrollments. Encountered the following error: {err}'.format(
                err=e.description
            ))
            pass

        return None

    @enrollments.setter
    def enrollments(self, value):
        raise LTIBusinessRuleError("CourseProvisioner.set_enrollments(). - enrollments is a read-only property.")

    @property
    def session(self):
        """Cache manager for LTI Grade Sync cache.

        Raises:
            LTIBusinessRuleError: raises exception if lti_params, user or course_id is None.

        Returns:
            [LTISession]
        """

        if self._session is not None:
            return self._session

        if DEBUG: log.info('CourseProvisioner.get_session() -- creating a new LTISession')


        if not self.lti_params:
            raise LTIBusinessRuleError('CourseProvisioner.get_session() - tried to instantiate LTISession but lti_params is not set.')

        if not self.user:
            raise LTIBusinessRuleError('CourseProvisioner.get_session() - tried to instantiate LTISession but user is not set.')

        if not self.course_id:
            raise LTIBusinessRuleError('CourseProvisioner.get_session() - tried to instantiate LTISession but course_id is not set.')

        self._session = LTISession(
            lti_params = self.lti_params.dictionary,
            user = self.user,
            course_id = self.course_id
            )
        return self._session

    @session.setter
    def session(self, value):
        """Make session a read-only property

        Arguments:
            value {any}

        Raises:
            LTIBusinessRuleError: raises exception if called.
        """
        raise LTIBusinessRuleError("CourseProvisioner.set_session() - session is a read-only property.")
