# -*- coding: utf-8 -*-
"""
  Constants for LTI Willo Labs Grade Sync support in third_party_auth

  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020

"""
from __future__ import absolute_import
import os

#WORKING_PATH = os.path.dirname(os.path.abspath(__file__))

# from the LTI role vocabulary
# https://www.imsglobal.org/specs/ltiv1p1/implementation-guide#toc-8
# you need to decide which roles you'll treat as instructor, but here is
# a reasonable starting point
LTI_INSTRUCTOR_ROLES = set((
    'Instructor',
    'urn:lti:role:ims/lis/Instructor',
    'urn:lti:instrole:ims/lis/Instructor',
    'Faculty',
    'urn:lti:instrole:ims/lis/Faculty',
    'ContentDeveloper',
    'urn:lti:role:ims/lis/ContentDeveloper',
    'TeachingAssistant',
    'urn:lti:role:ims/lis/TeachingAssistant',
    'Administrator',
    'urn:lti:role:ims/lis/Administrator',
    'urn:lti:instrole:ims/lis/Administrator',
    'urn:lti:sysrole:ims/lis/Administrator'
))

# each of the following is an example of what can be expected in
# a single LTI message
LTI_ROLES_PARAM_EXAMPLES = (
    'Learner',
    'urn:lti:instrole:ims/lis/Student,Student,urn:lti:instrole:ims/lis/Learner,Learner',
    'Instructor',
    'Instructor,urn:lti:sysrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Administrator',
    'TeachingAssistant',
    'urn:lti:instrole:ims/lis/Administrator'
)

LTI_DOMAINS = (
    'test.willolabs.com',
    'stage.willolabs.com',
    'app.willolabs.com',
    'ca.willolabs.com',
    'ca-stage.willolabs.com'
)

LTI_CACHE_TABLES = (
    'LTIExternalCourse',
    'LTIExternalCourseEnrollment',
    'LTIExternalCourseEnrollmentGrades',
    'LTIExternalCourseAssignments',
    'LTIExternalCourseAssignmentProblems'
)
LTI_CACHE_TABLES_LIST = [
            ('LTIExternalCourse', 'LTIExternalCourse'),
            ('LTIExternalCourseEnrollment', 'LTIExternalCourseEnrollment'),
            ('LTIExternalCourseEnrollmentGrades', 'LTIExternalCourseEnrollmentGrades'),
            ('LTIExternalCourseAssignments', 'LTIExternalCourseAssignments'),
            ('LTIExternalCourseAssignmentProblems', 'LTIExternalCourseAssignmentProblems'),
        ]

LTI_PARAMS_DEFAULT_CONFIGURATION = {
    "LTIExternalCourse": {
        "context_title": "context_title",
        "context_label": "context_label",

        "ext_wl_launch_key": "ext_wl_launch_key",
        "ext_wl_launch_url": "ext_wl_launch_url",
        "ext_wl_version": "ext_wl_version",
        "ext_wl_outcome_service_url": "ext_wl_outcome_service_url",

        "tool_consumer_info_product_family_code": "tool_consumer_info_product_family_code",
        "tool_consumer_info_version": "tool_consumer_info_version",
        "tool_consumer_instance_contact_email": "tool_consumer_instance_contact_email",
        "tool_consumer_instance_guid": "tool_consumer_instance_guid",
        "tool_consumer_instance_name": "tool_consumer_instance_name",

        "custom_tpa_next": "custom_tpa_next",

        "custom_api_domain": "custom_canvas_api_domain",
        "custom_course_id": "custom_canvas_course_id",
        "custom_course_startat": "custom_canvas_course_startat",

        "custom_orig_context_id": "custom_orig_context_id",
        "custom_profile_url": "custom_tc_profile_url",
        "tool_consumer_instance_description": "tool_consumer_instance_description"

    },

    "LTIExternalCourseEnrollment": {
        "roles": "roles",
        "ext_roles": "ext_roles",
        "ext_wl_privacy_mode": "ext_wl_privacy_mode",
        "lis_person_contact_email_primary": "lis_person_contact_email_primary",
        "lis_person_name_family": "lis_person_name_family",
        "lis_person_name_full": "lis_person_name_full",
        "lis_person_name_given": "lis_person_name_given",

        "custom_user_id": "custom_canvas_user_id",
        "custom_user_login_id": "custom_canvas_user_login_id",
        "custom_person_timezone": "custom_canvas_person_timezone",

        "lis_person_sourcedid": "lis_person_sourcedid"
    },

    "LTIExternalCourseEnrollmentGrades": {},

    "LTIExternalCourseAssignments": {},

    "LTIExternalCourseAssignmentProblems": {}

}
