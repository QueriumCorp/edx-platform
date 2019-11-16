"""
  written by:   Matt Hangar, Willo Labs
                matt.hanger@willolabs.com

                Lawrence McDaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

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

from third_party_auth.lti_v1.constants import instructor_roles
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
