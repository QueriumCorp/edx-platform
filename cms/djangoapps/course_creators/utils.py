"""
written by: mcdaniel
date:       feb-2019

Utilities for working with oAuth connections to openstax.org.
"""
from student import auth
from student.roles import CourseCreatorRole
from views import _add_user, update_course_creator_group

def grant_course_creator_status(user):
    """
    called during oAuth pipeline.
    sets course creator status to GRANTED.
    """
    _add_user(user, CourseCreator.GRANTED)
    update_course_creator_group(get_staff_user(), user, True)

def get_staff_user():
    """
    magically pull a user with is_staff from the green grassy knoll
    """
    return None
