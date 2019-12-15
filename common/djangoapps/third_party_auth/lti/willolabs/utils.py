"""
  written by:   Matt Hangar, Willo Labs
                matt.hanger@willolabs.com

  Date:         June-2019

  Usage:        determine whether an LTI-authenticated user is faculty.
"""
from third_party_auth.lti.willolabs.constants import (
    WILLO_INSTRUCTOR_ROLES, 
    WILLO_DOMAINS
    )
from urllib.parse import urlparse
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

import logging
log = logging.getLogger(__name__)

def is_willo_lti(lti_params):
    """
    Determine from data in the lti_params json object returns by LTI authentication
    whether the session originated from Willo Labs.

    True if there is a parameter named "ext_wl_launch_url" and the value is a 
    valid URL, and the hostname of the URL is contained in the set WILLO_DOMAINS
    """

    try:
        launch_domain = urlparse(lti_params.get("ext_wl_launch_url")).hostname
    except Exception as e:
        pass
        return False

    return launch_domain in WILLO_DOMAINS

def is_valid_course_id(value):

    # try to create an instance of CourseKey from the value passed
    try:
        course_key = CourseKey.from_string(value)
    except:
        pass
        return False

    # Verify that this course_id corresponds with a Rover course 
    if not CourseOverview.get_from_id(course_key):
        return False
    
    return True

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
            is_instructor = bool(user_roles & WILLO_INSTRUCTOR_ROLES)
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
        if roles in WILLO_INSTRUCTOR_ROLES:
            return "confirmed_faculty"

    return "no_faculty_info"

"""
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
