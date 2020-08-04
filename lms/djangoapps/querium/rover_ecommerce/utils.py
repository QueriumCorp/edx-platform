"""
Utility methods called from Mako templates in Rover theme.
"""
# python  stuff
import logging
import datetime

# django stuff
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

# open edx stuff
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from courseware.date_summary import VerifiedUpgradeDeadlineDate
from student.models import is_faculty

# our stuff
from .models import Configuration, EOPWhitelist

log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG


def paywall_should_render(request):
    """
    A series of boolean tests to determine whether the paywall html
    should be rendered an injected into the current page.

    Args:
        request: the current http request

    Returns:
        [boolean]: True if the Mako template should fully render all html.
    """
    ## this code is moot if the user is not yet authenticated.
    if not request.user.is_authenticated:
    logger('paywall_should_render() - Not authenticated, exiting.')
    return False

    if is_faculty(request.user):
        logger('paywall_should_render() - Faculty user - never block!, exiting.')
        return False


    if is_eop_student(request.user.email):
        logger('paywall_should_render() - User is an EOP student, exiting.')
        return False

    course = get_course(request)
    if course is None:
        logger('paywall_should_render() - Not a course, exiting.')
        return False

    if not is_ecommerce_enabled(request):
        logger('paywall_should_render() - Ecommerce is not enabled for this course, exiting.')
        return False

    return True

def paywall_should_raise(request)
    """[summary]

    Args:
        request: the current http request

    Returns:
        [boolean]: True if the user has exceeded the payment deadline date
        for the course in which the current page is being rendered.
    """
    payment_deadline_date = get_course_deadline_date(request)
    if payment_deadline_date is None:
        return False

    now = datetime.datetime.now()
    if now <= payment_deadline_date:
        logger('Payment deadline is in the future, exiting.')
        return False

    log.error('paywall_should_raise() - Ecommerce paywall being raised on user {}!'.format(user.email))
    return True

def is_eop_student(request)
    """Looks for a record in EOPWhitelist with the email address
    of the current user.

    Args:
        request: the current http request

    Returns:
        [boolean]: True if the current user's email address is saved
        to the EOP Whitelist table.
    """
    logger('is_eop_student() - begin')
    try:
        usr = EOPWhitelist.objects.filter(user_email=request.user.email)
        return True
    except ObjectDoesNotExist:
        pass

    return False


def is_ecommerce_enabled(request)
    """
    Args:
        request: the current http request

    Args:
        request: the current http request

    Returns:
        [boolean]: True if Oscar e-commerce is running and this course
        has been configured for e-commerce.
    """
    logger('is_ecommerce_enabled() - begin')

    block = get_verified_upgrade_deadline_block(request)
    if block is None:
        return False

    return block.is_enabled

def get_verified_upgrade_deadline_block(request):
    """Retrieve the content block containing the
    Verified Upgrade meta information.

    Args:
        request: the current http request

    Returns:
        [type]: [description]
    """

    logger('get_verified_upgrade_deadline_block() - begin')
    course = get_course(request)
    return VerifiedUpgradeDeadlineDate(course, request.user)


def get_course_id(request):
    """
    Extract the course_id from the current request, if one exists.

    Args:
        request: the current http request

    Returns:
        [string]: string representation of the course_id, or None
    """
    try:
        ## this is a hacky way to test for a course object that MIGHT be
        ## included in the page context for whatever page called this template.

        ## attempt to grap the course_id slug, if it exists.
        course_id = request.path.split("/")[2]

        ## test to see if the slug we grabbed is really a course_id
        course_key = CourseKey.from_string(course_id)

        return course_id
    except:
        pass

    return None

def get_course(request):
    """retrieve the course object from the current request

    Args:
        request (http request): current request from the current  user

    Returns:
        [course]: a ModuleStore course object
    """
    try:
        course_id = get_course_id()
        course_key = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_key)
        return course
    except:
        logger('Not a course, exiting.')
        pass

    return None

def get_course_deadline_date(request):
    """
    retrieve the payment deadline date for the course.

    Args:
        course (CourseKey): the Opaque Key for the course which the current page
        is related.

    Returns:
        [DateTimeField]: the payment deadline date for the CourseKey
    """

    try:
        course_id = get_course_id(request)
        configuration = Configuration.objects.filter(course_id=course_id)
        return configuration.payment_deadline_date
    except ObjectDoesNotExist:
        return None

def logger(msg):
    if DEBUG:
        log.info(msg)

