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
from django.utils.dateparse import parse_date
from django.conf import settings

from common.djangoapps.third_party_auth.lti_consumers.willolabs.models import (
    LTIExternalCourse,
    LTIExternalCourseEnrollment,
    LTIExternalCourseEnrollmentGrades,
    LTIExternalCourseAssignmentProblems,
    LTIExternalCourseAssignments,
    )
from student.models import is_faculty, CourseEnrollment
from common.djangoapps.third_party_auth.lti_consumers.willolabs.utils import is_willo_lti, is_valid_course_id
from common.djangoapps.third_party_auth.lti_consumers.willolabs.exceptions import LTIBusinessRuleError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import BlockUsageLocator

#from django.db.models import Sum

log = logging.getLogger(__name__)
DEBUG = settings.DEBUG

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
        refresh()
        clear_cache()
        register_course()
        register_enrollment()
        post_grades()

    properties:
    -----------
        lti_params
        user
        course_id
        context_id
        course
        course_assignments
        course_assignment_problems
        course_enrollment
        course_enrollment_grades
    """
    def __init__(self, lti_params=None, user=None, course_id=None, clear_cache=False):
        if DEBUG: log.info('LTISession.__init__()')

        # initialize all class variables
        self.init()

        # optimization: this prevents register_course from being called multiple times
        # while property values are initializing.
        if lti_params is not None and course_id is not None:
            self.COMPLETE_MAPPING = True
        else:
            self.COMPLETE_MAPPING = False

        # class initializations
        #----------------------------------------------------------------------
        self.set_lti_params(lti_params)     # this needs to initialized first bc it resets all
                                            # other class properties.

        self.set_user(user)                 # Rover (django) user object
        
        self.set_course_id(course_id)       # Rover (Open edX) course_id (aka Opaque Key)
                                            # this MUST be initialized after self.lti_params

        # removes any cache data that is persisted to MySQL
        if clear_cache:
            self.clear_cache()

        # retrieve cache data from MySQL
        self.refresh()
        if DEBUG:
            log.info('LTISession.__init__() user: {user}, context_id: {context_id}'.format(
                user=self.get_user(),
                context_id=self.get_context_id()
            ))

    def init(self):
        """ Initialize class variables """
        if DEBUG: log.info('LTISession.init()')
        self._context_id = None
        self._course = None
        self._course_enrollment = None
        self._course_enrollment_grades = None
        self._lti_params = None
        self._user = None
        self._course_id = None

    def refresh(self):
        """
        Retrieve cached content from MySQL for the current context_id, user
        """
        self.register_course()
        self.register_enrollment()

        # handle alternative non-LTI initializations from within the Grader programs.
        if self.get_lti_params() is None:
            # we need both a user and a course_id.
            if self.get_user() is None or self.get_course_id() is None:
                return None

            course = LTIExternalCourse.objects.filter(course_id=self.get_course_id()).first()
            if course:
                self.set_course(course)
                self._context_id = course.context_id
                course_enrollment = LTIExternalCourseEnrollment.objects.filter(
                    course = course, 
                    user = self._user
                    ).first()
                self.set_course_enrollment(course_enrollment)



    def clear_cache(self):
        """
        Remove cached content from MySQL for the current context_id, user
        """
        if DEBUG: log.info('clear_cache()')

        context_id = self.get_context_id()
        user = self.get_user()

        course = LTIExternalCourse.objects.filter(
            context_id=context_id
            )
        course.delete()

        enrollment = LTIExternalCourseEnrollment.objects.filter(
            course = course, 
            user = user
            )
        enrollment.delete()

    def register_course(self):
        """
        try to retrieve a cached course record for the context_id / course_id
        otherwise, create a new record for the cache.
        """
        if DEBUG: log.info('LTISession - register_course()')

        if self.get_lti_params() is None:
            return None

        self._course = None
        self._course_enrollment = None

        # if __init__() received both lti_params and a course_id then we should 
        # check to verify that we are fully initialized before attempting to 
        # register the course.
        if self.COMPLETE_MAPPING and (self.get_course_id() is None or self.get_lti_params() is None):
            if DEBUG: 
                log.info('LTISession - register_course() - COMPLETE_MAPPING=True'\
                    'but we are not yet fully initialized. exiting. course_id: {course_id}, lti_params: {lti_params}'.format(
                        course_id = self.get_course_id(),
                        lti_params = self.get_lti_params()
                    )
                )
            return None

        # another check against partial initialization, or corruption of the property values.
        # self.context_id is automatically initialized from self.lti_params. however,
        # the property value is editable and can be set to None.
        if self.get_context_id() is None:
            if DEBUG: log.info('LTISession - register_course() - context_id is not set. exiting.')
            return None

        course = LTIExternalCourse.objects.filter(context_id=self.context_id).first()
        if course:
            if DEBUG: log.info('LTISession.register_course() - found a cached course.')
            # we didn't necesarily know the course_id at the time the record was created.
            # the course_id could materialize at any time, and if so then we'll 
            # need to persist the value.
            if course.course_id is None and self.get_course_id() is not None:
                course.course_id = self.get_course_id()
                course.save()
            else:
                # sneaky write to ensure integrity between context_id / course_id.
                #
                # Note: if for any reason there were descrepancy between course.course_id
                # and a not-null value of self.course_id, then we'll always assume
                # that course.course_id is the correct value.
                self._course_id = course.course_id

            return course 

        if self.get_lti_params() is None or self.get_course_id() is None:
            if DEBUG: log.info('LTISession.register_course() - missing some required data. cannot cache. exiting.')
            return None

        date_str = self._lti_params.get('custom_canvas_course_startat')
        # FIX NOTE: this is a complete kluge. need to learn more about custom_canvas_course_startat
        # and then change this logic accordingly.
        if date_str is not None:
            date_str = date_str[0:10]
        else:
            date_str = "2019/01/01"

        custom_canvas_course_startat = parse_date(date_str)

        course = LTIExternalCourse(
            context_id = self.get_context_id(),
            course_id = self.get_course_id(),
            context_title = self._lti_params.get('context_title'),
            context_label = self._lti_params.get('context_label'),
            ext_wl_launch_key = self._lti_params.get('ext_wl_launch_key'),
            ext_wl_launch_url = self._lti_params.get('ext_wl_launch_url'),
            ext_wl_version = self._lti_params.get('ext_wl_version'),
            ext_wl_outcome_service_url = self._lti_params.get('ext_wl_outcome_service_url'),
            custom_canvas_api_domain = self._lti_params.get('custom_canvas_api_domain'),
            custom_canvas_course_id = self._lti_params.get('custom_canvas_course_id'),
            custom_canvas_course_startat = custom_canvas_course_startat,
            tool_consumer_info_product_family_code = self._lti_params.get('tool_consumer_info_product_family_code'),
            tool_consumer_info_version = self._lti_params.get('tool_consumer_info_version'),
            tool_consumer_instance_contact_email = self._lti_params.get('tool_consumer_instance_contact_email'),
            tool_consumer_instance_guid = self._lti_params.get('tool_consumer_instance_guid'),
            tool_consumer_instance_name = self._lti_params.get('tool_consumer_instance_name'),
        )
        
        course.save()
        if DEBUG: log.info('LTISession.register_course() - saved new cache record.')
        return course

    def register_enrollment(self):
        """
        try to retreive a cached enrollment record for the context_id / user
        otherwise, create a new record for the cache.
        """
        if DEBUG: log.info('LTISession.register_enrollment()')

        if self.get_lti_params() is None:
            return None

        self._course_enrollment = None

        if self.get_user() is None or self.get_context_id() is None:
            # we need a user and a context_id. otherwise, there's nothing to do here.
            return None

        # look for a cached record for this user / context_id
        enrollment = LTIExternalCourseEnrollment.objects.filter(
            course = self.get_course(), 
            user = self.get_user()
            ).first()
        if enrollment:
            # if we have a cached enrollment record then we know that we also have the parent course
            # record, where the course_id is stored.

            # set course enrollment
            self._course_enrollment = enrollment
            if DEBUG: log.info('LTISession.register_enrollment() - returning a cached enrollment record.')
            return enrollment

        if self.get_lti_params() is None or \
            self.get_course() is None or \
            self.get_course_id() is None or \
            not CourseEnrollment.is_enrolled(self.get_user(), self.get_course_id()):
            if DEBUG: log.info('LTISession.register_enrollment() - user not enrolled, or missing some required information. exiting.')
            return None

        enrollment = LTIExternalCourseEnrollment(
            course = self.get_course(),
            user = self.get_user(),
            lti_user_id = self.user_id,
            custom_canvas_user_id = self._lti_params.get('custom_canvas_user_id'),
            custom_canvas_user_login_id = self._lti_params.get('custom_canvas_user_login_id'),
            custom_canvas_person_timezone = self._lti_params.get('custom_canvas_person_timezone'),
            ext_roles = self._lti_params.get('ext_roles'),
            ext_wl_privacy_mode = self._lti_params.get('ext_wl_privacy_mode'),
            lis_person_contact_email_primary = self._lti_params.get('lis_person_contact_email_primary'),
            lis_person_name_family = self._lti_params.get('lis_person_name_family'),
            lis_person_name_full = self._lti_params.get('lis_person_name_full'),
            lis_person_name_given = self._lti_params.get('lis_person_name_given'),
        )
        enrollment.save()

        if DEBUG: log.info('LTISession - register_enrollment() saved new cache record.')
        return enrollment

    def post_grades(self, usage_key, grades_dict):
        """
            usage_key:  identifier for a problem of a Rover course. 
                        corresponds to the homework problem that was just graded.

            grades_dict: contains all fields from grades.models.PersistentSubsectionGrade
                    {
                        'grades': {
                            'section_display_name': 'Chapter 5 Section 1 Quadratic Functions Sample Homework'
                            'section_attempted_graded': True, 
                            'section_possible_graded': 17.0, 
                            'section_earned_graded': 0.0, 
                            'section_possible_all': 17.0, 
                            'section_earned_all': 0.0}
                            'section_grade_percent': 0.0
                            }, 
                        'url': u'https://dev.roverbyopenstax.org/courses/course-v1:ABC+OS9471721_9626+01/courseware/c0a9afb73af311e98367b7d76f928163/c8bc91313af211e98026b7d76f928163'
                    }

        """
        if DEBUG: log.info('LTISession - post_grades()')
        if self.get_course_enrollment() is None or self.get_user() is None or self.get_course() is None:
            raise LTIBusinessRuleError("course, course_enrollment and user are required.")

        if not grades_dict['grades']['section_attempted_graded']:
            # no grade data to report
            return False
        try:
            # validate the usage_key to verify that it at least
            # points to SOMETHING in Rover.
            if isinstance(usage_key, str) or isinstance(usage_key, unicode):
                key = UsageKey.from_string(usage_key)
            else:
                if isinstance(usage_key, UsageKey) or isinstance(usage_key, BlockUsageLocator):
                    pass
                else:
                    raise LTIBusinessRuleError("Tried to pass an invalid usage_key: {key_type} {usage_key} ".format(
                            key_type=type(usage_key),
                            usage_key=usage_key
                        ))
        except:
            raise LTIBusinessRuleError("Tried to pass an invalid usage_key: {key_type} {usage_key} ".format(
                    key_type=type(usage_key),
                    usage_key=usage_key
                ))

        curr = LTIExternalCourseEnrollmentGrades.objects.filter(
            course_enrollment = self.get_course_enrollment(),
            section_url = grades_dict['url']
        ).order_by('-created').first()

        if not curr or\
            curr.earned_all != grades_dict['grades']['section_earned_all'] or\
            curr.possible_all != grades_dict['grades']['section_possible_all'] or\
            curr.earned_graded != grades_dict['grades']['section_earned_graded'] or\
            curr.possible_graded != grades_dict['grades']['section_possible_graded']:

            # cache the relationship between this assignment URL and the course to which it belongs.
            assignment = self.set_course_assignment(
                url=grades_dict['url'], 
                display_name=grades_dict['grades']['section_display_name']
                )

            # cache the relationship between the homework problem that was just graded and the assignment to which it belongs.
            problem = self.set_course_assignment_problem(
                course_assignment=assignment, 
                usage_key=usage_key
                )

            # cache the grade data
            grades = LTIExternalCourseEnrollmentGrades(
                course_enrollment = self.get_course_enrollment(),
                course_assignment = assignment,
                usage_key = usage_key,
                section_url = grades_dict['url'],
                earned_all = grades_dict['grades']['section_earned_all'],
                possible_all = grades_dict['grades']['section_possible_all'],
                earned_graded = grades_dict['grades']['section_earned_graded'],
                possible_graded = grades_dict['grades']['section_possible_graded']
            )
            grades.save()

            if DEBUG: log.info('LTISession - post_grades() saved new cache record - username: {username}, '\
                'course_id: {course_id}, context_id: {context_id}, usage_key: {usage_key}, grades: {grades}'.format(
                username = self.get_user().username,
                usage_key = usage_key,
                course_id = self.get_course().course_id,
                context_id = self.get_course().context_id,
                grades = grades_dict
            ))
            return True
        else:
            if DEBUG: log.info('LTISession - post_grades() nothing new to record. exiting')
            return False

    #=========================================================================================================
    #                                       PROPERTIES SETTERS & GETTERS
    #=========================================================================================================
    """
    def get_course_assignment_grades(self, usage_key):

        grades = LTIExternalCourseEnrollmentGrades.objects.filter(
            course_enrollment = self.get_course_enrollment(),
            course_assignment = self.get_course_assignment(usage_key)
        ).aggregate(
            Sum('earned_all'),
            Sum('possible_all'),
            Sum('earned_graded'),
            Sum('possible_graded'),
        )

        return grades
    """

    def get_course_assignment_grade(self, usage_key):
        """
        Try to retrieve a cached course assignment grade object for the given usage_key (Opaque Key).
        """
        if DEBUG: log.info('LTISession.get_course_assignment_grade() - usage_key: {usage_key} {key_type}'.format(
            usage_key=usage_key,
            key_type=type(usage_key)
        ))
        grade = LTIExternalCourseEnrollmentGrades.objects.filter(
            course_enrollment = self.get_course_enrollment(),
            course_assignment = self.get_course_assignment(usage_key)
        ).order_by('-created').first()
        return grade

    def get_course_assignment(self, usage_key):
        """
        Try to retrieve a cached course assignment for the given usage_key (Opaque Key).
        """
        if DEBUG: log.info('LTISession.get_course_assignment() - usage_key: {usage_key} {key_type}'.format(
            usage_key=usage_key,
            key_type=type(usage_key)
        ))
        problem = LTIExternalCourseAssignmentProblems.objects.filter(
            usage_key = usage_key
        ).first()
        if problem:
            if DEBUG: log.info('LTISession.get_course_assignment() - returning a cached record.')
            return problem.course_assignment

        if DEBUG: log.info('LTISession.get_course_assignment() - no record found.')
        return None

    def set_course_assignment(self, url, display_name):
        """
        Cache the given assignment URL.
        """
        if DEBUG: log.info('LTISession.set_course_assignment() - {url}, {display_name}'.format(
            url=url,
            display_name=display_name
        ))

        assignment = LTIExternalCourseAssignments.objects.filter(
            course = self.get_course(),
            url = url
        ).first()

        if assignment:
            if DEBUG: log.info('LTISession.set_course_assignment() - returning a cached record.')
            return assignment

        if self.get_course() is None:
            if DEBUG: log.info('LTISession.set_course_assignment() - get_course() returned None. Exiting.')
            return None

        assignment = LTIExternalCourseAssignments(
            course = self.get_course(),
            url = url,
            display_name = display_name
        )
        assignment.save()
        if DEBUG: log.info('LTISession.set_course_assignment() - creating and returning a new record.')
        return assignment

    def get_course_assignment_problem(self, usage_key):
        """
        Try to retrieve a cached assignment problem.
        """
        problem = LTIExternalCourseAssignmentProblems.objects.filter(
            usage_key = usage_key
        )
        if problem:
            if DEBUG: log.info('LTISession.get_course_assignment_problem() - returning a cached record.')

        return problem

    def set_course_assignment_problem(self, course_assignment, usage_key):
        """
        cache an assignment problem.
        """
        if DEBUG: log.info('LTISession.set_course_assignment_problem() - {course_assignment}, {usage_key}.'.format(
            course_assignment=course_assignment,
            usage_key=usage_key
        ))
        problem = LTIExternalCourseAssignmentProblems.objects.filter(
            usage_key = usage_key
        )
        if problem:
            if DEBUG: log.info('LTISession.set_course_assignment_problem() - returning a cached problem record: {problem}'.format(
                problem=problem
            ))
            return problem

        problem = LTIExternalCourseAssignmentProblems(
            course_assignment = course_assignment,
            usage_key = usage_key
        )
        problem.save()
        return problem

    
    def get_context_id(self):
        if DEBUG: log.info('LTISession.get_context_id() - {value}'.format(
            value=self._context_id
        ))
        return self._context_id

    
    def set_context_id(self, value):
        """
        the context_id changed, so try
        reinitializing the course and course_enrollment cache objects.
        """
        if DEBUG: log.info('LTISession.set_context_id() - {value}'.format(
            value=value
        ))
        # check for integrity between context_id and the current contents of lti_params
        if self.get_lti_params().get('context_id') is not None:
            if value != self.get_lti_params().get('context_id'):
                raise LTIBusinessRuleError("Tried to set context_id to {value}, which is inconsistent with the " \
                    "current value of lti_params['context_id']: {lti_params}.".format(
                        value=value,
                        lti_params=self.get_lti_params().get('context_id')
                    ))

        # need to clear all class properties to ensure integrity between lti_params values and whatever is
        # currently present in the cache.
        self.init()

        self._context_id = value
    
    def get_lti_params(self):
        if DEBUG: log.info('LTISession.get_lti_params() - {value}'.format(
            value = 'Set' if self._lti_params is not None else 'None'
        ))
        return self._lti_params

    
    def set_lti_params(self, value):
        """
        lti_params json object changed, so clear course and course_enrollment
        also need to initialize any property values that are sourced from lti_params
        """
        if DEBUG: log.info('set_lti_params()')
            
        # ensure that this object is being instantiated with data that originated
        # from an LTI authentication from Willo Labs.
        if value is not None and not is_willo_lti(value):
            raise LTIBusinessRuleError("Tried to instantiate Willo Labs CourseProvisioner with lti_params " \
                "that did not originate from Willo Labs: '%s'." % value)

        # need to clear all class properties to ensure integrity between lti_params values and whatever is
        # currently present in the cache.
        self.init()

        self._lti_params = value

        # property initializations from lti_params
        if self._lti_params is not None:
            self._context_id = value.get('context_id')          # uniquely identifies course in Willo
            self.user_id = value.get('user_id')                 # uniquely identifies user in Willo


    def get_user(self):
        if DEBUG: log.info('LTISession.get_user() - {value}'.format(
            value=self._user
        ))
        return self._user

    def set_user(self, value):
        """
        the user object changed, so reinitialize any properties that are functions of user.
        also need to try to reinitialize course_enrollment.
        """
        if DEBUG: log.info('set_user()')
        self._user = value

        # initialize properties that depend on user
        self.is_faculty = is_faculty(self.user)

        # clear, and attempt to reinitialize the enrollment cache.
        self._course_enrollment = None

    def get_course_id(self):
        if DEBUG: log.info('get_course_id() - {val}, {obj_type}'.format(
            val = self._course_id,
            obj_type = type(self._course_id)
        ))
        return self._course_id

    def set_course_id(self, value):
        if DEBUG: log.info('set_course_id() - {value}, {obj_type}'.format(
            value=value,
            obj_type=type(value)
        ))

        previous_value = self._course_id
        if isinstance(value, CourseKey):
            self._course_id = value
        else:
            if isinstance(value, str) or isinstance(value, unicode):
                self._course_id = CourseKey.from_string(value)
            else:
                raise LTIBusinessRuleError("Course_key provided is not a valid object type"\
                    " ({}). Must be either CourseKey or String.".format(
                    type(value)
            ))

        if previous_value != value:
            self._course = None
            self._course_enrollment = None

    def get_course(self):
        """
        return a cached instance of the LTIExternalCourse record, if it exists.
        otherwise tries to register a new context_id/course_id course record
        """
        if DEBUG: log.info('LTISession.get_course() - {value}'.format(
            value=self._course
        ))

        # try to return an instance, if we have one.
        if self._course is not None:
            return self._course

        # otherwise, try to retreive an instance from the cache, if it exists
        self._course = self.register_course()

        return self._course

    def set_course(self, value):
        if DEBUG: log.info('set_course())')
        if not isinstance(value, LTIExternalCourse):
            raise LTIBusinessRuleError("Tried to assign object {dtype} {obj} to course property that is not" \
                " an instance of third_party_auth.models.LTIExternalCourse.".format(
                    dtype=type(value),
                    obj=value
                ))

        self._course = value
        self._course_enrollment = None

    def get_course_enrollment(self):
        """
        returns a cached instance of LTIExternalCourseEnrollment, if it exists.
        otherwise tries to register a new user / course record
        """
        if DEBUG: log.info('LTISession.get_course_enrollment() - {value}'.format(
            value=self._course_enrollment
        ))

        # try to return an instance, if we have one.
        if self._course_enrollment is not None:
            return self._course_enrollment

        # otherwise, try to retreive an instance from the cache, if it exists
        self._course_enrollment = self.register_enrollment()

        return self._course_enrollment

    def set_course_enrollment(self, value):
        if DEBUG: log.info('LTISession.set_course_enrollment() - {value}, {val_type}'.format(
            value=value,
            val_type=type(value)
        ))
        
        if not isinstance(value, LTIExternalCourseEnrollment):
            raise LTIBusinessRuleError("Tried to assign an object to course_enrollment property that is not" \
                "an instance of third_party_auth.models.LTIExternalCourseEnrollment.")

        self._course_enrollment = value


    context_id = property(get_context_id, set_context_id)
    lti_params = property(get_lti_params, set_lti_params)
    user = property(get_user, set_user)
    course_id = property(get_course_id, set_course_id)
    course = property(get_course, set_course)
    course_enrollment = property(get_course_enrollment, set_course_enrollment)