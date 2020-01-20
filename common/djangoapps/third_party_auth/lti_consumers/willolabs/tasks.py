# -*- coding: utf-8 -*-
"""
Code to manage Willo Labs Grade Sync
"""

from celery.task import task
from celery.exceptions import SoftTimeLimitExceeded
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask
from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError
from common.djangoapps.third_party_auth.lti_consumers.willolabs.exceptions import DatabaseNotReadyError
from common.djangoapps.third_party_auth.lti_consumers.willolabs.models import (
    LTIExternalCourse, 
    LTIExternalCourseEnrollment    
)
from common.djangoapps.third_party_auth.lti_consumers.willolabs.cache import LTISession
from lms.djangoapps.grades.api.v2.utils import parent_usagekey

from opaque_keys.edx.keys import CourseKey, UsageKey
from django.conf import settings

# for Willo api
import requests
import json
from datetime import datetime
import pytz
from exceptions import LTIBusinessRuleError

import logging
log = logging.getLogger(__name__)
#log = get_task_logger(__name__)

KNOWN_RETRY_ERRORS = (  # Errors we expect occasionally, should be resolved on retry
    DatabaseError,
    ValidationError,
    DatabaseNotReadyError,
)
RECALCULATE_GRADE_DELAY_SECONDS = 2  # to prevent excessive _has_db_updated failures. See TNL-6424.
RETRY_DELAY_SECONDS = 40
TIMEOUT_SECONDS = 300
TASK_TIME_LIMIT = 60
TASK_SOFT_TIME_LIMIT = 50
MAX_RETRIES = 5


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
    # create a few local class variables
    try:
        if settings.DEBUG:
            log.info('_post_grades() - username: {username}, course_id: {course_id}, usage_id: {usage_id}'.format(
                username=username,
                course_id=course_id,
                usage_id=usage_id
            ))
        user = get_user_model().objects.get(username=username)
        course_key = CourseKey.from_string(course_id)
        problem_usage_key = UsageKey.from_string(usage_id)
        session = LTISession(user = user, course_id = course_id)

        lti_cached_course = session.get_course()
        if lti_cached_course is None:
            raise LTIBusinessRuleError('Tried to call Willo api with partially initialized LTI session object. course property is not set.')

        lti_cached_assignment = session.get_course_assignment(problem_usage_key)

        # Note: this is scaffolding that will
        # faciliate a faster, cached grade post operation
        # once we learn more about how to pull cached
        # grade data from Block Store structures.
        if lti_cached_assignment is not None:
            # do something fast (someday).
            homework_assignment_dict = parent_usagekey(
                user,
                course_key = course_key,
                usage_key = problem_usage_key
                )
            
        else:
            # do something slow.
            # Note: very slow, high-overhead function call. 
            # this data might be (probably is) cached, so look there first.
            homework_assignment_dict = parent_usagekey(
                user,
                course_key = course_key,
                usage_key = problem_usage_key
                )

        if lti_cached_assignment is None:
            raise LTIBusinessRuleError('Tried to call Willo api with partially initialized LTI session object. course assignment property is not set.')

        lti_cached_enrollment = session.get_course_enrollment()
        if lti_cached_enrollment is None:
            raise LTIBusinessRuleError('Tried to call Willo api with partially initialized LTI session object. enrollment property is not set.')

        lti_cached_grade = session.get_course_assignment_grade(problem_usage_key)
        if lti_cached_grade is None:
            raise LTIBusinessRuleError('Tried to call Willo api with partially initialized LTI session object. grades property is not set for usagekey {usage_key}.'.format(
                usage_key=problem_usage_key
            ))


        session.post_grades(
            usage_key=problem_usage_key, 
            grades_dict=homework_assignment_dict
            )

        # Push grades to Willo grade sync
        willo_api_create_column(
            self, 
            lti_cached_course, 
            lti_cached_assignment,
            lti_cached_grade
            )

        willo_api_post_grade(
            self, 
            lti_cached_course, 
            lti_cached_enrollment,
            lti_cached_assignment, 
            lti_cached_grade
            )

        willo_api_get(
            self, 
            url = lti_cached_course.ext_wl_outcome_service_url,
            assignment_id = str(lti_cached_assignment.id),
            user_id = lti_cached_enrollment.lti_user_id
        )

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

