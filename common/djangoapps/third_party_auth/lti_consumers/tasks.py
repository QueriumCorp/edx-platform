# -*- coding: utf-8 -*-
"""
LTI Grade Sync

Written by: mcdaniel
            https://lawrencemcdaniel.com
            lpm0073@gmail.com

Date:       jan-2020
"""

import logging
import datetime
import pytz
import traceback

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from celery.task import task
from celery.exceptions import SoftTimeLimitExceeded
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError

from opaque_keys.edx.keys import CourseKey, UsageKey

# for LTI Grade Sync api
from .exceptions import DatabaseNotReadyError, LTIBusinessRuleError
from .cache import LTICacheManager
from .utils import willo_id_from_url, get_subsection_chapter
from .api import (
    willo_api_post_grade,
    willo_api_create_column,
    willo_activity_id_from_string,
    willo_date
    )

# to retrieve assignment grade
from xmodule.modulestore.django import modulestore
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.grades.transformer import GradesTransformer
from lms.djangoapps.grades.subsection_grade_factory import SubsectionGradeFactory

# mcdaniel dec-2020
# Calstatela Fall 2020 midterm3 patch
CALSTATELA_MIDTERM3_PATCH = True
if CALSTATELA_MIDTERM3_PATCH:
    try:
        from .patches.calstatela_2020midterm3_patch_001 import (
            CALSTATELA_MIDTERM3_ASSIGNMENTS,
            CALSTATELA_MIDTERM3_COURSE_KEYS,
            calstatela_midterm3_patch_column, 
            calstatela_midterm3_patch_grade
            )
    except:
        CALSTATELA_MIDTERM3_PATCH = False
        pass


log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG

UTC = pytz.UTC

