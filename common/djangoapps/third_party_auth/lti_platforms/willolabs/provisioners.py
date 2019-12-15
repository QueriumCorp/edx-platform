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
        queries the coursecache for information about the Rover course corresponding to context_id
        if found, then checks for and if necesary, enrolls the student in the course.



    example source: ./sample_data/tpa_lti_params.json
"""
from __future__ import absolute_import
#from django.contrib.auth.decorators import login_required
#from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.management.base import CommandError
from student.models import is_faculty, CourseEnrollment

from .models import LTIWilloLabsExternalCourse
from .exceptions import LTIBusinessRuleError
from .coursecache import LTIWilloSession
from .utils import is_willo_lti, is_valid_course_id

#from cms.djangoapps.contentstore.views.course import (
#    get_courses_accessible_to_user, 
#    _process_courses_list
#    )

import logging
log = logging.getLogger(__name__)


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
        willo_session   - course / enrollments cache

    methods
    -----------
        check_enrollment()
    """
    def __init__(self, user, lti_params, course_id=None):
        log.info('CourseProvisioner - __init__()')

        # local cached instance variables
        self._lti_params  = None
        self._course_id = None
        self._user = None
        self.is_faculty = False

        self._enrollments = None
        self._willo_session = None

        # constructor intializations ...
        # ----------------------------------------------------
        self.lti_params = lti_params        # originates from the http response body from LTI auth
        self.user = user
        self.course_id = course_id

    def check_enrollment(self):
        """
        For students.

        Verify that the student is enrolled in the Rover course corresponding to the context_id
        in lti_params. If not, then automatically enroll the student in the course.
        """
        log.info('CourseProvisioner - check_enrollment()')

        # if the user is not a student (ie is_faculty == True ) 
        # then we don't need to be here.
        if self.is_faculty or \
            self.course_id is None or \
            CourseEnrollment.is_enrolled(self.user, self.course_id):
            return False 

        # Student is not yet enrolled in the Rover course corresponding to the
        # context_id in their lti_params. So, lets get them enrolled!
        CourseEnrollment.enroll(self.user, self.course_id)
        self.willo_session.register_enrollment()

        return True

    @property
    def lti_params(self):
        """
        json object of LTI parameters passed from the external system
        connecting to Rover via LTI
        """
        return self._lti_params


    @lti_params.setter
    def lti_params(self, value):
        # ensure that this object is being instantiated with data that originated
        # from an LTI authentication from Willo Labs.
        if not is_willo_lti(value):
            raise LTIBusinessRuleError("Tried to instantiate Willo Labs CourseProvisioner with lti_params " \
                "that did not originate from Willo Labs: '%s'." % value)

        self._lti_params = value
        self.context_id = lti_params.get('context_id')
        self._willo_session = None


    @property
    def user(self):
        """
        Rover django user object
        """
        return self._user

    @user.setter
    def user(self, value):
        self._user = value

        # initialize properties that depend on user
        self.is_faculty = is_faculty(self.user)

        # clearn enrollments and the willo_session cache.
        self._enrollments = None
        self._willo_session = None

    
    @property
    def enrollments(self):
        """
        a list of active Rover courses which the user is currently enrolled.
        """
        if self._enrollments is not None:
            return self._enrollments 

        self._enrollments = CourseEnrollment.enrollments_for_user(self.user)
        return self._enrollments

    @property
    def course_id(self):
        """
        We accumulate persisted intelligence about which course_id in Rover to map context_id
        values by looking for cases where students are enrolled in exactly course in Rover.
        """
        if self._course_id is not None:
            return self._course_id 

        # first we'll look in the persisted Willo Labs LTI course enrollments table to see if 
        # a record exists for this user.
        try:
            self.course_id = self.willo_session.course_enrollment.course_id
            if self._course_id is not None:
                return self._course_id
        except:
            pass

        # if no record exists then we'll next look at this user's active Rover enrollments
        # and we'll potentially pull a course_id if there's exactly one active course for the
        # student.
        if len(self.enrollments) == 1:
            self.course_id = self.enrollments[0].course_id
            return self._course_id

        # we struck out. didn't find a course_id from any of our possible sources
        return None

    @course_id.setter
    def course_id(self, value):
        """
        Alternatively, we could simply set the course_id corresponding to this instances
        context_id, and in this case we only need to validate the course_id passed.
        """
        if value is None:
            self._course_id = None 
            self._willo_session = None
            return 
            
        if not is_valid_course_id(value):
            raise InvalidKeyError("Invalid course_key: '%s'." % value)

        self._course_id = course_key
        self.check_enrollment()

    @property
    def willow_session(self):
        """
        Cache manager for Willo Lab external system cached objects: 
            course      -> maps context_id to course_id
            enrollments -> maps user + course_id to lti_params values
            grades      -> maps user assignment grades to be exported to external system
        """
        # Try to return a cached instance of a LTIWilloSession object
        if self._willo_session is not None:
            return self._willo_session

        # otherwise try to instantiate a new Willow Session
        self._willo_session = LTIWilloSession(
            lti_params=self.lti_params, 
            user=self.user, 
            context_id=self.context_id, 
            course_id=self._course_id
            )
        return self._willo_session
