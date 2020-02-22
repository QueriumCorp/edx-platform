# -*- coding: utf-8 -*-
"""Utility and convenient methods."""

from __future__ import absolute_import
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .models import LTIExternalCourse

def is_lti_gradesync_enabled(course_key):
    """Grade sync is considered enabled for a course if
    there exists a cache record for the course. Cache
    records are created during LTI authentication via Willo Labs.
    
    Arguments:
        course_key {CourseKey} 
    
    Returns:
        [Boolean] -- True if LTI Grade Sync is enabled for the course_key
    """
    try:
        return LTIExternalCourse.objects.filter(course_id = course_key).exists()
    except:
        return False

    return False

def is_valid_course_id(course_id):
    """Validate a string representing a course_id.
    course_id is considered valid if:
    1. it is possible to instantiate a CourseKey
       object from the string.
    2. Open edX LMS returns a CourseOverview object
    for the course_key.
    
    Arguments:
        course_id {string} -- example: ?????????
    
    Returns:
        [Boolean] -- True if the course_id string is valid.
    """
    # try to create an instance of CourseKey from the course_id passed
    try:
        course_key = CourseKey.from_string(course_id)
    except:
        pass
        return False

    # Verify that this course_id corresponds with a Rover course 
    if not CourseOverview.get_from_id(course_key):
        return False
    
    return True