"""
    Canvas via Willo Integration:
    ===================
    https://willowlabs.instructure.com/
    un: rover_teach
    pw: WilloTest1

    https://willowlabs.instructure.com/
    un: rover_learner
    pw: WilloTest1

 Willo api methods.

    Gist:  https://gist.github.com/matthanger-willo/4ab620e811c6da7c4412271945d85a6c
    Docs:  https://docs.google.com/document/d/1Q_dRXEpHnzWFti2j8R5CNtgOVIDMBXfRXWbf4fSHvBE/edit

    Create a column in LMS grade book
    -------------------------
    curl -v -X POST https://stage.willolabs.com/api/v1/outcomes/BBKQyB/4469701c1aad450891edf449942cb25b/ \
        -H "Content-Type: application/vnd.willolabs.outcome.activity+json" \
        -H "Authorization: Token sampleaccesstoken" \
        -d \
    '{
        "type": "activity",
        "id": "tutorial-avoiding-plagiarism",
        "title": "Tutorial: Avoiding Plagiarism",
        "description": "sample description",
        "due_date": "2019-06-01T00:00:00+04:00",
        "points_possible": 100
    }'

    Push grades for a student
    -------------------------
    curl -v -X POST https://stage.willolabs.com/api/v1/outcomes/BBKQyB/4469701c1aad450891edf449942cb25b/ \
        -H "Content-Type: application/vnd.willolabs.outcome.result+json" \
        -H "Authorization: Token sampleaccesstoken" \
        -d \
    '{
        "type": "result",
        "id": "8627ec7e1215413385f10b20d0dde4f0",
        "activity_id": "tutorial-avoiding-plagiarism",
        "user_id": "523bd4baaf772a615a478397d560a1591c7e3347",
        "result_date": "2019-05-04T16:59:01.938229+00:00",
        "score": 100,
        "points_possible": 100
    }'

    Get grade received by one student for one assignment
    -------------------------
    curl -v -X GET "https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/?id=tutorial-avoiding-plagiarism&user_id=523bd4baaf772a615a478397d560a1591c7e3347" \
        -H "Accept: application/vnd.willolabs.outcome.result+json" \
        -H "Authorization: Token qHT28EAgrxag3AjyM3ZQmUYemBQeTy82eRC8hdua"

"""
def willo_api_create_column(self, lti_cached_course, lti_cached_assignment, lti_cached_grade):
    """
     Willo Grade Sync api.
     Add a new grade column to the LMS grade book. 
     returns True if the return code is 200 or 201, False otherwise.
    """
    if settings.DEBUG:
        log.info('willo_api_create_column() - assignment: {assignment}'.format(
            assignment=lti_cached_assignment.display_name
        ))

    # Example: 'https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/'
    url = lti_cached_course.ext_wl_outcome_service_url

    # FIX ME!!!!
    due_date = datetime.now(tz=pytz.utc).isoformat()
    #due_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%Z")   # https://docs.python.org/3/library/datetime.html
    
    headers = willo_api_headers(
        self,
        key = 'Content-Type',
        value = 'application/vnd.willolabs.outcome.activity+json'
        )
    data = {
        "type": "activity",				
        "id": str(lti_cached_assignment.id),	                ## bigint. example: 1234567890
        "title": lti_cached_assignment.display_name,	        ## example: Getting to Know Rover Review Assignment
        "description": lti_cached_assignment.display_name,	    ## example: Getting to Know Rover Review Assignment
        "due_date": due_date,                                   ## FIX ME!!!!!
        "points_possible": lti_cached_grade.possible_graded     ## int. example: 11
    }
    data_json = json.dumps(data)

    response = requests.post(url, data=data_json, headers=headers)
    if 200 <= response.status_code <= 299:
        if response.status_code == 200:
            if settings.DEBUG:
                log.info('willo_api_create_column() - successfully created grade column: {grade_column_data}'.format(
                    grade_column_data = data_json
                ))
        return True
    else:
        log.error('willo_api_create_column() - encountered an error while attempting to create a new grade column: {grade_column_data}, which generated the following response: {response}'.format(
            grade_column_data = data_json,
            response = response.status_code
        ))
        return False

    return False


