# -*- coding: utf-8 -*-
"""
Willo Labs real-time Grade Sync

Written by: mcdaniel
            https://lawrencemcdaniel.com
            lpm0073@gmail.com

Date:       jan-2020
"""

import logging
from datetime import datetime
import pytz
import traceback

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from celery.task import task
from celery.exceptions import SoftTimeLimitExceeded
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask
#from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError
from lms.djangoapps.grades.api.v2.utils import parent_usagekey

from opaque_keys.edx.keys import CourseKey, UsageKey

# for Willo api
from .exceptions import DatabaseNotReadyError, LTIBusinessRuleError
from .cache import LTISession
from .utils import willo_id_from_url
from .api import (
    willo_api_post_grade,
    willo_api_create_column,
    willo_activity_id_from_string,
    willo_date
    )


log = logging.getLogger(__name__)
#log = get_task_logger(__name__)

KNOWN_RETRY_ERRORS = (  # Errors we expect occasionally, should be resolved on retry
    DatabaseError,
    ValidationError,
    DatabaseNotReadyError,
)
RECALCULATE_GRADE_DELAY_SECONDS = 5  # to prevent excessive _has_db_updated failures. See TNL-6424.
RETRY_DELAY_SECONDS = 40
TIMEOUT_SECONDS = 300
TASK_TIME_LIMIT = 60
TASK_SOFT_TIME_LIMIT = 50
MAX_RETRIES = 1


@task(
    bind=True,
    base=LoggedPersistOnFailureTask,
    time_limit=TIMEOUT_SECONDS,
    max_retries = MAX_RETRIES,
    default_retry_delay=RETRY_DELAY_SECONDS,
    routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY,        # edx.lms.core.default

    acks_late=True,
    task_time_limit=TASK_TIME_LIMIT, 
    task_soft_time_limit=TASK_SOFT_TIME_LIMIT,
    )
def post_grades(self, username, course_id, usage_id):
    """ see docstring for _post_grades() """

    _post_grades(
        self, 
        username=username,
        course_id=course_id,
        usage_id=usage_id
    )

def _post_grades(self, username, course_id, usage_id):
    """
        username: a string
        course_id: a string identifier for a CourseKey
        usage_id: a string identifier for a UsageKey

    Post Rover grade data to a Willo Labs external platform via LTI integration.
    This task is called from lms/djangoapps/grades/tasks.py
	    recalculate_subsection_grade_v3()
    The grading process is executed real-time, each time a learner submits a problem.

    Note: the grader program sends us a usage_id corresponding to the problem that was just graded.
    But we need to use this usage_id to locate the UsageKey corresponding to the homework exercise in 
    which this problem is contained. 


    @task:
    ------
    bind: 
    retry_limit: post_grades will be attempted this many time before failing.
    default_retry_delay: wait interval between attempts, in seconds.
    acks_late: 

    Return value:
        failure_messages: List of error messages for the providers that could not be updated
    """
    try:
        log.debug('_post_grades() - username: {username}, course_id: {course_id}, usage_id: {usage_id}'.format(
            username=username,
            course_id=course_id,
            usage_id=usage_id
        ))

        # reinstantiate our local class variables
        user = get_user_model().objects.get(username=username)
        course_key = CourseKey.from_string(course_id)
        problem_usage_key = UsageKey.from_string(usage_id)
        session = LTISession(user=user, course_id=course_id)

        lti_cached_course = session.course
        if lti_cached_course is None:
            raise LTIBusinessRuleError('Tried to call Willo api with partially initialized LTI session object. course property is not set.')

        lti_cached_assignment = session.get_course_assignment(problem_usage_key)

        # Note: this is scaffolding that will
        # facilitate a faster, cached grade post operation
        # once we learn more about how to pull cached
        # grade data from Block Store structures.
        homework_assignment_dict = parent_usagekey(
            user,
            course_key = course_key,
            usage_key = problem_usage_key
            )

        if lti_cached_assignment is None:
            log.error('Tried to call Willo api with partially initialized LTI session object. course assignment property is not set.')

        lti_cached_enrollment = session.get_course_enrollment()
        if lti_cached_enrollment is None:
            log.error('Tried to call Willo api with partially initialized LTI session object. enrollment property is not set.')

        # Cache the grade data
        session.post_grades(
            usage_key=problem_usage_key, 
            grades_dict=homework_assignment_dict
            )

        lti_cached_grade = session.get_course_assignment_grade(problem_usage_key)
        if lti_cached_grade is None:
            log.error('Tried to call Willo api with partially initialized LTI session object. grades property is not set for usagekey {usage_key}.'.format(
                usage_key=problem_usage_key
            ))

        # Push grades to Willo grade sync
        retval = create_column(self, lti_cached_course, lti_cached_assignment, lti_cached_grade)
        if retval:
            retval = post_grade(self, lti_cached_course, lti_cached_enrollment, lti_cached_assignment, lti_cached_grade)
        
        return retval

    except Exception as exc:
        if not isinstance(exc, KNOWN_RETRY_ERRORS):
            log.error("willolabs.tasks.post_grades() unexpected failure: {exc}. task id: {req}.".format(
                exc=repr(exc),
                req=self.request.id,
            ))
        else:
            log.error('willolabs.tasks.post_grades() - retrying')
        raise self.retry(exc=exc)

    except SoftTimeLimitExceeded:
        self.recover_from_exceeded_time_limit()


