"""
written by: mcdaniel
date:       feb-2019

Utilities for working with oAuth connections to openstax.org.
"""
from student import auth
from student.roles import CourseCreatorRole
from cms.djangoapps.course_creators.views import _add_user, update_course_creator_group

from logging import getLogger
logger = getLogger(__name__)

def grant_course_creator_status(user):
    """
    called during oAuth pipeline.
    sets course creator status to GRANTED.
    """
    full_name = user.first_name + u' ' + user.last_name

    msg = u'trying to grant AM course creator status to {}.'.format(full_name)
    logger.info(msg)

    _add_user(user, CourseCreator.GRANTED)
    update_course_creator_group(get_staff_user(), user, True)

    msg = u'{} has been granted course creator permissions in AM.'.format(full_name)
    logger.info(msg)

    return None

def get_staff_user():
    """
    magically pull a user with is_staff from the green grassy knoll
    """
    return None
