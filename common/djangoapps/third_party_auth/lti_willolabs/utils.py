"""
Lawrence McDaniel
lpm0073@gmail.com
https://lawrencemcdaniel.com

Third-party-auth for LTI via Willo Labs. 
Used for integration to Canvas, Blackboard, Moodle and other platforms.
"""
import logging
import json

from third_party_auth.models import (
    LTIWilloLabsGradeSynCourse,
    LTIWilloLabsGradeSynCourseEnrollment,
    LTIWilloLabsGradeSynCourseEnrollmentGrades
    )

log = logging.getLogger(__name__)

class WilloLTISession:
    """
    mcdaniel dec-2019

    Persists external course and enrollment data provided by LTI authentication via
    tpa_lti_params. Establishes the relationships between external courses/users and 
    the corresponding Rover courses/users.

    These relationships are required so that we can send Grade Sync requests to the Willo Lab api.
    """
    def __init__(self, tpa_lti_params, response, user=None, course_id=None):
        self.tpa_lti_params = tpa_lti_params
        self.response = response

        # primary key values
        self.context_id = tpa_lti_params['context_id']      # uniquely identifies course in Willo
        self.user_id = tpa_lti_params['user_id']            # uniquely identifies user in Willo
        self.user = user                                    # Rover (django) user object
        self.course_id = course_id                          # Rover (Open edX) course_id (aka Opaque Key)

        # class declarations
        self.course = self.register_course()
        self.course_enrollment = self.register_enrollment()
        self.course_enrollment_grades = None

    def register_course(self):
        course = LTIWilloLabsGradeSynCourse.objects.filter(context_id=self.context_id)
        return course if course 

        course.context_id = self.context_id
        course.course_id = self.course_id

        course.context_title = self.tpa_lti_params.get('context_title')
        course.context_label = self.tpa_lti_params.get('context_label')
        course.ext_wl_launch_key = self.tpa_lti_params.get('ext_wl_launch_key')
        course.ext_wl_launch_url = self.tpa_lti_params.get('ext_wl_launch_url')
        course.ext_wl_version = self.tpa_lti_params.get('ext_wl_version')
        course.ext_wl_outcome_service_url = self.tpa_lti_params.get('ext_wl_outcome_service_url')
        course.custom_canvas_api_domain = self.tpa_lti_params.get('custom_canvas_api_domain')
        course.custom_canvas_course_id = self.tpa_lti_params.get('custom_canvas_course_id')
        course.custom_canvas_course_startat = self.tpa_lti_params.get('custom_canvas_course_startat')
        course.tool_consumer_info_product_family_code = self.tpa_lti_params.get('tool_consumer_info_product_family_code')
        course.tool_consumer_info_version = self.tpa_lti_params.get('tool_consumer_info_version')
        course.tool_consumer_instance_contact_email = self.tpa_lti_params.get('tool_consumer_instance_contact_email')
        course.tool_consumer_instance_guid = self.tpa_lti_params.get('tool_consumer_instance_guid')
        course.tool_consumer_instance_name = self.tpa_lti_params.get('tool_consumer_instance_name')
        
        course.save()
        return course

    def register_enrollment(self):
        enrollment = LTIWilloLabsGradeSynCourseEnrollment.objects.filter(context_id=self.context_id, user=self.user)
        return enrollment if enrollment

        enrollment.context_id = self.context_id
        enrollment.user = self.user
        enrollment.user_id = self.user_id

        enrollment.custom_canvas_user_id = self.tpa_lti_params.get('custom_canvas_user_id')
        enrollment.custom_canvas_user_login_id = self.tpa_lti_params.get('custom_canvas_user_login_id')
        enrollment.custom_canvas_person_timezone = self.tpa_lti_params.get('custom_canvas_person_timezone')
        enrollment.ext_roles = self.tpa_lti_params.get('ext_roles')
        enrollment.ext_wl_privacy_mode = self.tpa_lti_params.get('ext_wl_privacy_mode')
        enrollment.lis_person_contact_email_primary = self.tpa_lti_params.get('lis_person_contact_email_primary')
        enrollment.lis_person_name_family = self.tpa_lti_params.get('lis_person_name_family')
        enrollment.lis_person_name_full = self.tpa_lti_params.get('lis_person_name_full')
        enrollment.lis_person_name_given = self.tpa_lti_params.get('lis_person_name_given')

        enrollment.save()
        return enrollment

    def post_grades(self, usage_key, grades_dict):
        """
            usage_key: a subsection of a Rover course. corresponds to a homework assignment
            grades_dict: contains all fields from grades.models.PersistentSubsectionGrade
        """
        # 'context_id', 'user', 'usage_key'
        grades = LTIWilloLabsGradeSynCourseEnrollmentGrades.objects.filter(
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
        return grades


"""
  written by:   Matt Hangar, Willo Labs
                matt.hanger@willolabs.com

  Date:         June-2019

  Usage:        determine whether an LTI-authenticated user is faculty.

  Output:

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: Learner
    Extracted roles:
    	Learner
    Is instructor: False

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: urn:lti:instrole:ims/lis/Student,Student,urn:lti:instrole:ims/lis/Learner,Learner
    Extracted roles:
    	Learner
    	Student
    	urn:lti:instrole:ims/lis/Learner
    	urn:lti:instrole:ims/lis/Student
    Is instructor: False

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: Instructor
    Extracted roles:
    	Instructor
    Is instructor: True

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: Instructor,urn:lti:sysrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Administrator
    Extracted roles:
    	Instructor
    	urn:lti:instrole:ims/lis/Administrator
    	urn:lti:sysrole:ims/lis/Administrator
    Is instructor: True

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: TeachingAssistant
    Extracted roles:
    	TeachingAssistant
    Is instructor: True

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: urn:lti:instrole:ims/lis/Administrator
    Extracted roles:
    	urn:lti:instrole:ims/lis/Administrator
    Is instructor: True
"""

from third_party_auth.lti_willolabs.constants import instructor_roles
import logging
log = logging.getLogger(__name__)

def get_lti_faculty_status(lti_params):
    """
    Input parameters:
    ===================
    lti_params - a tpa_lti_params dictionary that is part of the http response body
    in an LTI authentication. see ./sample_data/tpa_lti_params.json for an example.

    Extract the LTI roles tuples parameter from lti_params, if it exists.
    Example:
    =======================
    roles_param = (
        'Learner',
        'urn:lti:instrole:ims/lis/Student,Student,urn:lti:instrole:ims/lis/Learner,Learner',
        'Instructor',
        'Instructor,urn:lti:sysrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Administrator',
        'TeachingAssistant',
        'urn:lti:instrole:ims/lis/Administrator'
    )
    """
    log.info('get_lti_faculty_status() - start')


    roles_param = lti_params.get("roles_param", ())
    if roles_param != ():
        log.info('get_lti_faculty_status() - found roles_param: {}'.format(roles_param))
        for role_param in roles_param:
            # build the lti_params dict similar to what exists in openedx third_party_auth LTIAuthBackend
            lti_params = {
                'email': 'matt.hanger@willolabs.com',
                'lis_person_name_full': 'Matt Hanger',
                'lis_person_name_given': 'Matt',
                'lis_person_name_family': 'Hanger',
                'roles': role_param
            }
            # extract the roles from lti_params
            user_roles = {x.strip() for x in lti_params.get('roles', '').split(',')}
            # check if the lti_params represent an instructor
            # use python set intersection operator "&" to simplify the check
            is_instructor = bool(user_roles & instructor_roles)
            if is_instructor:
                return "confirmed_faculty"

    """
        mcdaniel oct-2019
        example from University of Kansas:
        "roles": "urn:lti:role:ims/lis/Instructor",

    """
    roles = lti_params.get("roles", None)
    if roles:
        log.info('get_lti_faculty_status() - found roles: {}'.format(roles))
        if roles in instructor_roles:
            return "confirmed_faculty"

    return "no_faculty_info"