def recover_from_exceeded_time_limit(self):
    """
    Scaffold, to take care of anything that needs cleaning up 
    after the task timed-out.
    """
    log.error('willolabs.tasks.recover_from_exceeded_time_limit()')
    return None

def create_column(self, lti_cached_course, lti_cached_assignment, lti_cached_grade):
    """Willo Grade Sync api - Add a new grade column to the LMS grade book. 
     Prepare and send a data payload to post to the Willo Labs Grade Sync api.
     Read more: https://readthedocs.roverbyopenstax.org/en/latest/developer_zone/edx-platform/willo_gradesync.html
    
    Arguments:
        lti_cached_course {[LTIExternalCourse]} -- The Rover course that is linked
        via LTI authentication using the lti_params dict. LTIExternalCourse
        records the 1:1 relationship between LTI context_id and Rover course_key.
        Also stores the URL pointing to the Willo Labs grade sync endpoint for
        grade data for the course. See ext_wl_outcome_service_url. Example: 
        https://app.willolabs.com/api/v1/outcomes/DKGSf3/e42f27081648428f8995b1bca2e794ad/

        lti_cached_assignment {[LTIExternalCourseAssignments]} -- assignment records
        are created automatically in real-time, as students submit answers to homework
        problems. LTIExternalCourseAssignments stores the assignment URL and Display
        name, along with the parent relationship back to LTIExternalCourse.

        lti_cached_grade {[LTIExternalCourseEnrollmentGrades]} -- records the
        grade dict data for one student response to one assignment problem.
    
    Returns:
        [Boolean] -- returns True if the return code is 200 or 201, False otherwise.
    """

    try:
        
        data = {
            "type": "activity",				
            "id": str(lti_cached_assignment.id),	                ## bigint. example: 1234567890
            "title": lti_cached_assignment.display_name,	        ## example: Getting to Know Rover Review Assignment
            "description": lti_cached_assignment.display_name,	    ## example: Getting to Know Rover Review Assignment
            "due_date": lti_cached_assignment.due_date.isoformat(), ## Rover assignment due_date in ISO string format: 2019-06-01T00:00:00+04:00
            "points_possible": lti_cached_grade.possible_graded     ## int. example: 11
        }

    except Exception as err:
        log.error('willolabs.tasks.create_column() - error preparing grade column data for Willo Labs api:\r\n{err}.\r\n{traceback}'.format(
            err=err,
            traceback=traceback.format_exc()
        ))
        return False

    log.info('willolabs.tasks.create_column() - assignment: {assignment} data: {data}'.format(
        assignment=lti_cached_assignment.display_name,
        data=data
    ))

    return willo_api_create_column(
        lti_cached_course.ext_wl_outcome_service_url, 
        data
        )


def post_grade(self, lti_cached_course, lti_cached_enrollment, lti_cached_assignment, lti_cached_grade):
    """Willo Grade Sync api. Post grade scored for one student, for one homework assignment.
    Willo api returns 200 if the grade was posted. Example ext_wl_outcome_service_url:
    'https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/'
    Read more: https://readthedocs.roverbyopenstax.org/en/latest/developer_zone/edx-platform/willo_gradesync.html

    
    Arguments:
        lti_cached_course {[LTIExternalCourse]} -- The Rover course that is linked
        via LTI authentication using the lti_params dict. LTIExternalCourse
        records the 1:1 relationship between LTI context_id and Rover course_key.

        lti_cached_enrollment {[type]} -- [description]

        lti_cached_assignment {[LTIExternalCourseAssignments]} -- assignment records
        are created automatically in real-time, as students submit answers to homework
        problems. LTIExternalCourseAssignments stores the assignment URL and Display
        name, along with the parent relationship back to LTIExternalCourse.

        lti_cached_grade {[LTIExternalCourseEnrollmentGrades]} -- records the
        grade dict data for one student response to one assignment problem.
    
    Returns:
        [Boolean] -- returns True if the return code is 200, False otherwise.
    """
    log.info('willolabs.tasks.post_grade()')

    try:

        data = {
            "type": "result",
            "id": willo_id_from_url(lti_cached_assignment.url),
            "activity_id": willo_activity_id_from_string(lti_cached_assignment.display_name),
            "user_id": lti_cached_enrollment.lti_user_id,
            "result_date": willo_date(lti_cached_grade.created),
            "score": lti_cached_grade.earned_graded,
            "points_possible": lti_cached_grade.possible_graded
        }

    except Exception as e:
        log.error('willolabs.tasks.post_grade() - error preparing grade data for Willo Labs api: {err}'.format(
            err=e
        ))
        return False


    log.info('willolabs.tasks.post_grade() - data: {data}'.format(
        data=data
    ))

    return willo_api_post_grade(
        lti_cached_course.ext_wl_outcome_service_url,
        data
    )