def willo_api_post_grade(self, lti_cached_course, lti_cached_enrollment, lti_cached_assignment, lti_cached_grade):
    """
     Willo Grade Sync api.
     post grade scored for one student, for one homework assignment.
     Willo api returns 200 if the grade was posted.
     returns True if the return code is 200, False otherwise.
    """
    if settings.DEBUG: log.info('willo_api_post_grade()')

    # Example: 'https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/'
    url = lti_cached_course.ext_wl_outcome_service_url
    headers = willo_api_headers(
        self,
        key='Content-Type',
        value='application/vnd.willolabs.outcome.result+json'
        )
    data = {
        "type": "result",
        "id": str(lti_cached_grade.usage_key),
        "activity_id": str(lti_cached_assignment.id),
        "user_id": lti_cached_enrollment.lti_user_id,
        "result_date": lti_cached_grade.created.strftime("%Y-%m-%dT%H:%M:%S%Z"),
        "score": lti_cached_grade.earned_graded,
        "points_possible": lti_cached_grade.possible_graded
    }
    data_json = json.dumps(data)

    response = requests.post(url, data=data_json, headers=headers)
    if 200 <= response.status_code <= 299:
        if settings.DEBUG:
            log.info('willo_api_post_grade() - successfully posted grade data: {grade_data}'.format(
                grade_data = data_json
            ))
        return True
    else:
        log.error('willo_api_post_grade() - encountered an error while attempting to post the following grade: {grade_data} which generated the following response: {response}'.format(
            grade_data = data_json,
            response = response.status_code
        ))
        return False

    return False

    

def willo_api_get(self, url, assignment_id, user_id):
    """
     Willo Grade Sync api.
     Retrieve a grade record (list) for one student for one assignment
     returns http response as a json dict
    """
    if settings.DEBUG: log.info('willo_api_get()')

    params = {
        'id' : assignment_id,
        'user_id' : user_id
        }
    headers = willo_api_headers(
        self,
        key='Accept',
        value='application/vnd.willolabs.outcome.result+json'
        )

    response = requests.get(url=url, params=params, headers=headers)
    if response.status_code == 200:
        if settings.DEBUG:
            log.info('willo_api_get() - successfully retrieved grade data for user_id: {user_id}, assignment id: {assignment_id}. The response was: {response}'.format(
                assignment_id = assignment_id,
                user_id = user_id,
                response = response.json()
            ))
        return response.json()
    else:
        log.error('willo_api_get() - encountered an error while attempting to retrieve grade data for user_id: {user_id}, assignment id: {assignment_id}. The response was: {response}'.format(
            assignment_id = assignment_id,
            user_id = user_id,
            response = response.status_code
        ))

    return None


def willo_api_authorization_token(self):
    """
     Returns a Willo Labs api authentication token
     example: qHT28EAgrxa1234567890abcdefghij2eRC8hdua
    """
    if settings.DEBUG: log.info('willo_api_authorization_token()')

    token = settings.WILLO_API_AUTHORIZATION_TOKEN
    return token

def willo_api_headers(self, key, value):
    """
     returns a Willo api request header
    """
    headers = {}
    headers['Authorization'] = 'Token {secret}'.format(
            secret = willo_api_authorization_token(self)
        )
    headers[key] = value

    if settings.DEBUG:
        log.info('willo_api_headers() - {headers}'.format(
            headers = json.dumps(headers)
        ))

    return headers

