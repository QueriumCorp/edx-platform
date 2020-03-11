# -*- coding: utf-8 -*-
"""Utility and convenient methods."""

from __future__ import absolute_import

import logging

from django.conf import settings

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .models import LTIExternalCourse
from opaque_keys.edx.locator import BlockUsageLocator

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG

def chapter_from_url(url):
    """
     Strip right-most segment of a URL path to use as a unique id for 
     Willo Labs api grades posts.

     Example - fully-qualified URL:
     url = https://dev.roverbyopenstax.org/courses/course-v1:OpenStax+PCL101+2020_Tmpl_RevY/courseware/aa342d9db424426f8c6c550935e8716a/249dfef365fd434c9f5b98754f2e2cb3
     path = /courses/course-v1:OpenStax+PCL101+2020_Tmpl_RevY/courseware/aa342d9db424426f8c6c550935e8716a/249dfef365fd434c9f5b98754f2e2cb3
     return value = 'aa342d9db424426f8c6c550935e8716a'

    """

    # a "url" from within an open edx course object
    if not isinstance(url, str):
        raise Exception('chapter_from_url() was expecting a string.')
    else:
        # a valid fully-qualified URL
        parsed_url = urlparse(url)
        return parsed_url.path.rsplit('/')[-2]

def willo_id_from_url(url):
    """
     Strip right-most segment of a URL path to use as a unique id for 
     Willo Labs api grades posts.

     Example - fully-qualified URL:
     url = https://dev.roverbyopenstax.org/courses/course-v1:OpenStax+PCL101+2020_Tmpl_RevY/courseware/aa342d9db424426f8c6c550935e8716a/249dfef365fd434c9f5b98754f2e2cb3
     path = /courses/course-v1:OpenStax+PCL101+2020_Tmpl_RevY/courseware/aa342d9db424426f8c6c550935e8716a/249dfef365fd434c9f5b98754f2e2cb3
     return value = '249dfef365fd434c9f5b98754f2e2cb3'

     Example - Open edX "url"
     url = block-v1:OpenStax+PCL101+2020_Tmpl_RevY+type@hdrxblock+block@a722024eb07f483cb3fee7df16c608f3
    return value = a722024eb07f483cb3fee7df16c608f3

    """

    # a "url" from within an open edx course object
    if isinstance(url, BlockUsageLocator):
        path = str(url)
        return path.rsplit('@', 1)[-1]
    else:
        # a valid fully-qualified URL
        parsed_url = urlparse(url)
        return parsed_url.path.rsplit('/', 1)[-1]




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



def find_course_unit(course, url):
    """
    Finds the unit (block, module, whatever the terminology is) in which
    the right-most slug of the url exists in the node.location parameter.

    Raises DashboardError if no unit is found.

    course: a Rover course object

    url: a fully-qualified URL (including http protocol). 
    example: https://dev.roverbyopenstax.org/courses/course-v1:OpenStax+PCL101+2020_Tmpl_RevY/courseware/aa342d9db424426f8c6c550935e8716a/249dfef365fd434c9f5b98754f2e2cb3
    """
    def find(node, url):
        """
        Find node in course tree for url.
        """
        location = willo_id_from_url(node.location)
        if location == url:
            if DEBUG: log.info('lti_consumers.willolabs.utils.find() - found course unit: {unit}'.format(
                    unit=node
                ))
            return node
        for child in node.get_children():
            found = find(child, url)
            if found:
                return found
        return None

    url = willo_id_from_url(url)
    unit = find(course,  url)
    if unit is None:
        raise Exception(_("Couldn't find module for url: {url}").format(
            url=url
            ))
    return unit
