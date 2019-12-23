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

import logging
#app_log = logging.getLogger(__name__)
app_log = get_task_logger(__name__)


"""
import requests
from requests import exceptions
from six import text_type

import datetime
import pytz
import dateutil.parser
from django.utils.timezone import now
"""

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

        user = get_user_model().objects.get(username=username)
        problem_usage_key = UsageKey.from_string(usage_id)

        homework_usage_key = parent_usagekey(
            user,
            course_id = course_id,
            usage_key_string = problem_usage_key
            )
        session = LTISession(user = user, course_id = course_id)
        course = LTIExternalCourse.objects.filter(course_id=CourseKey.from_string(course_id)).first()
        session.set_course(course)

        course_enrollment = LTIExternalCourseEnrollment.objects.filter(
            context_id = course.context_id, 
            user = user
            ).first()
        session.set_course_enrollment(course_enrollment)

        session.post_grades(usage_key=problem_usage_key)

    except Exception as exc:
        if not isinstance(exc, KNOWN_RETRY_ERRORS):
            app_log.error("willolabs.tasks.post_grades() unexpected failure: {exc}. task id: {req}.".format(
                exc=repr(exc),
                req=self.request.id,
            ))
        else:
            app_log.info('willolabs.tasks.post_grades() - retrying')
        raise self.retry(exc=exc)

    except SoftTimeLimitExceeded:
        self.recover_from_exceeded_time_limit()


def recover_from_exceeded_time_limit(self):
    """
    Scaffold, to take care of anything that needs cleaning up 
    after the task timed-out.
    """
    app_log.info('willolabs.tasks.recover_from_exceeded_time_limit()')
    return None
