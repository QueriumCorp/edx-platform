# -*- coding: utf-8 -*-
"""LTI authentications include a JSON paramater in the body response with the key "tpa_lti_params"
which contains the value "context_id", that uniquely identifies the course from the host LMS which the student's
session originated.

1. The LTI consumer is not assumed to have any knowledge of the courseware available on Rover, which presents a
conundrum with respect to establishing a map of context_id's to Rover's corresponding course_id's. The only
real-world independent connection between a context_id and a course_id is the instructor teaching the course.
Therefore, when this instructor authenticates via LTI we can poll for the instructor's course(s) in Rover and
then draw some logical conclusions about what do about mapping the instructor's context_id to a course_id in Rover.

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

from student.models import is_faculty, CourseEnrollment
from opaque_keys.edx.keys import CourseKey

from .exceptions import LTIBusinessRuleError
from .cache import LTISession
from .lti_params import LTIParams, get_cached_course_id


User = get_user_model()
log = logging.getLogger(__name__)
DEBUG = True


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

        self.lti_params = lti_params         # originates from the http response body from LTI auth
        self.user = user
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

        # if we have a course_id for the user and 
        if not CourseEnrollment.is_enrolled(self.user, self.course_id):
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
    def get_lti_params(self):
        """
        json object of LTI parameters passed from the external system
        connecting to Rover via LTI
        """
        return self._lti_params


    def set_lti_params(self, value):
        """ensure that this object is being instantiated with data that originated
        from an LTI authentication from Willo Labs.
        
        Arguments:
            value {dict or LTIParams}
        
        Raises:
            LTIBusinessRuleError
        """
        if value is not None:
            if isinstance(value, LTIParams):
                if value == self._lti_params:
                    return
                self._lti_params = value
            else:
                if isinstance(value, dict):
                    if self._lti_params is not None and value == self._lti_params.dictionary:
                        return
                    new_params = LTIParams(value)
                    if new_params.is_valid:
                        self._lti_params = new_params
                    else:
                        raise LTIBusinessRuleError('CourseProvisioner.set_lti_params() - received invalid lti_params.')
        else:
            self._lti_params = None

        self.init()
        self._context_id = self._lti_params.context_id

    def get_context_id(self):
        """read-only context_id
        
        Returns:
            [string]
        """
        return self._context_id

    def set_context_id(self, value):
        """read-only context_id
        
        Arguments:
            value {any}
        
        Raises:
            LTIBusinessRuleError: raises an exception if called
        """
        raise LTIBusinessRuleError("CourseProvisioner.set_context_id() context_id is a read-only field.")

    def get_user(self):
        """Rover django user object"""
        return self._user

    def set_user(self, value):
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
            
        self._user = value

        # initialize properties that depend on user
        self.is_faculty = is_faculty(self.user)

        # clearn enrollments and the session cache.
        self._enrollments = None
        self._session = None

    
    def get_course_id(self):
        """Lazy-reader implementation. Try to find course_id from the
        student's enrollment information; but only if the student is currently
        enrolled in exactly 1 course. Otherwise look for the course in the LTI cache
        using the LTI context_id.
        
        Returns:
            [course_id] -- a string representation of a CourseKey
        """
        if self._course_id is not None:
            return self._course_id 

        if DEBUG: log.info('CourseProvisioner.get_course_id() -- trying to self-initialize...')

        enrollments = self.enrollments
        if enrollments is not None:
            if len(enrollments) == 1:
                if DEBUG: log.info('CourseProvisioner.get_course_id() -- found a course_id from self.enrollments')
                self._course_id = enrollments[0].course_id
                return self._course_id
            else:
                if DEBUG: log.info('CourseProvisioner.get_course_id() -- student is enrolled in multiple courses, so looking in the LTI cache.')
                self._course_id = get_cached_course_id(context_id=self.context_id)

        # we struck out. didn't find a course_id from any of our possible sources
        return None

    def set_course_id(self, value):
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

        if isinstance(value, CourseKey):
            self._course_id = value
        else:
            if isinstance(value, str):
                self._course_id = CourseKey.from_string(value)
            else:
                raise LTIBusinessRuleError("Course_key provided is not a valid object type. Must be either CourseKey or String.")

        self._session = None
        self.check_enrollment()

    def get_enrollments(self):
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

    def set_enrollments(self, value):
        raise LTIBusinessRuleError("CourseProvisioner.set_enrollments(). - enrollments is a read-only property.")

    def get_session(self):
        """Cache manager for Willo Lab LTI cache.
        
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
            course_id = self._course_id
            )
        return self._session

    def set_session(self, value):
        """Make session a read-only property
        
        Arguments:
            value {any}
        
        Raises:
            LTIBusinessRuleError: raises exception if called.
        """
        raise LTIBusinessRuleError("CourseProvisioner.set_session() - session is a read-only property.")

    lti_params = property(get_lti_params, set_lti_params)
    context_id = property(get_context_id, set_context_id)
    user = property(get_user, set_user)
    course_id = property(get_course_id, set_course_id)
    enrollments = property(get_enrollments, set_enrollments)
    session = property(get_session, set_session)
