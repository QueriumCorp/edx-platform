"""Library to interact with LTI tpa_lti_params dictionary data
and LTI cache tables

Raises:
    ValidationError: [description]
    LTIBusinessRuleError: [description]
"""

# python stuff
import json
try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs
import logging
import traceback

# django stuff
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings

# open edx stuff
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

# rover stuff
from .exceptions import LTIBusinessRuleError
from .utils import get_default_lti_configuration
from .constants import (
    LTI_INSTRUCTOR_ROLES,
    LTI_DOMAINS,
    LTI_CACHE_TABLES,
    LTI_PARAMS_DEFAULT_CONFIGURATION
    )
from .models import (
    LTIInternalCourse,
    LTIConfigurations,
    LTIConfigurationParams,
    LTIExternalCourse,
    LTIExternalCourseEnrollment,
    LTIExternalCourseAssignments,
    LTIExternalCourseEnrollmentGrades,
    )

log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG

class LTIParams(object):
    """Provides a means of dynamically mapping lti_params dictionary
    elements to class property names. Also handles all lti_params
    validations.
    """

    def __init__(self, lti_params):
        """Bootstrap this class. is_valid and set lti_params

        Arguments:
            lti_params {dict} -- a Python dictionary provided in the
            http response body of LTI authentication request.
            see https://readthedocs.roverbyopenstax.org/en/latest/how_to/lti.html#tpa-lti-params

        """
        if DEBUG: log.info('LTIParams.__init__()')

        self.dictionary = lti_params

        if not self.is_valid:
            log.error("LTIParams.__init__() - received invalid lti_params: {lti_params}".format(
                lti_params=lti_params
            ))

        if DEBUG: log.info('LTIParams.__init__() - initialized: {self}'.format(
            self=self
        ))

    def _get_cached_course_id(self):
        """Queries the cache and returns the course_id associated
        with a context_id

        Returns:
            course_id --
        """
        try:
            course = LTIExternalCourse.objects.filter(context_id=self.context_id).first()
            if course:
                if DEBUG:
                    log.info('LTIParams._get_cached_course_id() - found course_id: {course_id}'.format(
                        course_id=course.course_id
                    ))
                return course.course_id
        except ObjectDoesNotExist:
            pass
        if DEBUG:
            log.info('LTIParams._get_cached_course_id() - did not find a course_id.')
        return None


    def _get_course_id_from_tpa_next(self):
        """attempt to extract a course_id parameter from tpa_next
        in the lti_params dict, if it exists.

        example: "custom_tpa_next": "/account/finish_auth?course_id=course-v1%3AKU%2BOS9471721_108c%2BSpring2020_Fuka_Sample1&enrollment_action=enroll&email_opt_in=false"

        Returns:
            [CourseKey]
        """

        try:
            url = urlparse(url=self.custom_tpa_next)
            query_dict = parse_qs(url.query)
            course_id = query_dict.get('course_id')[0]
            course_key = CourseKey.from_string(course_id)

            if DEBUG:
                log.info('LTIParams._get_course_id_from_tpa_next() - found course_id: {course_id}'.format(
                    course_id=course_id
                ))

            return course_key

        except Exception as err:
            msg='LTIParams._get_course_id_from_tpa_next() - Exception encountered while extracting course_id from lti_params: \r\nError: {err}.\r\n{traceback}'.format(
                err=err,
                traceback=traceback.format_exc()
            )
            log.error(msg)

        return None

    def _get_course_id_from_lis_course_offering_sourcedid(self):
        """Attempt to get course section information from self.lis_course_offering_sourcedid
        used by Cal State LA for fall 2020

        examples:
            "lis_course_offering_sourcedid": "2209-90086"  (maps to external key2)

        Returns:
            [string]: course_id string value.
        """
        if DEBUG:
            log.info('LTIParams._get_course_id_from_lis_course_offering_sourcedid() - retrive course_id for lis_course_offering_sourcedid: {lis_course_offering_sourcedid}'.format(
                lis_course_offering_sourcedid=self.lis_course_offering_sourcedid
            ))

        try:
            course_id = LTIInternalCourse.objects.filter(lti_external_course_key1=self.lis_course_offering_sourcedid).first().course_id
            return course_id
        except:
            pass

        try:
            course_id = LTIInternalCourse.objects.filter(lti_external_course_key2=self.lis_course_offering_sourcedid).first().course_id
            return course_id
        except:
            pass

        try:
            course_id = LTIInternalCourse.objects.filter(lti_external_course_key3=self.lis_course_offering_sourcedid).first().course_id
            return course_id
        except:
            pass

        if DEBUG:
            log.info('LTIParams._get_course_id_from_lis_course_offering_sourcedid() - did not find a course_id.')

        return None

    @property
    def dictionary(self):
        """a dump of the original lti_params dictionary

        Returns:
            [dict] -- the lti_params dictionary passed to __init__()
        """
        return self._lti_params

    @dictionary.setter
    def dictionary(self, value):
        if isinstance(value, str):
            value = json.loads(value)

        self._lti_params = value

    def __getattr__(self, attr):
        """generic getter. Dynamic properties for lti_params elements.

        Arguments:
            attr {string} -- a lti_params element
        """
        # recursion buster
        if attr == '_lti_params':
            return

        return self.dictionary.get(attr)

    def __str__(self):
        return 'LTIParams(context_id={context_id}, user_id={user_id})'.format(
            context_id = self.context_id,
            user_id = self.user_id
        )

    @property
    def course_id(self):

        # priority 1: use the LTI External Course cache object if it exists
        course_id = self._get_cached_course_id()
        if course_id: return course_id

        # priority 2: try to parse the course key from custom_tpa_next
        course_id = self._get_course_id_from_tpa_next()
        if course_id: return course_id

        # priority 3: try to match self.lis_course_offering_sourcedid to one of the lti_external_course_key field
        # mcdaniel aug-2020: added this for Calstatela
        course_id = self._get_course_id_from_lis_course_offering_sourcedid()
        if course_id: return course_id

        raise LTIBusinessRuleError('LTIParams.course_id() was unable to determine the course_id from these lti_params: {lti_params}'.format(
                lti_params=self.dictionary
            ))

    @property
    def faculty_status(self):
        """
        Input parameters:
        ===================
        lti_params - a tpa_lti_params dictionary that is part of the http response body
        in an LTI authentication. see ./sample_data/tpa_lti_params.json for an example.

        Extract the LTI roles tuples parameter from lti_params, if it exists.
        Example:
        =======================
        roles_param = (
            'Learner', 'urn:lti:instrole:ims/lis/Student,Student,urn:lti:instrole:ims/lis/Learner,Learner',
            'Instructor', 'Instructor,urn:lti:sysrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Administrator',
            'TeachingAssistant', 'urn:lti:instrole:ims/lis/Administrator'
        )

        "roles": "urn:lti:role:ims/lis/Learner"

        "ext_roles": "urn:lti:instrole:ims/lis/Student,urn:lti:role:ims/lis/Learner,urn:lti:sysrole:ims/lis/User"
        """

        # 1. look for a roles_param tuple
        if self.roles_param:
            log.info('LTIParams.faculty_status() - found roles_param: {roles_param}'.format(
                roles_param=self.roles_param
                ))
            for role_param in self.roles_param:
                # extract a list of the roles from lti_params
                user_roles = {x.strip() for x in role_param.split(',')}
                # check if the lti_params represent an instructor
                # use python set intersection operator "&" to simplify the check
                is_instructor = bool(user_roles & LTI_INSTRUCTOR_ROLES)
                if is_instructor:
                    return "confirmed_faculty"

        # 2. check for roles list
        """
        mcdaniel oct-2019
        example from University of Kansas:
        "roles": "urn:lti:role:ims/lis/Instructor",
        """
        if self.roles:
            log.info('LTIParams.faculty_status - found roles: {roles}'.format(
                roles=self.roles
                ))
            if self.roles in LTI_INSTRUCTOR_ROLES:
                return "confirmed_faculty"


        # 3. check for ext_roles list
        """
        mcdaniel feb-2020
        example:
        "ext_roles": "urn:lti:instrole:ims/lis/Student,urn:lti:role:ims/lis/Learner,urn:lti:sysrole:ims/lis/User",
        """
        if self.ext_roles:
            log.info('LTIParams.faculty_status - found ext_roles: {roles}'.format(
                roles=self.ext_roles
                ))
            if self.ext_roles in LTI_INSTRUCTOR_ROLES:
                return "confirmed_faculty"

        return "no_faculty_info"

    @property
    def is_willolabs(self):
        """Determine if the lti_params dictionary provided to __init__
        came from Willo Labs.

        Returns:
            [Boolean] -- True if the dictionary came from Willo Labs.
                         False otherwise.
        """
        try:
            launch_url = self.ext_wl_launch_url
            if not launch_url:
                if DEBUG: log.info('LTIParams.is_willolabs() - no ext_wl_launch_url. returning False')
                return False

            launch_domain = urlparse(launch_url).hostname
            if not launch_domain:
                if DEBUG: log.info('LTIParams.is_willolabs() - invalid launch_domain: {launch_domain}. returning False'.format(
                    launch_domain=launch_domain
                ))
                return False

        except Exception as e:
            if DEBUG: log.info('LTIParams.is_willolabs() - exception: {exception}'.format(
                Exception=e
            ))
            pass
            return False

        if not launch_domain in LTI_DOMAINS:
            if DEBUG: log.info('LTIParams.is_willolabs() - invalid launch_domain {launch_domain}. returning False'.format(
                launch_domain=launch_domain
            ))
            return False

        if DEBUG: log.info('LTIParams.is_willolabs() returning True')
        return True

    @property
    def is_valid(self):
        """
        Determine from data in the lti_params json object returns by LTI authentication
        whether the session originated from Willo Labs.

        True if there is a parameter named "ext_wl_launch_url" and the value is a
        valid URL, and the hostname of the URL is contained in the set LTI_DOMAINS
        """

        if DEBUG: log.info('LTIParams.is_valid() - beginning validation')

        if not isinstance(self.dictionary, dict):
            if DEBUG: log.info('LTIParams.is_valid() - not a dict. returning False')
            return False

        if not self.context_id:
            if DEBUG: log.info('LTIParams.is_valid() - no context_id. returning False')
            return False

        if not self.user_id:
            if DEBUG: log.info('LTIParams.is_valid() - no user_id. returning False')
            return False

        if not self.lis_person_contact_email_primary:
            if DEBUG: log.info('LTIParams.is_valid() - no lis_person_contact_email_primary. returning False')
            return False

        if not self.lis_person_name_full:
            if DEBUG: log.info('LTIParams.is_valid() - no lis_person_name_full. returning False')
            return False

        if not self.lis_person_name_given:
            if DEBUG: log.info('LTIParams.is_valid() - no lis_person_name_given. returning False')
            return False

        if not self.lis_person_name_family:
            if DEBUG: log.info('LTIParams.is_valid() - no lis_person_name_family. returning False')
            return False

        if DEBUG: log.info('LTIParams.is_valid() - lti_params are validated.')
        return True


