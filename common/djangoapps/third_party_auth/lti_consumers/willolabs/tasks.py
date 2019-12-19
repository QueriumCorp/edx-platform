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

from opaque_keys.edx.keys import CourseKey

import logging
app_log = logging.getLogger(__name__)
celery_log = get_task_logger(__name__)


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
    routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY,

    acks_late=True,
    task_time_limit=TASK_TIME_LIMIT, 
    task_soft_time_limit=TASK_SOFT_TIME_LIMIT,
    )
def post_grades(self, username, course_id, subsection_usage_key, subsection_grade):
    """ see docstring for _post_grades() """

    _post_grades(
        self, 
        username=username,
        course_id=course_id,
        subsection_usage_key=subsection_usage_key,
        subsection_grade=subsection_grade
    )

def _post_grades(self, username, course_id, subsection_usage_key, subsection_grade):
    """
    Post Rover grade data to a Willo Labs external platform via LTI integration.
    This task is called from lms/djangoapps/grades/tasks.py
	    recalculate_subsection_grade_v3()
    The grading process is executed real-time, each time a learner submits a problem.

    @task:
    ------
    bind: 
    retry_limit: post_grades will be attempted this many time before failing.
    default_retry_delay: wait interval between attempts, in seconds.
    acks_late: 

    Return value:
        failure_messages: List of error messages for the providers that could not be updated
    """
    self.user = get_user_model().objects.get(username=username)
    self.course_key = CourseKey.from_string(course_id)
    self.subsection_usage_key = subsection_usage_key
    self.subsection_grade = subsection_grade

    # create a few local class variables
    try:
        """
        perform our tasks ...
        """

        log(self, 'willolabs.tasks.post_grades() - starting')

        x = 1 + 1

        log(self, 'willolabs.tasks.post_grades() - finished')

    except Exception as exc:
        if not isinstance(exc, KNOWN_RETRY_ERRORS):
            log(self, "willolabs.tasks.post_grades() unexpected failure: {exc}. task id: {req}.".format(
                exc=repr(exc),
                req=self.request.id,
            ))
        else:
            log(self, 'willolabs.tasks.post_grades() - retrying')
        raise self.retry(exc=exc)

    except SoftTimeLimitExceeded:
        self.recover_from_exceeded_time_limit()


def recover_from_exceeded_time_limit(self):
    """
    Scaffold, to take care of anything that needs cleaning up 
    after the task timed-out.
    """
    log(self, 'willolabs.tasks.recover_from_exceeded_time_limit()')
    return None

def log(self, msg, exc=None):

    msg += ". task id: {id}, "\
        "user: {username}, "\
        "course_key: {course_key}, "\
        "subsection_usage_key: {subsection_usage_key}, "\
        "subsection_grade: {subsection_grade}, "\
        "".format(
        id = self.request.id,
        username = self.user.username,
        course_key = self.course_key,
        subsection_usage_key = self.subsection_usage_key,
        subsection_grade = self.subsection_grade,
    )

    if exc is not None:
        msg += " error: {err}".format(
            err = repr(exc)
        )

        #app_log.error(msg)
        celery_log.error(msg)
    else:
        #app_log.info(msg)
        celery_log.info(msg)

    return None