KNOWN_RETRY_ERRORS = (  # Errors we expect occasionally, should be resolved on retry
    DatabaseError,
    ValidationError,
    DatabaseNotReadyError,
)
RECALCULATE_GRADE_DELAY_SECONDS = 5  # to prevent excessive _has_db_updated failures. See TNL-6424.
RETRY_DELAY_SECONDS = 40
TIMEOUT_SECONDS = 600
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
    username: a string representing the User.username of the student
    course_id: a string identifier for a CourseKey
    usage_id: a string identifier for a UsageKey. Identifies the problem that was just submitted and graded.


    Post Rover grade data to an LTI Consumer platform via LTI integration.
    This task is called from lms/djangoapps/grades/tasks.py
	    recalculate_subsection_grade_v3()
    The grading process is executed real-time, each time a learner submits a problem.

    Note: the grader program sends us a usage_id corresponding to the problem that was just graded.
    But we need to use this usage_id to locate the UsageKey corresponding to the assignment in
    which this problem is contained.

    Return value:
        failure_messages: List of error messages for the providers that could not be updated
    """

    log.info('_post_grades() - username: {username}, course_id: {course_id}, usage_id: {usage_id}'.format(
        username=username,
        course_id=course_id,
        usage_id=usage_id
    ))

    try:

        # re-instantiate our class objects
        student = User.objects.get(username=username)
        course_key = CourseKey.from_string(course_id)
        problem_usage_key = UsageKey.from_string(usage_id)
        session = LTICacheManager(user=student, course_id=course_id)

        lti_cached_course = session.course
        if lti_cached_course is None:
            log.error('Tried to call LTI Consumer api with partially initialized LTI session object. course property is not set. username: {username}, course_id: {course_id}, usage_id: {usage_id}'.format(
                username=username,
                course_id=course_id,
                usage_id=usage_id
            ))
            return False

        lti_cached_enrollment = session.course_enrollment
        if lti_cached_enrollment is None:
            log.error('Tried to call LTI Consumer api with partially initialized LTI session object. enrollment property is not set. username: {username}, course_id: {course_id}, usage_id: {usage_id}'.format(
                username=username,
                course_id=course_id,
                usage_id=usage_id
            ))
            return False

        subsection_grade = get_subsection_grade(student, course_key, problem_usage_key)
        if subsection_grade is None:
            return False

        homework_assignment_dict = get_assignment_grade(
            course_key=course_key,
            problem_usage_key=problem_usage_key,
            subsection_grade=subsection_grade
            )

        # Cache the grade data
        session.post_grades(
            usage_key=problem_usage_key,
            grades_dict=homework_assignment_dict
            )

        lti_cached_assignment = session.get_course_assignment(problem_usage_key)
        if lti_cached_assignment is None:
            log.error('Tried to call LTI Consumer api with partially initialized LTI session object. course assignment property is not set. username: {username}, course_id: {course_id}, usage_id: {usage_id}, problem_usage_key: {problem_usage_key}, homework_assignment_dict: {homework_assignment_dict}'.format(
                usage_key=problem_usage_key,
                username=username,
                course_id=course_id,
                usage_id=usage_id,
                homework_assignment_dict=homework_assignment_dict
            ))
            return False

        lti_cached_grade = session.get_course_assignment_grade(problem_usage_key)
        if lti_cached_grade is None:
            log.error('Tried to call LTI Consumer api with partially initialized LTI session object. grades property is not set for usagekey {usage_key}. username: {username}, course_id: {course_id}, usage_id: {usage_id}, homework_assignment_dict: {homework_assignment_dict}'.format(
                usage_key=problem_usage_key,
                username=username,
                course_id=course_id,
                usage_id=usage_id,
                homework_assignment_dict=homework_assignment_dict
            ))
            return False

        if not lti_cached_course.enabled:
            log.info('LTI Consumer API Grade Sync is not enabled for course {coursekey}. Grade was locally cached for problem {usage_key} but it will not be posted to Willo Labs API.'.format(
                coursekey=lti_cached_course.course_id,
                usage_key=problem_usage_key
            ))
            return True

        # Push grades to LTI Grade Sync
        retval = create_column(
            self,
            lti_cached_course=lti_cached_course,
            lti_cached_assignment=lti_cached_assignment,
            lti_cached_grade=lti_cached_grade
            )
        if retval:
            retval = post_grade(
                self,
                lti_cached_course=lti_cached_course,
                lti_cached_enrollment=lti_cached_enrollment,
                lti_cached_assignment=lti_cached_assignment,
                lti_cached_grade=lti_cached_grade
                )

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

def get_subsection_grade(student, course_key, problem_usage_key):
    """the code pattern that follow originates from lms.djangoapps.grades.tasks._update_subsection_grades()
    the object we need -- subsection_grade -- is recreated here rather than passed from _update_subsection_grades()
    in order to avoid passing a potentially large chunky object thru Celery.

    notes:
    subsection_grade.graded_total: <common.lib.xmodule.xmodule.graders.AggregatedScore>
    from xmodule.graders import AggregatedScore

    AggregatedScore({'first_attempted': datetime.datetime(2020, 1, 17, 20, 33, 14, 114130, tzinfo=<UTC>), 'graded': True, 'possible': 11.0, 'earned': 11.0})
    subsection_grade.graded_total.__dict__: {'first_attempted': datetime.datetime(2020, 1, 17, 20, 33, 14, 114130, tzinfo=<UTC>), 'graded': True, 'possible': 11.0, 'earned': 11.0}


    Parameters:
        student = User
        course_key = CourseKey
        problem_usage_key = UsageKey

    Returns:
        subsection_grade: lms.djangoapps.grades.subsection_grade.CreateSubsectionGrade
    """
    if DEBUG: log.info('get_subsection_grade() student: {student}, '\
        'course_key: {course_key}, problem_usage_key: {problem_usage_key}'.format(
        student=student,
        course_key=course_key,
        problem_usage_key=problem_usage_key
    ))

    subsection_grade = None
    store = modulestore()
    with store.bulk_operations(course_key):
        course_structure = get_course_blocks(student, store.make_course_usage_key(course_key))
        subsections_to_update = course_structure.get_transformer_block_field(
            problem_usage_key,
            GradesTransformer,
            'subsections',
            set(),
        )
        course = store.get_course(course_key, depth=0)
        subsection_grade_factory = SubsectionGradeFactory(student, course, course_structure)
        for subsection_usage_key in subsections_to_update:
            if subsection_usage_key in course_structure:
                subsection_grade = subsection_grade_factory.update(
                    course_structure[subsection_usage_key]
                )

    if not subsection_grade:
        log.error('get_subsection_grade() - did not find a grade object for student: {student}, '\
            'course_key: {course_key}, problem_usage_key: {problem_usage_key}'.format(
            student=student,
            course_key=course_key,
            problem_usage_key=problem_usage_key
        ))
    return subsection_grade

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
        due_date = lti_cached_assignment.due_date.isoformat() if lti_cached_assignment.due_date is not None else None
        data = {
            "type": "activity",
            "id": willo_id_from_url(lti_cached_assignment.url),	    ## example: 249dfef365fd434c9f5b98754f2e2cb3
            "title": lti_cached_assignment.display_name,	        ## example: Getting to Know Rover Review Assignment
            "description": lti_cached_assignment.display_name,	    ## example: Getting to Know Rover Review Assignment
            "due_date": due_date,                                   ## Rover assignment due_date in ISO string format: 2019-06-01T00:00:00+04:00
            "points_possible": lti_cached_grade.possible_graded     ## int. example: 11
        }

    except Exception as err:
        log.error('willolabs.tasks.create_column() - error preparing grade column data for Willo Labs api:\r\n{err}.\r\n{traceback}'.format(
            err=err,
            traceback=traceback.format_exc()
        ))
        return False

    # mcdaniel dec-2020 
    # Calstatela Fall 2020 midterm3 patch
    if CALSTATELA_MIDTERM3_PATCH:
        if lti_cached_course.course_id in CALSTATELA_MIDTERM3_COURSE_KEYS:
            if lti_cached_assignment.display_name in CALSTATELA_MIDTERM3_ASSIGNMENTS:
                if lti_cached_grade.possible_graded != 54.0:
                    data = calstatela_midterm3_patch_column(data)

    if DEBUG: log.info('willolabs.tasks.create_column() - assignment: {assignment} data: {data}'.format(
            assignment=lti_cached_assignment.display_name,
            data=data
        ))

    return willo_api_create_column(
        ext_wl_outcome_service_url=lti_cached_course.ext_wl_outcome_service_url,
        data=data,
        operation="post"
        )


def post_grade(self, lti_cached_course, lti_cached_enrollment, lti_cached_assignment, lti_cached_grade):
    """
    Willo Grade Sync api. Post grade scored for one student, for one homework assignment.
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


    Obsoleted:
        "activity_id": willo_activity_id_from_string(lti_cached_assignment.display_name),
    """
    if DEBUG: log.info('willolabs.tasks.post_grade()')

    try:

        willo_id = willo_id_from_url(lti_cached_assignment.url) + ":" + lti_cached_enrollment.lti_user_id
        data = {
            "type": "result",
            "id": willo_id,
            "activity_id": willo_id_from_url(lti_cached_assignment.url),
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

    # mcdaniel dec-2020 
    # Calstatela Fall 2020 midterm3 patch
    if CALSTATELA_MIDTERM3_PATCH:
        log.info('if CALSTATELA_MIDTERM3_PATCH')
        if lti_cached_course.course_id in CALSTATELA_MIDTERM3_COURSE_KEYS:
            log.info('if lti_cached_course.course_id in CALSTATELA_MIDTERM3_COURSE_KEYS')
            if homework_assignment_dict.get('section_display_name') in CALSTATELA_MIDTERM3_ASSIGNMENTS:
                log.info("if homework_assignment_dict.get('section_display_name') in CALSTATELA_MIDTERM3_ASSIGNMENTS")
                if lti_cached_grade.possible_graded != 54.0:
                    log.info('if lti_cached_grade.possible_graded != 54.0')
                    data = calstatela_midterm3_patch_grade(data)


    if DEBUG: log.info('willolabs.tasks.post_grade() - data: {data}'.format(
            data=data
        ))

    response_code = willo_api_post_grade(
        ext_wl_outcome_service_url=lti_cached_course.ext_wl_outcome_service_url,
        data=data
        )

    if 200 <= response_code <= 299:
        now = UTC.localize(datetime.datetime.now())
        lti_cached_grade.synched = now
        lti_cached_grade.save()




def get_assignment_grade(course_key,  problem_usage_key, subsection_grade):
    """
    Extract assignment grade data and compose into a dict, along with the URL
    for the assignment.

    Arguments:
    course_key: CourseKey

    problem_usage_key: block usage locator for the problem that was submitted.

    subsection_grade:
        lms.djangoapps.grades.subsection_grade.CreateSubsectionGrade
        this contains a private __dict__ object along w dynamic getters
        allowing references such as "subsection_grade.display_name"

    subsection_grade.graded_total:
        <common.lib.xmodule.xmodule.graders.AggregatedScore>
        from xmodule.graders import AggregatedScore
        also uses a private __dict__ and dynamic getters

        AggregatedScore({'first_attempted': datetime.datetime(2020, 1, 17, 20, 33, 14, 114130, tzinfo=<UTC>), 'graded': True, 'possible': 11.0, 'earned': 11.0})
        subsection_grade.graded_total.__dict__: {'first_attempted': datetime.datetime(2020, 1, 17, 20, 33, 14, 114130, tzinfo=<UTC>), 'graded': True, 'possible': 11.0, 'earned': 11.0}

    Returns: dict
        - the url of the homework assignment containing the usage_key that was passed.
        - a grade dictionary for the homework assignment
    This method assumes that the usage_key passed points to a homework problem.

    example return:
    {
        'grades': {
            'section_display_name': "Getting to Know Rover Review Assignment",
            'section_due': datetime.datetime(2020, 1, 17, 20, 33, 14, 114130, tzinfo=<UTC>)
            'section_attempted_graded': True,
            'section_earned_all': 11,
            'section_possible_all': 17,
            'section_earned_graded': 11,
            'section_possible_graded': 11,
            'section_grade_percent': 100,
            },
        'url': u'https://dev.roverbyopenstax.org/courses/course-v1:ABC+OS9471721_9626+01/courseware/c0a9afb73af311e98367b7d76f928163/c8bc91313af211e98026b7d76f928163'
    }
    """

    grades = {
        'section_display_name': subsection_grade.display_name,
        'section_due': subsection_grade.due or (datetime.datetime.now() + datetime.timedelta(days=365.25/2)),
        'section_attempted_graded': subsection_grade.attempted_graded,
        'section_earned_all': subsection_grade.all_total.earned,
        'section_possible_all': subsection_grade.all_total.possible,
        'section_earned_graded': subsection_grade.graded_total.earned,
        'section_possible_graded': subsection_grade.graded_total.possible,
        'section_grade_percent': _calc_grade_percentage(subsection_grade.graded_total.earned, subsection_grade.graded_total.possible),
        }

    chapter = get_subsection_chapter(problem_usage_key)
    section_url = u'{scheme}://{host}/{url_prefix}/{course_id}/courseware/{chapter}/{section}'.format(
            scheme=u"https" if settings.HTTPS == "on" else u"http",
            host=settings.SITE_NAME,
            url_prefix=u"courses",
            course_id=course_key.html_id(),
            chapter=chapter,
            section=subsection_grade.url_name
            )

    retval = {
        'grades':  grades,
        'url': section_url
    }
    return retval

def _calc_grade_percentage(earned, possible):
    """
        calculate the floating point percentage grade score based on the
        integer parameters "earned" and "possible"
    """
    f_grade = float(0)
    if possible != 0:
        f_grade = float(earned) / float(possible)
    return f_grade

