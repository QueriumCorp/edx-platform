"""Utility functions that have to do with the courseware."""


import datetime
import logging

from django.conf import settings
from lms.djangoapps.commerce.utils import EcommerceService
from pytz import utc

from course_modes.models import CourseMode
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID
from xmodule.partitions.partitions_service import PartitionService

DEBUG = False
log = logging.getLogger(__name__)

def verified_upgrade_deadline_link(user, course=None, course_id=None):
    """
    Format the correct verified upgrade link for the specified ``user``
    in a course.

    One of ``course`` or ``course_id`` must be supplied. If both are specified,
    ``course`` will take priority.

    Arguments:
        user (:class:`~django.contrib.auth.models.User`): The user to display
            the link for.
        course (:class:`.CourseOverview`): The course to render a link for.
        course_id (:class:`.CourseKey`): The course_id of the course to render for.

    Returns:
        The formatted link that will allow the user to upgrade to verified
        in this course.
    """
    if course is not None:
        course_id = course.id
    return EcommerceService().upgrade_url(user, course_id)


def can_show_verified_upgrade(user, enrollment, course=None):
    """
    Return whether this user can be shown upgrade message.

    Arguments:
        user (:class:`.AuthUser`): The user from the request.user property
        enrollment (:class:`.CourseEnrollment`): The enrollment under consideration.
            If None, then the enrollment is considered to be upgradeable.
        course (:class:`.ModulestoreCourse`): Optional passed in modulestore course.
            If provided, it is expected to correspond to `enrollment.course.id`.
            If not provided, the course will be loaded from the modulestore.
            We use the course to retrieve user partitions when calculating whether
            the upgrade link will be shown.
    """
    # Return `true` if user is not enrolled in course
    if enrollment is None:
        if DEBUG: log.info('can_show_verified_upgrade() - not enrolled. returning False.')
        return False
    partition_service = PartitionService(enrollment.course.id, course=course)
    enrollment_track_partition = partition_service.get_user_partition(ENROLLMENT_TRACK_PARTITION_ID)
    group = partition_service.get_group(user, enrollment_track_partition)
    current_mode = None
    if group:
        try:
            current_mode = [
                mode.get('slug') for mode in settings.COURSE_ENROLLMENT_MODES.values() if mode['id'] == group.id
            ].pop()
        except IndexError:
            pass
    upgradable_mode = not current_mode or current_mode in CourseMode.UPSELL_TO_VERIFIED_MODES

    if not upgradable_mode:
        if DEBUG: log.info('can_show_verified_upgrade() - not upgradable_mode. returning False.')
        return False

    #---------------------------------------------------------------------------------------
    # mcdaniel sep-2020: Rover uses a payment deadline rather than an upgrade deadline.
    # in our case we only want to hide the Buy button if a) ecommerce is not enabled for
    # the course, or b) the student has already paid.
    #---------------------------------------------------------------------------------------
    #upgrade_deadline = enrollment.upgrade_deadline
    #
    #if upgrade_deadline is None:
    #    return False
    #
    #if datetime.datetime.now(utc).date() > upgrade_deadline.date():
    #    return False

    # Show the summary if user enrollment is in which allow user to upsell
    if DEBUG: log.info('can_show_verified_upgrade() - return value is based on our custom logic of enrollment.is_active: {is_active}, enrollment.mode: {mode}, upsell modes: {upsell_modes}'.format(
        is_active=enrollment.is_active,
        mode=enrollment.mode,
        upsell_modes=CourseMode.UPSELL_TO_VERIFIED_MODES
    ))
    return enrollment.is_active and enrollment.mode in CourseMode.UPSELL_TO_VERIFIED_MODES
