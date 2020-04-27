# -*- coding: utf-8 -*-
"""Manages cached course and enrollment relationship data between Rover 
and External platforms like Canvas, Blackboard and Moodle via Willo Labs

Raises:
    LTIBusinessRuleError
"""
from __future__ import absolute_import
import datetime
import logging
import json
import traceback

from django.utils.dateparse import parse_date
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from student.models import is_faculty, CourseEnrollment
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import BlockUsageLocator

# for locating a course assignment by its URL.
from lms.djangoapps.courseware.courses import get_course_by_id
from .utils import find_course_unit

from .exceptions import LTIBusinessRuleError
from .lti_params import LTIParamsFieldMap, LTIParams, get_cached_course_id
from .models import (
    LTIExternalCourse,
    LTIExternalCourseEnrollment,
    LTIExternalCourseEnrollmentGrades,
    LTIExternalCourseAssignmentProblems,
    LTIExternalCourseAssignments,
    )

User = get_user_model()
log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG

class LTISession(object):
    """Used during LTI authentication from external platforms connecting to Rover via
    Willo Labs. Persists external course and enrollment data provided during LTI authentication
    in the http response body, in a json object named lti_params. Establishes the 
    relationships between external courses/users and the corresponding Rover courses/users.
    These relationships are required by Rover's Grade Sync, so that we can send 
    Grade Sync requests to the Willo Lab api.
    
    Arguments:
        object {object} -- required to implement Python properties
    
    Raises:
        LTIBusinessRuleError
    """
    def __init__(self, lti_params=None, user=None, course_id=None, clear_cache=False):
        """Bootstrap initialization of the class. Much of our initialization is driven
        by lti_params if it exists. Otherwise, we have to carefully pick through
        which property initializations are possible based on which arguments are provided.
        Bootstrap sequence matters a lot.
        
        Keyword Arguments:
            lti_params {dict or LTIParams} -- (default: {None}) Provided in http request body during 
            authentication. contains extensive data on the student and the source system
            where authentication originated. 

            user {User} -- (default: {None}) Django User model.

            course_id {string} -- (default: {None}) A string representation of a CourseKey

            clear_cache {bool} -- (default: {False}) If true then all cache data for the
            User / context_id will be deleted.
        """

        if DEBUG: log.info('LTISession.__init__() - initializing. user: {user}, course_id: {course_id}, lti_params: {lti_params}'.format(
            user=user,
            course_id=course_id,
            lti_params='yes' if lti_params is not None else 'no'
        ))

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
        self.lti_params = lti_params        # this needs to initialized first bc it resets all
                                            # other class properties.


        if user:
            self.user = user                    # Rover (django) user object
        else:
            # try to set the user object from tpa_lti_params info.
            if lti_params is not None:
                username = self.lti_param.user_id
                if username is not None:
                    if DEBUG: log.info('LTISession.__init__() - trying to assign user from tpi_param data. username: {username}'.format(
                        username=username
                    ))
                    self.user = User.objects.get(username=username)
        
        if course_id:
            # assign the course_id passed to __init__()
            self.course_id = course_id              # Rover (Open edX) course_id (aka Opaque Key)
                                                    # this MUST be initialized after self.lti_params
        else:
            # if self.user is set, and we are lacking a course_id
            # then try to find the course in which the user is currently enrolled.
            #
            # note that this breaks if a student is enrolled in more than one course.
            # so we'll only use this in cases where only 1 course enrollment record is returned.
            if self.user is not None:
                enrollments = CourseEnrollment.enrollments_for_user(self.user)
                if enrollments is not None and len(enrollments) == 1:
                    self.course_id = enrollments[0].course_id
                    if DEBUG: log.info('LTISession.__init__() - located user enrollment. course: {course}'.format(
                        course=self.course_id
                    ))
                else:
                    # we'll arrive here if a) the student is enrolled in multiple courses, 
                    # or b) the student is not enrolled in any courses.
                    self.course_id =  self.get_cached_course_id(context_id=self.context_id)

        # removes any cache data that is persisted to MySQL
        if clear_cache:
            self.clear_cache()

        # retrieve cache data from MySQL
        self.refresh()

        if DEBUG: log.info('LTISession.__init__() - initialized. user: {user}, course: {course}, enrollment: {enrollment}, course_id: {course_id}, context_id: {context_id}'.format(
            user=self.user,
            course=self.course,
            enrollment=self.course_enrollment,
            course_id=self.course_id,
            context_id=self.context_id
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
        """Retrieve cached content from MySQL for the current context_id, user
        
        Returns:
            [type] -- [description]
        """

        if DEBUG: log.info('LTISession.refresh()')

        # refresh during LTI authentication
        if self.lti_params is not None:
            if self._course is None:
                self.course = self.register_course()

            return None

        # all other use cases (Grader programs, etc.)
        else:
            if DEBUG: log.info('LTISession.refresh() - lti_params not found. Initializing with user and course_id')
            if self.user is None:
                if DEBUG: log.info('LTISession.refresh() - self.user is not set. Exiting.')
                return None

            if self.course_id is None:
                if DEBUG: log.info('LTISession.refresh() - self.course_id is not set. Exiting.')
                return None

            if self.course is None:
                # belt & suspenders. this should have already been set by set_course_id()
                course = LTIExternalCourse.objects.filter(course_id=self.course_id).first()
                if course:
                    self.course = course
            
            if self.course_enrollment is None:
                # this only covers cases where cache data exists. if user is student
                # entering Rover for the first time then we'll still be None
                self.course_enrollment = LTIExternalCourseEnrollment.objects.filter(
                    course = self.course,
                    user = self._user
                    ).first()



    def clear_cache(self):
        """Remove cached content from MySQL for the current context_id, user
        """
        if DEBUG: log.info('clear_cache()')

        context_id = self.context_id
        user = self.user

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
        """try to retrieve a cached course record for the context_id / course_id
        otherwise, add a new course record to the cache.
        
        Returns:
            [LTIExternalCourse] -- the LTI cache record for the course_id
        """
        if DEBUG: log.info('LTISession.register_course()')

        course = None
        self._course = None
        self._course_enrollment = None

        # if __init__() received both lti_params and a course_id then we should 
        # check to verify that we are fully initialized before attempting to 
        # register the course.
        if self.COMPLETE_MAPPING and (self.course_id is None or self.lti_params is None):
            if DEBUG: 
                log.info('LTISession.register_course() - COMPLETE_MAPPING=True'\
                    'but we are not yet fully initialized. exiting. course_id: {course_id}, lti_params: {lti_params}'.format(
                        course_id = self.course_id,
                        lti_params = self.lti_params
                    )
                )
            return None

        # look for a record based on course_id (our most common use case), if its set
        if course is None and self._course_id is not None:
            course = LTIExternalCourse.objects.filter(course_id=self._course_id).first()

        # as a fallback, look for a cached record based on context_id, if its set
        if course is None and self._context_id is not None:
            course = LTIExternalCourse.objects.filter(context_id=self._context_id).first()

        if course:
            if DEBUG: log.info('LTISession.register_course() - found a cached course.')
            # we didn't necesarily know the course_id at the time the record was created.
            # the course_id could materialize at any time, and if so then we'll 
            # need to persist the value.
            if course.course_id is None and self.course_id is not None:
                try:
                    course.course_id = self.course_id
                    course.save()
                except ValidationError as err:
                    msg='LTISession.register_course() - could not update course_id of LTIExternalCourse for context_id {context_id}, course_id {course_id}.\r\nError: {err}.\r\n{traceback}'.format(
                        context_id=self.context_id,
                        course_id=course_id,
                        err=err,
                        traceback=traceback.format_exc()
                    )
                    log.error(msg)
                    return None
            else:
                # sneaky write to ensure integrity between context_id / course_id.
                #
                # Note: if for any reason there were a descrepency between course.course_id
                # and a not-null value of self.course_id, then we'll always assume
                # that course.course_id is the correct value.
                self._course_id = course.course_id

            return course 

        # Did not find a cached record. In order to proceed beyond this point we 
        # need to verify that lti_params is set and that we have a Rover course_id
        # to map to.
        if self.lti_params is None:
            if DEBUG: log.info('LTISession.register_course() - lti_params is not set. cannot cache. exiting.')
            return None
        if self.course_id is None:
            if DEBUG: log.info('LTISession.register_course() - course_id is not set. cannot cache. exiting.')
            return None

        params = LTIParamsFieldMap(lti_params=self.lti_params, table='LTIExternalCourse')
        date_str = params.custom_course_startat

        # FIX NOTE: this is a complete kluge. need to learn more about custom_course_startat
        # and then change this logic accordingly.
        if date_str is not None:
            date_str = date_str[0:10]
        else:
            date_str = "2019/01/01"

        custom_course_startat = parse_date(date_str)

        try:
            course = LTIExternalCourse(
                context_id = self.context_id,
                course_id = self.course_id,
                context_title = params.context_title,
                context_label = params.context_label,
                ext_wl_launch_key = params.ext_wl_launch_key,
                ext_wl_launch_url = params.ext_wl_launch_url,
                ext_wl_version = params.ext_wl_version,
                ext_wl_outcome_service_url = params.ext_wl_outcome_service_url,
                custom_api_domain = params.custom_api_domain,
                custom_course_id = params.custom_course_id,
                custom_course_startat = custom_course_startat,
                tool_consumer_info_product_family_code = params.tool_consumer_info_product_family_code,
                tool_consumer_info_version = params.tool_consumer_info_version,
                tool_consumer_instance_contact_email = params.tool_consumer_instance_contact_email,
                tool_consumer_instance_guid = params.tool_consumer_instance_guid,
                tool_consumer_instance_name = params.tool_consumer_instance_name,
            )
            
            course.save()

        except ValidationError as err:
            msg='LTISession.register_course() - could not save LTIExternalCourse record for context_id {context_id}, course_id {course_id}.\r\nError: {err}.\r\n{traceback}'.format(
                context_id=self.context_id,
                course_id=self.course_id,
                err=err,
                traceback=traceback.format_exc()
            )
            log.error(msg)
            return None

        if DEBUG: log.info('LTISession.register_course() - saved new cache record.')
        return course

    def register_enrollment(self):
        """try to retreive a cached enrollment record for the context_id / user
        otherwise, create a new record for the cache.
        
        Returns:
            [LTIExternalCourseEnrollment] -- the cached enrollment record for the student / course_id
        """
        if DEBUG: log.info('LTISession.register_enrollment()')

        if self.user is None:
            if DEBUG: log.info('LTISession.register_enrollment() - self.user is not set. exiting.')
            return None
        if self.course is None:
            if DEBUG: log.info('LTISession.register_enrollment() - self.course is not set. exiting.')
            return None

        # look for a cached record for this user / context_id
        enrollment = LTIExternalCourseEnrollment.objects.filter(
            course = self.course, 
            user = self.user
            ).first()
        if enrollment:
            # if we have a cached enrollment record then we know that we also have the parent course
            # record, where the course_id is stored.

            # set course enrollment
            self.course_enrollment = enrollment
            if DEBUG: log.info('LTISession.register_enrollment() - returning a cached enrollment record.')
            return enrollment

        if not CourseEnrollment.is_enrolled(self.user, self.course_id):
            if DEBUG: log.info('LTISession.register_enrollment() - learner is not enrolled in this course. exiting.')
            return None

        if not self.lti_params:
            if DEBUG: log.info('LTISession.register_enrollment() - lti_params is not set. partially populating enrollment record.')
            return None

        try:
            if self._lti_params:
                params = LTIParamsFieldMap(lti_params=self.lti_params, table='LTIExternalCourseEnrollment')
                enrollment = LTIExternalCourseEnrollment(
                    course = self.course,
                    user = self.user,
                    lti_user_id = self.user_id,

                    custom_user_id = params.custom_user_id,
                    custom_user_login_id = params.custom_user_login_id,
                    custom_person_timezone = params.custom_person_timezone,
                    ext_roles = params.ext_roles,
                    ext_wl_privacy_mode = params.ext_wl_privacy_mode,
                    lis_person_contact_email_primary = params.lis_person_contact_email_primary,
                    lis_person_name_family = params.lis_person_name_family,
                    lis_person_name_full = params.lis_person_name_full,
                    lis_person_name_given = params.lis_person_name_given,
                )
            else:
                enrollment = LTIExternalCourseEnrollment(
                    course = self.course,
                    user = self.user,
                    lti_user_id = self.user_id
                )

            enrollment.save()
        except ValidationError as err:
            msg='LTISession.register_enrollment() - could not save LTIExternalCourseEnrollment record for lti_user_id {lti_user_id}, username {username}.\r\nError: {err}.\r\n{traceback}'.format(
                lti_user_id=self.user_id,
                username=student.username,
                err=err,
                traceback=traceback.format_exc()
            )
            log.error(msg)
            return None

        if DEBUG: log.info('LTISession - register_enrollment() saved new cache record.')
        return enrollment

    def post_grades(self, usage_key, grades_dict):
        """Caches the grade data for one problem response. This is called each time a student
        submits an answer to a problem in LTI Grade Sync-enabled course.
        
        Arguments:
            usage_key {OpaqueKey} -- identifier for a problem of a Rover course. 
                                     corresponds to the homework problem that was just graded.
            grades_dict {dict} -- contains all fields from grades.models.PersistentSubsectionGrade
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
        
        Raises:
            LTIBusinessRuleError: [description]
        
        Returns:
            [Boolean] -- returns True if the Grades were posted.
        """
        if DEBUG: log.info('LTISession.post_grades() - usage_key: {usage_key}, grades: {grades_dict}'.format(
            usage_key=usage_key,
            grades_dict=grades_dict
        ))

        if self.course_enrollment is None:
            log.error('LTISession.post_grades() - self.course_enrollment is not set."')
            return False

        if self.user is None:
            log.error('LTISession.post_grades() - self.user is not set."')
            return False

        if self.course is None:
            log.error('LTISession.post_grades() - self.course is not set."')
            return False

        if not grades_dict['grades']['section_attempted_graded']:
            if DEBUG: log.info('no grade data to report. exiting.')
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
                    raise LTIBusinessRuleError("LTISession.post_grades() - Tried to pass an invalid usage_key: {key_type} {usage_key} ".format(
                            key_type=type(usage_key),
                            usage_key=usage_key
                        ))
        except:
            raise LTIBusinessRuleError("LTISession.post_grades() - Tried to pass an invalid usage_key: {key_type} {usage_key} ".format(
                    key_type=type(usage_key),
                    usage_key=usage_key
                ))
            return False

        curr = LTIExternalCourseEnrollmentGrades.objects.filter(
            course_enrollment = self.course_enrollment,
            section_url = grades_dict['url']
        ).order_by('-created').first()

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

        if not curr or\
            curr.earned_all != grades_dict['grades']['section_earned_all'] or\
            curr.possible_all != grades_dict['grades']['section_possible_all'] or\
            curr.earned_graded != grades_dict['grades']['section_earned_graded'] or\
            curr.possible_graded != grades_dict['grades']['section_possible_graded']:

            try:

                # cache the grade data
                grades = LTIExternalCourseEnrollmentGrades(
                    course_enrollment = self.course_enrollment,
                    course_assignment = assignment,
                    usage_key = usage_key,
                    section_url = grades_dict['url'],
                    earned_all = grades_dict['grades']['section_earned_all'],
                    possible_all = grades_dict['grades']['section_possible_all'],
                    earned_graded = grades_dict['grades']['section_earned_graded'],
                    possible_graded = grades_dict['grades']['section_possible_graded']
                )
                grades.save()

            except ValidationError as err:
                msg='LTISession.post_grades() - could not save LTIExternalCourseEnrollmentGrades record for usage_key {usage_key}, grades_dict {grades_dict}.\r\nError: {err}.\r\n{traceback}'.format(
                    usage_key=usage_key,
                    grades_dict=grades_dict,
                    err=err,
                    traceback=traceback.format_exc()
                )
                log.error(msg)
                return False

            if DEBUG: log.info('LTISession.post_grades() saved new cache record - username: {username}, '\
                'course_id: {course_id}, context_id: {context_id}, usage_key: {usage_key}, grades: {grades}'.format(
                username = self.user.username,
                usage_key = usage_key,
                course_id = self.course.course_id,
                context_id = self.course.context_id,
                grades = grades_dict
            ))
            return True
        else:
            if DEBUG: log.info('LTISession.post_grades() nothing new to record. exiting')
            return False

    #=========================================================================================================
    #                                       PROPERTIES SETTERS & GETTERS
    #=========================================================================================================
    def get_course_assignment_grade(self, usage_key):
        """Try to retrieve a cached course assignment grade object for the given usage_key (Opaque Key).
        
        Arguments:
            usage_key {OpaqueKey} -- add an example usage_key.
        
        Returns:
            [LTIExternalCourseEnrollmentGrades] -- the cache record corresponding to the usage_key
        """
        course_assignment = self.get_course_assignment(usage_key)

        if self.course_enrollment is None:
            log.error('LTISession.get_course_assignment_grade() - self.course_enrollment is not set."')
            return False

        if course_assignment is None:
            log.error('LTISession.get_course_assignment_grade() - course_assignment is not set."')
            return False

        grade = LTIExternalCourseEnrollmentGrades.objects.filter(
            course_enrollment = self.course_enrollment,
            course_assignment = course_assignment
        ).order_by('-created').first()

        if DEBUG: log.info('LTISession.get_course_assignment_grade() - course_enrollment: {course_enrollment}, course_assignment: {course_assignment}, usage_key: {usage_key}, key_type: {key_type}, grade: {grade}'.format(
            course_enrollment=self.course_enrollment,
            course_assignment=course_assignment,
            usage_key=usage_key,
            key_type=type(usage_key),
            grade=grade
        ))
        return grade

    def get_course_assignment(self, usage_key):
        """Try to retrieve a cached course assignment for the given usage_key (Opaque Key).
        
        Arguments:
            usage_key {OpaqueKey} -- add an example usage_key
        
        Returns:
            [LTIExternalCourseAssignments] -- the cache record corresponding to the usage_key
        """
        if DEBUG: log.info('LTISession.get_course_assignment() - usage_key: {usage_key} {key_type}'.format(
            usage_key=usage_key,
            key_type=type(usage_key)
        ))

        # try to find a cached problem record, then return its parent.
        problem = LTIExternalCourseAssignmentProblems.objects.filter(
            usage_key=usage_key
        ).order_by('-created').first()
        if problem:
            if DEBUG: log.info('LTISession.get_course_assignment() - returning the cached parent assignment object.\n\rproblem: {problem}\n\rassignment: {course_assignment}'.format(
                problem=problem,
                course_assignment=problem.course_assignment
            ))
            return problem.course_assignment

        # no problem record found, so look for the most recently-added assignment and
        # assume that this is where the student is currently working.
        #
        # FIX NOTE: there could be holes in this logic.
        assignment = LTIExternalCourseAssignments.objects.filter(
            course=self.course
        ).order_by('-created').first()
        if assignment:
            if DEBUG: log.info('LTISession.get_course_assignment() - returning most recently created cached assignment record.')
            return assignment

        if DEBUG: log.info('LTISession.get_course_assignment() - no record found.')
        return None

    def set_course_assignment(self, url, display_name):
        """Cache the given assignment URL.
        
        Arguments:
            url {string or url} -- a valid URL
            display_name {string} -- the visible text description of the Assignment in the course
        
        Returns:
            [LTIExternalCourseAssignments] -- the cache record corresponding to this url
        """
        if DEBUG: log.info('LTISession.set_course_assignment() - {url}, {display_name}'.format(
            url=url,
            display_name=display_name
        ))

        assignment = LTIExternalCourseAssignments.objects.filter(
            course = self.course,
            url = url
        ).first()

        if assignment:
            if DEBUG: log.info('LTISession.set_course_assignment() - returning a cached record.')
            return assignment

        if self.course is None:
            if DEBUG: log.info('LTISession.set_course_assignment() - self.course() returned None. Exiting.')
            return None

        # get the due_date for the assignment
        try:
            rover_course = get_course_by_id(self.course_id)
            unit = find_course_unit(rover_course, url)
            log.debug('LTISession.set_course_assignment() - found course unit: {unit}, due date: {due_date}'.format(
                unit=unit,
                due_date=unit.due
            ))
            due_date = unit.due
            if not due_date:
                log.info('LTISession.set_course_assignment() - WARNING: no due date for this assignment. Setting to far future.')
                due_date = datetime.datetime.now() + datetime.timedelta(days=365.25/2)

        except Exception as err:
            msg='LTISession.set_course_assignment() - error getting due date for display_name {display_name}, url {url}. Error: {err}.\r\n{traceback}'.format(
                display_name=display_name,
                url=url,
                err=err,
                traceback=traceback.format_exc()
            )
            log.error(msg)
            return None

        try:
            assignment = LTIExternalCourseAssignments(
                course = self.course,
                url = url,
                display_name = display_name,
                due_date = due_date
            )
            assignment.save()

        except ValidationError as err:
            msg='LTISession.set_course_assignment() - could not save LTIExternalCourseAssignments record for display_name {display_name}, url {url}. Error: {err}.\r\n{traceback}'.format(
                display_name=display_name,
                url=url,
                err=err,
                traceback=traceback.format_exc()
            )
            log.error(msg)
            return None

        if DEBUG: log.info('LTISession.set_course_assignment() - creating and returning a new record.')
        return assignment

    def get_course_assignment_problem(self, usage_key):
        """Try to retrieve a cached assignment problem.
        
        Arguments:
            usage_key {OpaqueKey} -- add an example usage_key
        
        Returns:
            [LTIExternalCourseAssignmentProblems] -- the cache record corresponding to this usage_key
        """
        problem = LTIExternalCourseAssignmentProblems.objects.filter(
            usage_key = usage_key
        )
        if problem:
            if DEBUG: log.info('LTISession.get_course_assignment_problem() - returning a cached record.')

        return problem

    def set_course_assignment_problem(self, course_assignment, usage_key):
        """cache an assignment problem.
        
        Arguments:
            course_assignment {LTIExternalCourseAssignment} -- the parent LTIExternalCourseAssignment
            usage_key {string} -- a string representation of an OpaqueKey
        
        Returns:
            LTIExternalCourseAssignmentProblems -- the cache record corresponding to the usage_key.
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

        try:
            problem = LTIExternalCourseAssignmentProblems(
                course_assignment = course_assignment,
                usage_key = usage_key
            )
            problem.save()

        except ValidationError as err:
            msg='LTISession.set_course_assignment_problem() - could not save LTIExternalCourseAssignmentProblems record for {course_assignment}, {usage_key}. Error: {err}.\r\n{traceback}'.format(
                course_assignment=course_assignment,
                usage_key=usage_key,
                err=err,
                traceback=traceback.format_exc()
            )
            log.error(msg)
            return None

        return problem

    @property
    def context_id(self):
        """Lazy reader implementation. If context_id has not been set
        then look for it in lti_params and/or course.
        
        Returns:
            [string] -- string value representing context_id
        """
        if DEBUG: log.info('LTISession.get_context_id() - {value}'.format(
            value=self._context_id
        ))
        if self._context_id is not None:
            return self._context_id

        # look for a context_id in lti_params, if its set.
        if self.lti_params is not None:
            self._context_id = self.lti_params.context_id
            return self._context_id

        # try to find a context_id from the course object, if its set.
        if self.course is not None:
            self._context_id = self.course.context_id
            return self._context_id
    
    @context_id.setter
    def context_id(self, value):
        """the context_id changed, so try re-initializing the course and 
        course_enrollment cache objects.
        
        Arguments:
            value {string} -- string value representing a context_id
        
        Raises:
            LTIBusinessRuleError: raises an error if the value provided is
            inconsistent with the value in lti_params or course.
        """
        if DEBUG: log.info('LTISession.set_context_id() - {value}'.format(
            value=value
        ))

        if value == self._context_id:
            if DEBUG: log.info('LTISession.set_context_id() - no changes. Exiting.')
            return 

        # check for integrity between context_id and the current contents of lti_params
        lti_params_context_id = self.lti_params.context_id
        if lti_params_context_id is not None and value != lti_params_context_id:
            raise LTIBusinessRuleError("set_context_id() - Tried to set context_id to {value}, which is inconsistent with the " \
                "current value of lti_params['context_id']: {lti_params}.".format(
                    value=value,
                    lti_params=self.lti_params.context_id
                ))

        # check for integrity between context_id and course.context_id        
        if self.course is not None:
            if self.course.context_id != value:
                raise LTIBusinessRuleError("set_context_id() - Tried to set context_id to {value}, which is inconsistent with the " \
                    "current value of course.context_id: {lti_params}.".format(
                        value=value,
                        lti_params=self.course.context_id
                    ))

        # need to clear all class properties to ensure integrity between lti_params values and whatever is
        # currently present in the cache.
        # mcdaniel feb-2020: FIX NOTE: do we need these??
        #self._course = None
        #self._course_enrollment = None
        #self._course_enrollment_grades = None
        #self._course_id = None


        self._context_id = value
    
    @property
    def lti_params(self):
        """lti_params getter
        
        Returns:
            dict -- lti_params dictionary
        """
        if DEBUG: log.info('LTISession.lti_params - {value}'.format(
            value = 'is set' if self._lti_params is not None else 'None'
        ))
        return self._lti_params

    @lti_params.setter
    def lti_params(self, value):
        """lti_params setter. lti_params json object changed, so clear course and course_enrollment
        also need to initialize any property values that are sourced from lti_params
        
        Arguments:
            value {LTIParams} -- a lti_params helper class
        
        Raises:
            LTIBusinessRuleError: raises an exception if lti_params is invalid.
        """
        if DEBUG: log.info('LTISession.set_lti_params()')

        if value is None:
            self._lti_params = None
        else:
            if isinstance(value, LTIParams):
                if value == self._lti_params:
                    return
                self._lti_params = value
            else:
                if isinstance(value, dict):
                    if self._lti_params is not None and value == self._lti_params.dictionary:
                        return
                    new_params = LTIParams(value)
                    if new_params.is_valid:
                        self._lti_params = new_params
                    else:
                        raise LTIBusinessRuleError('LTISession.set_lti_params() - received invalid lti_params.')


        # need to clear all class properties to ensure integrity between lti_params values and whatever is
        # currently present in the cache.
        #self.init()
        self._course = None
        self._course_enrollment = None
        self._course_enrollment_grades = None
        self._user = None
        self._course_id = None

        # property initializations from lti_params
        if self._lti_params is not None:
            self._context_id = self._lti_params.context_id          # uniquely identifies course in Willo
            self.user_id = self._lti_params.user_id                 # uniquely identifies user in Willo


    @property
    def user(self):
        """user getter
        
        Returns:
            User -- Django User object
        """
        if DEBUG: log.info('LTISession.get_user() - {value}'.format(
            value=self._user
        ))
        return self._user

    @user.setter
    def user(self, value):
        """user setter. the user object changed, so reinitialize any properties that are functions of user.
        also need to try to reinitialize course_enrollment.
        
        Arguments:
            value {User} -- a valid Django User object.
        """
        if DEBUG: log.info('LTISession.set_user()')

        if value == self._user:
            if DEBUG: log.info('LTISession.set_user() - no changes. Exiting.')
            return 

        self._user = value

        # initialize properties that depend on user
        self.is_faculty = is_faculty(self.user)

        # clear, and attempt to reinitialize the enrollment cache.
        self._course_enrollment = None

    @property
    def course_id(self):
        """course_id getter
        
        Returns:
            string -- a string value representing a course_id (CourseKey)
        """
        if DEBUG: log.info('LTISession.get_course_id() - {val}, {obj_type}'.format(
            val = self._course_id,
            obj_type = type(self._course_id)
        ))
        return self._course_id

    @course_id.setter
    def course_id(self, value):
        """course_id setter
        
        Arguments:
            value {string} -- a string representation of a CourseKey
        
        Raises:
            LTIBusinessRuleError: raises an excpetion if value is not a valid CourseKey
        """
        if DEBUG: log.info('LTISession.set_course_id() - {value}, {obj_type}'.format(
            value=value,
            obj_type=type(value)
        ))

        if value == self._course_id:
            if DEBUG: log.info('LTISession.set_course_id() - no changes. Exiting.')
            return 

        if isinstance(value, CourseKey):
            self._course_id = value
        else:
            if isinstance(value, str) or isinstance(value, unicode):
                self._course_id = CourseKey.from_string(value)
            else:
                raise LTIBusinessRuleError("LTISession.set_course_id() - Course_key provided is not a valid object type"\
                    " ({}). Must be either CourseKey or String.".format(
                    type(value)
            ))

        self._course = LTIExternalCourse.objects.filter(course_id=self._course_id).first()
        self._course_enrollment = None

    @property
    def course(self):
        """course getter. return a cached instance of the LTIExternalCourse record, if it exists.
        otherwise tries to register a new context_id/course_id course record
        
        Returns:
            LTIExternalCourse -- a course cache record.
        """
        if DEBUG: log.info('LTISession.get_course() - {value}'.format(
            value=self._course
        ))

        # try to return an instance, if we have one.
        if self._course is not None:
            return self._course

        return self._course

    @course.setter
    def course(self, value):
        """course setter
        
        Arguments:
            value {LTIExternalCourse} -- a course cache record.
        
        Raises:
            LTIBusinessRuleError: raises an exception if value is not an object of type LTIExternalCourse
        """
        if DEBUG: log.info('LTISession.set_course()')

        if value == self.course:
            if DEBUG: log.info('LTISession.set_course() - no changes. Exiting.')
            return 

        if not isinstance(value, LTIExternalCourse):
            raise LTIBusinessRuleError("set_course() - Tried to assign object {dtype} {obj} to course property that is not" \
                " an instance of third_party_auth.models.LTIExternalCourse.".format(
                    dtype=type(value),
                    obj=value
                ))

        self._course = value
        self._course_enrollment = None
        self._context_id = self._course.context_id

    @property
    def course_enrollment(self):
        """course_enrollment getter. Returns a cached instance of LTIExternalCourseEnrollment, if it exists.
        otherwise tries to register a new user / course record
        
        Returns:
            LTIExternalCourseEnrollment -- a cache record corresponding to user / context_id / course_id
        """
        if DEBUG: log.info('LTISession.get_course_enrollment() - {value}'.format(
            value=self._course_enrollment
        ))

        # try to return an instance, if we have one.
        if self._course_enrollment is not None:
            return self._course_enrollment

        # otherwise, try to retreive an instance from the cache, if it exists
        retval = self.register_enrollment()
        if retval:
            self.course_enrollment = retval

        return self._course_enrollment

    @course_enrollment.setter
    def course_enrollment(self, value):
        """course_enrollment setter.
        
        Arguments:
            value {LTIExternalCourseEnrollment} -- a course enrollment cache record
        
        Raises:
            LTIBusinessRuleError: raises an exception if value is not an object of type LTIExternalCourseEnrollment
        """
        msg = ' - course_enrollment: {value}, data type: {val_type}'.format(
            value=value,
            val_type=type(value)
        )
        if DEBUG: log.info('LTISession.set_course_enrollment()' + msg)
        
        if value == self._course_enrollment:
            if DEBUG: log.info('LTISession.set_course_enrollment() - no changes. Exiting.')
            return 

        if not isinstance(value, LTIExternalCourseEnrollment) and value is not None:
            msg = "LTISession.set_course_enrollment() - Tried to assign an object to course_enrollment property that is not" \
                " an instance of third_party_auth.models.LTIExternalCourseEnrollment." \
                + msg
            raise LTIBusinessRuleError(msg)

        self._course_enrollment = value


    #context_id = property(get_context_id, set_context_id)
    #lti_params = property(get_lti_params, set_lti_params)
    #user = property(get_user, set_user)
    #course_id = property(get_course_id, set_course_id)
    #course = property(get_course, set_course)
    #course_enrollment = property(get_course_enrollment, set_course_enrollment)