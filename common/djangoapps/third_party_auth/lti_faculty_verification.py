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
# from the LTI role vocabulary
# https://www.imsglobal.org/specs/ltiv1p1/implementation-guide#toc-8
# you need to decide which roles you'll treat as instructor, but here is
# a reasonable starting point
instructor_roles = set((
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
roles_param_examples = (
    'Learner',
    'urn:lti:instrole:ims/lis/Student,Student,urn:lti:instrole:ims/lis/Learner,Learner',
    'Instructor',
    'Instructor,urn:lti:sysrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Administrator',
    'TeachingAssistant',
    'urn:lti:instrole:ims/lis/Administrator'
)

def is_lti_faculty(strategy, details, user=None, *args, **kwargs):

    """
    Extract the LTI roles tuples parameter from details, if it exists.
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
    roles_param = details.get("roles_param", ())

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

    return "no_faculty_info"
