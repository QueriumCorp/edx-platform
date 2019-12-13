
"""
Third-party-auth module for LTI via Willo Labs. 
Used for integration to Canvas, Blackboard, Moodle and other platforms.
"""
import logging
import json

from third_party_auth.models import (
    LTIWilloLabsGradeSynCourse,
    LTIWilloLabsGradeSynCourseEnrollment,
    LTIWilloLabsGradeSynCourseEnrollmentGrades
    )

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

