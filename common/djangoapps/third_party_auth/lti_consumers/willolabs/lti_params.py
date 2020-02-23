"""Library to interact with LTI tpa_lti_params dictionary data
and LTI cache tables

Raises:
    ValidationError: [description]
    LTIBusinessRuleError: [description]
"""
from django.core.exceptions import ValidationError
from opaque_keys import InvalidKeyError

from .constants import WILLO_INSTRUCTOR_ROLES, WILLO_DOMAINS, LTI_CACHE_TABLES
from .cache_config import parser
from .models import (
    LTIExternalCourse,
    LTIExternalCourseEnrollment,
    LTIExternalCourseAssignments,
    LTIExternalCourseEnrollmentGrades,
    )

DEBUG = True

class LTIParamsFieldMap(object):
    """Provides a means of dynamically mapping LTI cache field names
    to cache_config.ini field mapping parameters.
    
    Arguments:
        table {string} -- name of a LTI Cache table

    Returns: {string} the field mapping corresponding to the attribute name accessed.
    """

    def __init__(self, lti_params, table=None):
        if not table in LTI_CACHE_TABLES:
            raise ValidationError('LTIParamsFieldMap.__init__() - Received table {table} but was expecting table to be any of {tables}'.format(
                table=table,
                tables=LTI_CACHE_TABLES
            ))

        if value is not None and not is_willo_lti(lti_params):
            raise LTIBusinessRuleError("LTISession.set_lti_params() - Tried to instantiate Willo Labs CourseProvisioner with lti_params " \
                "that did not originate from Willo Labs: '%s'." % value)

        self.lti_params = lti_params
        self.table = table

    def __getattr__(self, attr):
	    """Implement dynamic attributes. 
        
        Arguments:
            attr {string} -- string representation of a class attribute
        
        Returns:
            String -- Returns corresponding cache_config value, if it exists.
        """
        return self.get_lti_param(key=attr)

    def __setattr__(self, attr):
        """Make all dynamic attributes read-only
        
        Arguments:
            attr {string} -- string representation of a dynamic attribute
        
        Raises:
            LTIBusinessRuleError:
        """
        raise LTIBusinessRuleError('LTIParamsFieldMap.__setattr__() - {attr} is a read-only attribute.'.format(
            attr=attr
        ))

    def get_lti_param(self, key):
        """Locates the cache_config.ini field mapping for 'key'. 
        Then retrieves the corresponding value from self.lti_params
        
        Arguments:
            table {string} -- the case-sensitive name of an LTI cache table.
            key {string} -- the lower case name of a field in an LTI cache table.
        
        Returns:
            [string] or None
        """
        if not self.lti_params:
            return None
        
        if not isinstance(key, str):
            raise LTIBusinessRuleError('LTIParamsFieldMap.get_lti_param() - was expecting a string value for key.')

        param_key = parser.get(self.table, key)
        value = self.lti_params.get(param_key)
        if DEBUG:
            log.info('get_lti_param() - table: {table}, key: {key}, param_key: {param_key}, value: {value}'.format(
                table=table,
                key=key,
                param_key=param_key,
                value = value
            ))
        return value

