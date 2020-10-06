"""
Utility methods called from Mako templates in Rover theme.
"""
# python  stuff
import logging
import datetime
import pytz

# django stuff
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

# open edx stuff
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from courseware.date_summary import VerifiedUpgradeDeadlineDate
from student.models import is_faculty, get_user_by_username_or_email

# our stuff
from lms.djangoapps.querium.rover_ecommerce.models import Configuration, EOPWhitelist

log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG
DEBUG = True
UTC = pytz.UTC

def paywall_should_render(request, context):
    """
    A series of boolean tests to determine whether the paywall html
    should be rendered an injected into the current page.

    Args:
        request: the current http request
        context: the mako context object

    Returns:
        [boolean]: True if the Mako template should fully render all html.
    """
    ## this code is moot if the user is not yet authenticated.
    try:
        user = get_user_by_username_or_email(request.user)
    except:
        return False

    if not user.is_authenticated:
        logger('paywall_should_render() - Not authenticated, exiting.')
        return False

    if is_faculty(user):
        logger('paywall_should_render() - Faculty user - never block!, exiting.')
        return False

    if is_eop_student(request):
        logger('paywall_should_render() - User is an EOP student, exiting.')
        return False

    course = get_course(request, context)
    if course is None:
        logger('paywall_should_render() - Not a course, exiting.')
        return False

    if not is_ecommerce_enabled(request, context):
        logger('paywall_should_render() - Ecommerce is not enabled for this course, exiting.')
        return False

    return True

def paywall_should_raise(request, context):
    """[summary]

    Args:
        request: the current http request
        context: the mako context object

    Returns:
        [boolean]: True if the user has exceeded the payment deadline date
        for the course in which the current page is being rendered.
    """
    payment_deadline_date = get_course_deadline_date(request, context)
    if payment_deadline_date is None:
        return False

    now = UTC.localize(datetime.datetime.now())
    if now <= payment_deadline_date:
        logger('Payment deadline is in the future, exiting.')
        return False

    user = get_user_by_username_or_email(request.user)
    logger('paywall_should_raise() - Ecommerce paywall being raised on user {}!'.format(user.email))
    return True

def is_eop_student(request):
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
        user = get_user_by_username_or_email(request.user)
        usr = EOPWhitelist.objects.filter(user_email=user.email).first()
        if usr is not None:
            return True
    except ObjectDoesNotExist:
        pass

    return False


def is_ecommerce_enabled(request, context):
    """
    Args:
        request: the current http request

    Args:
        request: the current http request
        context: the mako context object

    Returns:
        [boolean]: True if Oscar e-commerce is running and this course
        has been configured for e-commerce.
    """
    logger('is_ecommerce_enabled() - begin')

    block = get_verified_upgrade_deadline_block(request, context)
    if block is None:
        logger('is_ecommerce_enabled() - get_verified_upgrade_deadline_block is None. returning False')
        return False

    logger('is_ecommerce_enabled() - block.is_enabled = {is_enabled}'.format(
        is_enabled=block.is_enabled
    ))
    return block.is_enabled

def get_verified_upgrade_deadline_block(request, context):
    """Retrieve the content block containing the
    Verified Upgrade meta information.

    Args:
        request: the current http request
        context: the mako context object

    Returns:
        [type]: [description]
    """

    logger('get_verified_upgrade_deadline_block() - begin')
    course = get_course(request, context)
    user = get_user_by_username_or_email(request.user)
    return VerifiedUpgradeDeadlineDate(course, user)


def get_course_id(request, context):
    """
    Extract the course_id from the current request, if one exists.

    Args:
        request: the current http request
        context: the mako context object

    Returns:
        [string]: string representation of the course_id, or None
    """
    try:
        ## this is a hacky way to test for a course object that MIGHT be
        ## included in the page context for whatever page called this template.

        ## attempt to grap the course_id slug, if it exists.
        logger('get_course_id() context: {context}, course_key: {course_key}'.format(
            context=context.keys(),
            course_key=context['course_key']
        ))

        course_id = str(context['course_key'])
        course_key = CourseKey.from_string(course_id)
        return course_id
    except Exception as e:
        logger('get_course_id() error: {e}'.format(
            e=e
        ))
        pass

    return None

def get_course(request, context):
    """retrieve the course object from the current request

    Args:
        request (http request): current request from the current  user
        context: the mako context object

    Returns:
        [course]: a ModuleStore course object
    """
    try:
        course_id = get_course_id(request, context)
        course_key = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_key)
        return course
    except:
        logger('get_course() {course_id} is not a course, exiting.'.format(
            course_id=course_id
        ))
        pass

    return None

def get_course_deadline_date(request, context):
    """
    retrieve the payment deadline date for the course.

    Args:
        course (CourseKey): the Opaque Key for the course which the current page
        is related.

    Returns:
        [DateTimeField]: the payment deadline date for the CourseKey
    """

    try:
        course_id = get_course_id(request, context)
        configuration = Configuration.objects.filter(course_id=course_id).first()
        if configuration is not None:
            return configuration.payment_deadline_date
    except Exception as e:
        logger('get_course_deadline_date() error: {e} '.format(
            e=e
        ))
        return None

    return None

def logger(msg):
    if DEBUG:
        log.info(msg)