class LTIParamsFieldMap(object):
    """Provides a means of dynamically mapping LTI cache field names

    Arguments:
        table {string} -- name of a LTI Cache table

    Returns: {string} the field mapping corresponding to the attribute name accessed.
    """

    def __init__(self, lti_params, table):
        """Bootstrap this class

        Arguments:
            lti_params {dict or LTIParams} -- a lti_params dictionary or object

        Keyword Arguments:
            table {string} -- (default: {None}) a string representing an LTI cache table name

        Raises:
            ValidationError: if table name is not a valid LTI External table
                             if lti_params is an invalid format or structure
                             if lti_params did not originate from Willo Labs

            LTIBusinessRuleError: [description]
        """
        def get_lti_internal_course(course_id):
            """retreives the LTI Internal Course object for the course_id if it exists,
            otherwise creates and returns a new object.

            Args:
                course_id (string): string representation of a CourseKey

            Returns:
                [LTIInternalCourse]: returns a single record representing the LTI Internal Course for the course_id
            """
            if DEBUG:
                log.info('get_lti_internal_course() - course_id: {course_id}'.format(
                    course_id=course_id
                ))

            try:
                lti_internal_course = LTIInternalCourse.objects.filter(course_id=course_id).first()
                if lti_internal_course is not None:
                    return lti_internal_course
            except ObjectDoesNotExist:
                pass

            # didn't find a record, so we'll create one...
            lti_configuration = get_default_lti_configuration()
            lti_internal_course = LTIInternalCourse(
                course_id=course_id,
                enabled=True,
                lti_configuration=lti_configuration
            )
            lti_internal_course.save()
            log.info('LTIParamsFieldMap.__init__().get_lti_internal_course() created a new LTIInternalCourse record for course_id {course_id}'.format(
                course_id=course_id
            ))
            return lti_internal_course

        if not table in LTI_CACHE_TABLES:
            raise ValidationError('LTIParamsFieldMap.__init__() - Received table {table} but was expecting table to be any of {tables}'.format(
                table=table,
                tables=LTI_CACHE_TABLES
            ))

        if not isinstance(lti_params, LTIParams):
            lti_params = LTIParams(lti_params)

        if not lti_params.is_valid:
            raise ValidationError('LTIParamsFieldMap.__init__() - lti_params is not a valid LTI dictionary.')

        if not lti_params.is_willolabs:
            raise ValidationError('LTIParamsFieldMap.__init__() - lti_params dict did not originate from Willo Labs.')

        self.dictionary = lti_params.dictionary
        self.table = table

        """
        mcdaniel july-2020
        Phase II field mapping
        """
        # extract the Rover course identifier embedded in the tpa_next URL string
        course_id = lti_params.course_id

        # use the CourseKey object to identify the LTI Internal Course record
        ## mcdaniel july-2020: we need to anticipate the scenario where course_id is not yet setup

        internal_course = get_lti_internal_course(course_id)

        if internal_course is not None:
            lti_configuration = LTIConfigurations.objects.filter(id=internal_course.lti_configuration.id).first()

            # retrieve the field-level LTI Grade Sync mapping configuration for this course.
            lti_configuration_params = LTIConfigurationParams.objects.filter(
                configuration=internal_course.lti_configuration,
                table_name=table
                )

            # build a params configuration dict
            #
            # first, lets ensure that we have a complete field list by initializing
            # to the generic default mapping.
            self.configuration_parameters = LTI_PARAMS_DEFAULT_CONFIGURATION.get(table)

            # next, we iterate lti_configuration_params
            for param in lti_configuration_params:
                self.configuration_parameters[param.internal_field] = param.external_field

        if DEBUG:
            log.info('LTIParamsFieldMap.__init__() - course_id: {course_id}, internal_course: {internal_course}, lti_configuration: {lti_configuration}, table: {table}, lti_configuration_params: {lti_configuration_params}, configuration_parameters: {configuration_parameters}'.format(
                course_id=course_id,
                internal_course=internal_course,
                lti_configuration=lti_configuration,
                table=table,
                lti_configuration_params=lti_configuration_params.objects.count(),
                configuration_parameters=self.configuration_parameters
            ))


    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, value):
        self._table = value

    @property
    def dictionary(self):
        """a dump of the original lti_params dictionary

        Returns:
            [dict] -- the lti_params dictionary passed to __init__()
        """
        return self._lti_params

    @dictionary.setter
    def dictionary(self, value):
        self._lti_params = value

    def __getattr__(self, attr):
        """Implement dynamic attributes.

        Arguments:
            attr {string} -- string representation of a class attribute

        Returns:
            String -- Returns corresponding field mapping value from LTIConfigurationParams, if it exists.
        """

        # recursion buster
        if attr in ['_lti_params', '_table']:
            return

        if not self.dictionary:
            return None

        param_key = self.configuration_parameters.get(attr)
        value = self.dictionary.get(param_key)
        if DEBUG:
            log.info('get_lti_param() - table: {table}, attr: {attr}, param_key: {param_key}, value: {value}'.format(
                table=self.table,
                attr=attr,
                param_key=param_key,
                value = value
            ))
        return value


    def __str__(self):
        return 'LTIParamsFieldMap({table})'.format(
            table=self.table
        )

"""
------------------------------------------------------------------------------------------------------------------
Utility functions.
These are used in this module as well as gradesync.py
------------------------------------------------------------------------------------------------------------------
"""
def get_lti_user_id(course_id, username, context_id=None):
    """
    Retrieve the LTI Consumer user_id assigned to Rover username for course_id.
    This is passed in tpa_params during LTI authentication and cached.
    """

    if DEBUG:
        log.info('get_lti_user_id() - course_id: {course_id}, username: {username}'.format(
            course_id=course_id,
            username=username
        ))


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

    # if there's not a context_id then we still must
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
    Retrieve an LTI Consumer outcome service URL from the LTI cache.
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

"""
For pre-populating / initializing new LTI Configurations

format:
LTI Table name
    internal field: external field
"""