def get_cached_course_id(context_id):
    """Queries the cache and returns the course_id associated
    with a context_id
    
    Returns:
        course_id -- 
    """
    course = LTIExternalCourse.objects.filter(context_id=context_id).first()

    if course:
        return course.course_id

    return None


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

    "roles": "urn:lti:role:ims/lis/Learner"

    "ext_roles": "urn:lti:instrole:ims/lis/Student,urn:lti:role:ims/lis/Learner,urn:lti:sysrole:ims/lis/User"
    """

    # 1. look for a roles_param tuple
    roles_param = lti_params.get("roles_param", ())
    if roles_param != ():
        log.info('get_lti_faculty_status() - found roles_param: {}'.format(roles_param))
        for role_param in roles_param:
            # extract a list of the roles from lti_params
            user_roles = {x.strip() for x in role_param.split(',')}
            # check if the lti_params represent an instructor
            # use python set intersection operator "&" to simplify the check
            is_instructor = bool(user_roles & WILLO_INSTRUCTOR_ROLES)
            if is_instructor:
                return "confirmed_faculty"

    # 2. check for roles list
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


    # 3. check for ext_roles list
    """
    mcdaniel feb-2020
    example from Willo Labs
    "ext_roles": "urn:lti:instrole:ims/lis/Student,urn:lti:role:ims/lis/Learner,urn:lti:sysrole:ims/lis/User",
    """
    roles = lti_params.get("ext_roles", None)
    if roles:
        log.info('get_lti_faculty_status() - found ext_roles: {}'.format(roles))
        if roles in WILLO_INSTRUCTOR_ROLES:
            return "confirmed_faculty"

    return "no_faculty_info"


def is_willo_lti(lti_params):
    """
    Determine from data in the lti_params json object returns by LTI authentication
    whether the session originated from Willo Labs.

    True if there is a parameter named "ext_wl_launch_url" and the value is a 
    valid URL, and the hostname of the URL is contained in the set WILLO_DOMAINS
    """

    if not isinstance(lti_params, dict):
        return False

    try:
        if not lti_params.get("context_id"):
            return False

        if not lti_params.get("user_id"):
            return False

        an_important_url = lti_params.get("ext_wl_launch_url")
        if not an_important_url:
            return False

        launch_domain = urlparse(an_important_url).hostname
        if not launch_domain:
            return False

    except Exception as e:
        pass
        return False

    return launch_domain in WILLO_DOMAINS


def get_lti_user_id(course_id, username, context_id=None):
    """
     Retrieve the Willo Labs user_id assigned to Rover username for course_id.
     This is passed in tpa_params during LTI authentication and cached.
    """

    #msg='get_lti_user_id() - course_id: {course_id}, username: {username}'.format(
    #    course_id=course_id,
    #    username=username
    #)
    #print(msg)

    user = USER_MODEL.objects.get(username=username)
    course_key = CourseKey.from_string(course_id)
    if context_id is not None:
        course = LTIExternalCourse.objects.get(context_id=context_id)
        if course is not None and user is not None:
            try:
                course_enrollment = LTIExternalCourseEnrollment.objects.get(
                    course = course,
                    user = user
                )
                return course_enrollment.lti_user_id
            except:
                pass
        else: return None

    # if there's not a context_id then we will still must 
    # take into consideration that course_id may not be unique
    # for LTIExternalCourse given that multiple external LMS'
    # could potentially share a common Rover course.
    courses = LTIExternalCourse.objects.filter(course_id = course_key)
    for course in courses:
        try:
            course_enrollment = LTIExternalCourseEnrollment.objects.get(
                course = course,
                user = user
            )
            if course_enrollment is not None: return course_enrollment.lti_user_id
        except:
            pass
    return None


def get_ext_wl_outcome_service_url(course_id, context_id=None):
    """
     Retrieve a Willo Labs outcome service URL from the LTI cache.
     This is passed in tpa_params during LTI authentication and cached.
    """
    if context_id is not None:
        course = LTIExternalCourse.objects.get(context_id=context_id)
    return course.ext_wl_outcome_service_url

    course_key = CourseKey.from_string(course_id)
    course = LTIExternalCourse.objects.filter(course_id=course_key).first()
    return course[0].ext_wl_outcome_service_url



def get_lti_cached_result_date(
            course_id,
            username, 
            section_url,
            section_completed_date=None, 
            section_due_date=None
            ):
    """
      Try to retrieve an assignment completion date from the LTI cache.

      course_id: course key that contains the assignment
      username: Rover user who completed the assignment
      lti_id: the LTI unique identifier for the assignment, created from the Rover resource key (right-most segment of URL path)
      section_completed_date: an alternative date that is potentially supplied by the Rover grades api.
      section_due_date: ditto.
    """

    # need to consider that there might be more than one course with this course_id 
    user = USER_MODEL.objects.get(username=username)
    course_key = CourseKey.from_string(course_id)

    # must take into consideration that course_id is not unique
    # for LTIExternalCourse given that multiple external LMS'
    # could potentially share a common Rover course.
    courses = LTIExternalCourse.objects.filter(course_id = course_key)
    for course in courses:
        try:
            course_assignment=LTIExternalCourseAssignments.objects.get(
                course=course,
                url=section_url
            )
            course_enrollment=LTIExternalCourseEnrollment.objects.get(
                course=course,
                user=user
            )
            res = LTIExternalCourseEnrollmentGrades.objects.filter(
                course_assignment=course_assignment,
                course_enrollment=course_enrollment
            ).order_by('-created').first()
            if res is not None: return res.created
        except:
            pass

    if section_completed_date is not None: return section_completed_date
    if section_due_date is not None:  return section_due_date
    return datetime.datetime.now()


def is_lti_cached_user(user, context_id):
    """
     Test to see if there is cached LTI enrollment data for this user.

     user: a Django user model
     course_id: a Opaque Key object.
    """
    try:
        ret = LTIExternalCourseEnrollment.objects.get(
            course=LTIExternalCourse.objects.get(context_id=context_id),
            user=user
            )
        return ret is not None
    except LTIExternalCourseEnrollment.DoesNotExist:
        return False
