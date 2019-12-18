# -*- coding: utf-8 -*-
"""
    mcdaniel nov-2019

    Description:
    =============
    LTI authentications include a JSON paramater in the body response with the key "tpa_lti_params"
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
        if found, then checks for and if necesary, enrolls the student in the course.



    example source: ./sample_data/tpa_lti_params.json
"""
from __future__ import absolute_import
#from django.contrib.auth.decorators import login_required
#from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.management.base import CommandError
from student.models import is_faculty, CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError

from .models import LTIExternalCourse
from .exceptions import LTIBusinessRuleError
from .cache import LTISession
from .utils import is_willo_lti, is_valid_course_id

#from cms.djangoapps.contentstore.views.course import (
#    get_courses_accessible_to_user, 
#    _process_courses_list
#    )

import logging
log = logging.getLogger(__name__)

DEBUG = True

class CourseProvisioner():
    """
    Instantiated during LTI authentication. Try to enroll user in a Rover course
    based on information received in the lti_params object from LTI authentication http response.

    properties
    -----------
        lti_params      - orginating from external platform authenticating via LTI - Willo Labs
        user            - django user object
        course_id       - Open edX Opaque key course key
        is_faculty      - True if user is faculty_confirmed at openstax.org
        enrollments     - list of active courses for this user
        session         - course / enrollments cache

    methods
    -----------
        check_enrollment()
    """
    def __init__(self, user, lti_params, course_id=None):
        log.info('CourseProvisioner - __init__()')

        self.init()

        # constructor intializations ...
        # ----------------------------------------------------
        self.set_lti_params(lti_params)         # originates from the http response body from LTI auth
        self.set_user(user)
        self.set_course_id(course_id)

    def init(self):
        if DEBUG: log.info('CourseProvisioner - init()')
        # local cached instance variables
        self._lti_params  = None
        self._context_id = None
        self._course_id = None
        self._user = None
        self.is_faculty = False

        self._enrollments = None
        self._session = None

    def check_enrollment(self):
        """
        For students.

        Verify that the student is enrolled in the Rover course corresponding to the context_id
        in lti_params. If not, then automatically enroll the student in the course.
        """
        if DEBUG: log.info('CourseProvisioner - check_enrollment()')
        if self.course_id is None:
            return False

        if DEBUG: log.info('CourseProvisioner - check_enrollment() course_id is set. continuing.')

        # if we have a course_id for the user and 
        if not CourseEnrollment.is_enrolled(self.user, self.course_id):
            CourseEnrollment.enroll(self.user, self.course_id)

        # cache our mappings between 
        #   Rover course_id and the LTI context_id
        #   Rover username and LTI user_id
        self.get_session().register_enrollment()

        return True

    def get_lti_params(self):
        """
        json object of LTI parameters passed from the external system
        connecting to Rover via LTI
        """
        return self._lti_params


    def set_lti_params(self, value):
        # ensure that this object is being instantiated with data that originated
        # from an LTI authentication from Willo Labs.
        if not is_willo_lti(value):
            raise LTIBusinessRuleError("Tried to instantiate Willo Labs CourseProvisioner with lti_params " \
                "that did not originate from Willo Labs: '%s'." % value)

        self.init()
        self._lti_params = value
        self._context_id = value.get('context_id')

    def get_context_id(self):
        return self._context_id

    def set_context_id(self, value):
        raise LTIBusinessRuleError("context_id is a read-only field.")

    def get_user(self):
        """
        Rover django user object
        """
        return self._user

    def set_user(self, value):
        if DEBUG: log.info('set_user()')
        self._user = value

        # initialize properties that depend on user
        self.is_faculty = is_faculty(self.user)

        # clearn enrollments and the session cache.
        self._enrollments = None
        self._session = None

    
    def get_course_id(self):
        """
        We accumulate persisted intelligence about which course_id in Rover to map context_id
        values by looking for cases where students are enrolled in exactly course in Rover.
        """
        if self._course_id is not None:
            return self._course_id 

        if DEBUG: log.info('get_course_id() -- looking for a course_id')

        # first we'll look in the persisted Willo Labs LTI course enrollments table to see if 
        # a record exists for this user.
        try:
            self._course_id = self.get_session().course_enrollment.course_id
            if self._course_id is not None:
                return self._course_id
        except:
            pass

        # if no record exists then we'll next look at this user's active Rover enrollments
        # and we'll potentially pull a course_id if there's exactly one active course for the
        # student.
        enrollments = self.get_enrollments()
        if len(enrollments) == 1:
            self._course_id = enrollments[0].course_id
            return self._course_id

        # we struck out. didn't find a course_id from any of our possible sources
        return None

    def set_course_id(self, value):
        """
        Alternatively, we could simply set the course_id corresponding to this instances
        context_id, and in this case we only need to validate the course_id passed.
        """
        if DEBUG: log.info('set_course_id()')
        if value is None:
            self._course_id = None 
            self._session = None
            return 
        
        if isinstance(value, CourseKey):
            self._course_id = value
        else:
            if isinstance(value, str):
                self._course_id = CourseKey.from_string(value)
            else:
                raise LTIBusinessRuleError("Course_key provided is not a valid object type. Must be either CourseKey or String.")

        self.check_enrollment()

    def get_enrollments(self):
        """
        a list of active Rover courses which the user is currently enrolled.
        """
        if self._enrollments is not None:
            return self._enrollments 

        if DEBUG: log.info('get_enrollments() -- looking for a new value')

        self._enrollments = CourseEnrollment.enrollments_for_user(self.user)
        return self._enrollments

    def set_enrollments(self, value):
        raise LTIBusinessRuleError("enrollments is a read-only property.")

    def get_session(self):
        """
        Cache manager for Willo Lab external system cached objects: 
            course      -> maps context_id to course_id
            enrollments -> maps user + course_id to lti_params values
            grades      -> maps user assignment grades to be exported to external system
        """
        # Try to return a cached instance of a LTISession object
        if self._session is not None:
            return self._session

        if DEBUG: log.info('get_session() -- creating a new session')
        # otherwise try to instantiate a new Willow Session
        self._session = LTISession(
            lti_params = self.get_lti_params(), 
            user = self.get_user(), 
            course_id = self._course_id
            )
        return self._session

    def set_session(self, value):
        raise LTIBusinessRuleError("session is a read-only property.")

    lti_params = property(get_lti_params, set_lti_params)
    context_id = property(get_context_id, set_context_id)
    user = property(get_user, set_user)
    course_id = property(get_course_id, set_course_id)
    enrollments = property(get_enrollments, set_enrollments)
    session = property(get_session, set_session)

