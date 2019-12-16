# -*- coding: utf-8 -*-
"""
Lawrence McDaniel
lpm0073@gmail.com
https://lawrencemcdaniel.com

Willo Labs LTI.

This module manages cached course and enrollment relationship data between Rover 
and External platforms like Canvas, Blackboard and Moodle.
"""
from __future__ import absolute_import
import logging
import json

from .models import (
    LTIExternalCourse,
    LTIExternalCourseEnrollment,
    LTIExternalCourseEnrollmentGrades
    )
from student.models import is_faculty, CourseEnrollment
from third_party_auth.lti_consumers.willolabs.utils import is_willo_lti, is_valid_course_id

log = logging.getLogger(__name__)

class LTISession:
    """
    mcdaniel dec-2019

    Used during LTI authentication from external platforms connecting to Rover via
    Willo Labs. Persists external course and enrollment data provided during LTI authentication
    in the oauth response body, in a json object named lti_params. Establishes the 
    relationships between external courses/users and the corresponding Rover courses/users.
    These relationships are required by Rover's Grade Sync, so that we can send 
    Grade Sync requests to the Willo Lab api.

    properties:
    -----------
        lti_params      - orginating from external platform authenticating via LTI - Willo Labs
        context_id      - uniquely identifies an external course registered on Willo Labs
        course_id       - Open edX Opaque key course key
        user            - django user object
        course                      - external course cache
        course_enrollment           - external course enrollments cache
        course_enrollment_grades    - external grade sync data cache

    methods:
    -----------
        register_course()
        register_enrollment()
        post_grades()
    """
    def __init__(self, lti_params, user=None, course_id=None):
        log.info('LTISession - __init__()')
        self.init()

        if lti_params is not None and course_id is not None:
            self.COMPLETE_MAPPING = True
        else:
            self.COMPLETE_MAPPING = False

        # class initializations
        self.lti_params = lti_params    # this needs to initialized first bc it resets all
                                        # other class properties.

        self.user = user                # Rover (django) user object
        
        self.course_id = course_id      # Rover (Open edX) course_id (aka Opaque Key)
                                        # this MUST be initialized after self.lti_params

    def init():
        self._context_id = None
        self._course = None
        self._course_enrollment = None
        self._course_enrollment_grades = None
        self._lti_params = None
        self._user = None
        self._course_id = None

    def register_course(self):
        """
        try to retrieve a cached course record for the context_id / course_id
        otherwise, create a new record for the cache.
        """

        # if __init__() received both lti_params and a course_id then we should 
        # check to verify that we are fully initialized before attempting to 
        # register the course.
        if self.COMPLETE_MAPPING and (self._course_id is None or self.lti_params is None):
            return None

        # another check against partial initialization, or corruption of the property values.
        # self.context_id is automatically initialized from self.lti_params. however,
        # the property value is editable and can be set to None.
        if self.context_id is None:
            return None

        log.info('LTISession - register_course()')
        course = LTIExternalCourse.objects.filter(context_id=self.context_id)
        if course is not None:
            # we didn't necesarily know the course_id at the time the record was created.
            # the course_id could materialize at any time, and if so then we'll 
            # need to persist the value.
            if course.course_id is None and self.course_id is not None:
                course.course_id = self.course_id
                course.save()
            else:
                # sneaky write to ensure integrity between context_id / course_id.
                #
                # Note: if for any reason there were descrepancy between course.course_id
                # and a not-null value of self.course_id, then we'll always assume
                # that course.course_id is the correct value.
                self._course_id = course.course_id

            return course 

        if self.lti_params is None or self.course_id is None:
            return None

        course.context_id = self.context_id
        course.course_id = self.course_id
        course.context_title = self.lti_params.get('context_title')
        course.context_label = self.lti_params.get('context_label')
        course.ext_wl_launch_key = self.lti_params.get('ext_wl_launch_key')
        course.ext_wl_launch_url = self.lti_params.get('ext_wl_launch_url')
        course.ext_wl_version = self.lti_params.get('ext_wl_version')
        course.ext_wl_outcome_service_url = self.lti_params.get('ext_wl_outcome_service_url')
        course.custom_canvas_api_domain = self.lti_params.get('custom_canvas_api_domain')
        course.custom_canvas_course_id = self.lti_params.get('custom_canvas_course_id')
        course.custom_canvas_course_startat = self.lti_params.get('custom_canvas_course_startat')
        course.tool_consumer_info_product_family_code = self.lti_params.get('tool_consumer_info_product_family_code')
        course.tool_consumer_info_version = self.lti_params.get('tool_consumer_info_version')
        course.tool_consumer_instance_contact_email = self.lti_params.get('tool_consumer_instance_contact_email')
        course.tool_consumer_instance_guid = self.lti_params.get('tool_consumer_instance_guid')
        course.tool_consumer_instance_name = self.lti_params.get('tool_consumer_instance_name')
        
        course.save()
        log.info('LTISession - register_course() saved new cache record.')
        return course

    def register_enrollment(self):
        """
        try to retreive a cached enrollment record for the context_id / user
        otherwise, create a new record for the cache.
        """
        log.info('LTISession - register_enrollment()')
        if self.user is None or self.context_id is None:
            return None

        # looked for a cached record for this user / context_id
        enrollment = LTIExternalCourseEnrollment.objects.filter(context_id=self.context_id, user=self.user)
        if enrollment is not None:
            # 1:1 relationship between context_id / course_id
            # if we have a cached enrollment record then we know that we also have the parent course
            # record, where the course_id is stored.
            self._course_id = self.course.course_id
            return enrollment

        if self.lti_params is None or \
            self.course is None or \
            self.course_id is None or \
            not CourseEnrollment.is_enrolled(self.user, self.course_id):
            return None

        enrollment.context_id = self.context_id
        enrollment.user = self.user
        enrollment.user_id = self.user_id

        enrollment.custom_canvas_user_id = self.lti_params.get('custom_canvas_user_id')
        enrollment.custom_canvas_user_login_id = self.lti_params.get('custom_canvas_user_login_id')
        enrollment.custom_canvas_person_timezone = self.lti_params.get('custom_canvas_person_timezone')
        enrollment.ext_roles = self.lti_params.get('ext_roles')
        enrollment.ext_wl_privacy_mode = self.lti_params.get('ext_wl_privacy_mode')
        enrollment.lis_person_contact_email_primary = self.lti_params.get('lis_person_contact_email_primary')
        enrollment.lis_person_name_family = self.lti_params.get('lis_person_name_family')
        enrollment.lis_person_name_full = self.lti_params.get('lis_person_name_full')
        enrollment.lis_person_name_given = self.lti_params.get('lis_person_name_given')

        enrollment.save()
        log.info('LTISession - register_enrollment() saved new cache record.')
        return enrollment

    def post_grades(self, usage_key, grades_dict):
        """
            usage_key: a subsection of a Rover course. corresponds to a homework assignment
            grades_dict: contains all fields from grades.models.PersistentSubsectionGrade
        """
        log.info('LTISession - post_grades()')
        if not self.course_enrollment:
            return None
        # null usage_key -- raiserror
        # null grades_dict -- raiserror

        # 'context_id', 'user', 'usage_key'
        grades = LTIExternalCourseEnrollmentGrades.objects.filter(
            context_id=self.context_id, 
            user=self.user,
            usage_key=usage_key
            )

        if not grades:
            grades.context_id = self.context_id
            grades.user = self.user
            grades.course_id = self.course_id
            grades.usage_key = usage_key

        grades.course_version = grades_dict.get('course_version')
        grades.earned_all = grades_dict.get('earned_all')
        grades.possible_all = grades_dict.get('possible_all')
        grades.earned_graded = grades_dict.get('earned_graded')
        grades.possible_graded = grades_dict.get('possible_graded')
        grades.first_attempted = grades_dict.get('first_attempted')
        grades.visible_blocks = grades_dict.get('visible_blocks')

        grades.save()
        log.info('LTISession - post_grades() saved new cache record.')
        return grades

    @property
    def context_id(self):
        return self._context_id

    @context_id.setter
    def context_id(self, value):
        """
        the context_id changed, so try
        reinitializing the course and course_enrollment cache objects.
        """

        # check for integrity between context_id and the current contents of lti_params
        if self.lti_params.get['context_id'] is not None:
            if value != self.lti_params.get['context_id']:
                raise LTIBusinessRuleError("Tried to set context_id to {value}, which is inconsistent with the " \
                    "current value of lti_params['context_id']: {lti_params}.".format(
                        value=value,
                        lti_params=self.lti_params.get['context_id']
                    ))

        # need to clear all class properties to ensure integrity between lti_params values and whatever is
        # currently present in the cache.
        self.init()

        self._context_id = value

        self.register_course()
        self.register_enrollment()

    @property
    def lti_params(self):
        return self._lti_params

    @lti_params.setter
    def lti_params(self, value):
        """
        lti_params json object changed, so clear course and course_enrollment
        also need to initialize any property values that are sourced from lti_params
        """
        # ensure that this object is being instantiated with data that originated
        # from an LTI authentication from Willo Labs.
        if not is_willo_lti(value):
            raise LTIBusinessRuleError("Tried to instantiate Willo Labs CourseProvisioner with lti_params " \
                "that did not originate from Willo Labs: '%s'." % value)

        # need to clear all class properties to ensure integrity between lti_params values and whatever is
        # currently present in the cache.
        self.init()

        self._lti_params = value

        # property initializations from lti_params
        self.context_id = value.get['context_id']      # uniquely identifies course in Willo
        self.user_id = value.get['user_id']            # uniquely identifies user in Willo



    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        """
        the user object changed, so reinitialize any properties that are functions of user.
        also need to try to reinitialize course_enrollment.
        """
        self._user = value

        # initialize properties that depend on user
        self.is_faculty = is_faculty(self.user)

        # clear, and attempt to reinitialize the enrollment cache.
        self._course_enrollment = None
        self.register_enrollment()

    @property
    def course_id(self):
        return self._course_id

    @course_id.setter
    def course_id(self, value):
        if not is_valid_course_id(value):
            raise LTIBusinessRuleError("Invalid course_id: '%s'." % value)

        self._course_id = value
        self._course = None
        self._course_enrollment = None

        self.register_course()
        self.register_enrollment()


    @property
    def course(self):
        """
        return a cached instance of the LTIExternalCourse record, if it exists.
        otherwise tries to register a new context_id/course_id course record
        """

        # try to return an instance, if we have one.
        if self._course is not None:
            return self._course

        # otherwise, try to retreive an instance from the cache, if it exists
        self._course = self.register_course()

        return self._course

    @course.setter
    def course(self, value):
        if not isinstance(value, LTIExternalCourse):
            raise LTIBusinessRuleError("Tried to assign an object to course property that is not" \
                "an instance of third_party_auth.models.LTIExternalCourse.")

        self._course = value
        self._course_enrollment = None



    @property
    def course_enrollment(self):
        """
        returns a cached instance of LTIExternalCourseEnrollment, if it exists.
        otherwise tries to register a new user / course record
        """

        # try to return an instance, if we have one.
        if self._course_enrollment is not None:
            return self._course_enrollment

        # otherwise, try to retreive an instance from the cache, if it exists
        self.course_enrollment = self.register_enrollment()

        return self._course_enrollment

    @course_enrollment.setter
    def course_enrollment(self, value):
        
        if not isinstance(value, LTIExternalCourseEnrollment):
            raise LTIBusinessRuleError("Tried to assign an object to course_enrollment property that is not" \
                "an instance of third_party_auth.models.LTIExternalCourseEnrollment.")

        self._course_enrollment = value
