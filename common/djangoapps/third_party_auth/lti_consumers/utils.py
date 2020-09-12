# -*- coding: utf-8 -*-
"""Utility and convenient methods."""

from __future__ import absolute_import

# python stuff
import logging
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

# django stuff
from django.conf import settings
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

# open edx stuff
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xmodule.modulestore.django import modulestore

# rover stuff
from .models import (
    LTIExternalCourse,
    LTIInternalCourse,
    LTIConfigurations,
    LTIConfigurationParams
    )
from .constants import LTI_PARAMS_DEFAULT_CONFIGURATION

log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG

# mcdaniel may-2020: copied from lms.djangoapps.courseware.courses
# to try to resolve a race situation in juniper.rc3.
def get_course_by_id(course_key, depth=0):
    """
    Given a course id, return the corresponding course descriptor.
    If such a course does not exist, raises a 404.
    depth: The number of levels of children for the modulestore to cache. None means infinite depth
    """
    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=depth)
    if course:
        return course
    else:
        raise Http404(u"Course not found: {}.".format(six.text_type(course_key)))


def get_subsection_chapter(subsection_url):
    """Traverse the course structure to locate the parent
    chapter of subsection_url.

    in this example
        https://dev.roverbyopenstax.org/courses/course-v1:ABC+OS9471721_9626+01/courseware/c0a9afb73af311e98367b7d76f928163/c8bc91313af211e98026b7d76f928163
    - the chapter is c0a9afb73af311e98367b7d76f928163
    - the subsection is c8bc91313af211e98026b7d76f928163

    Arguments:
        subsection_url {String} --

    Returns:
        [String] -- string representation of the chapter segment for a URL.
    """
    if not isinstance(subsection_url, BlockUsageLocator):
        log.error('get_subsection_chapter() - data type mismatch. expected subsection_url of type BlockUsageLocator but received {t}'.format(
            t=type(subsection_url)
        ))
        return None

    parent = subsection_url
    while parent.block_type != u'chapter':
        parent = modulestore().get_parent_location(parent)

    # mcdaniel sep-2020: getting this warning: DeprecationWarning: Name is no longer supported as a property of Locators. Please use the block_id property.
    #return parent.name
    return parent.block_id


def chapter_from_url(url):
    """
     Strip right-most segment of a URL path to use as a unique id for
     LTI Consumer API grades posts.

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
    """LTI Grade Sync is enabled for a course if:
    1. settings.ROVER_ENABLE_LTI_GRADE_SYNC == True
    2. LTIInternalCourse.enabled == True for the course_key
    3. there exists a cache record in LTIExternalCourse for the course.

    Note: this is coded to hopefully avoid run-time errors and instead
    to generate copious log info describing any configuration problems that
    prevent the proper evaluation of LTI Grade Sync usage for a course.

    Arguments:
        course_key: CourseKey object or string representation of a CourseKey

    Returns:
        [Boolean] -- True if LTI Grade Sync is enabled for the course_key
    """
    if DEBUG:
        log.info('is_lti_gradesync_enabled() - entering. course_key: {course_key}'.format(
            course_key=str(course_key)
        ))

    if not is_valid_course_id(course_key):
        log.error('is_lti_gradesync_enabled() received an invalid CourseKey: {course_key} {t}'.format(
            course_key=course_key,
            t=type(course_key)
            ))
        return False

    if type(course_key) is str:
        course_key = CourseKey.from_string(course_key)

    """
    Test #1
    Global system control over LTI Grade Sync. This is set
    in /home/ubuntu/.rover/rover.env.json.

    we wrap this in a try/except in case the django settings
    are missing this parameter, which would only plausibly happen
    if someone were to comment out the parameter assignment in
    lms/envs/production.py
    """
    try:
        if not settings.ROVER_ENABLE_LTI_GRADE_SYNC: return False
    except:
        log.error('is_lti_gradesync_enabled() - Missing parameter ROVER_ENABLE_LTI_GRADE_SYNC.')
        return False


    """
    Test #2
    A Rover system administrator has to manually create a record in LTIInternalCourse
    AND this record must satisfy LTIInternalCourse.enabled == True.
    return False if the record is missing, or if enabled == False
    """
    try:
        # test #2a: is there a control record in LTIInternalCourse for this course_key?
        lti_internal_course = LTIInternalCourse.objects.filter(course_id = course_key).first()
        if not lti_internal_course: return False

        # test #2b: is the control record enabled?
        if not lti_internal_course.enabled: return False
    except Exception as err:
        log.error('is_lti_gradesync_enabled() - Internal error while attempting to read LTIInternalCourse: {err}'.format(err=err))
        return False

    """
    Test #3
    Cache records are created automatically during LTI authentication
    This lti_consumers module provides functionality in cache.py that
    abstracts data from the http body response of the LTI authentication
    response, and upserts a tracking record in LTIExternalCourse.
    """
    try:
        lti_external_course = LTIExternalCourse.objects.filter(course_id=course_key).first()
        if not lti_external_course: return False

        return lti_external_course.enabled
    except:
        log.error('is_lti_gradesync_enabled() - Internal error while attempting to read LTIExternalCourse.')
        return False

    # we should never reach this code!
    log.error('is_lti_gradesync_enabled() - Internal coding error in this method. :(')
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
    if type(course_id) is CourseLocator: return True

    # try to create an instance of CourseKey from the course_id passed
    if type(course_id) is str:
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

def initialize_lti_configuration(name):
    """Initialize an LTI Configuration with the default mapping
    of LTI authentication parameters in LTI_PARAMS_DEFAULT_CONFIGURATION.

    Args:
        name (string): a human readable name for the LTI Configuration
                       example: "Default LTI Configuration"
    """
    configuration = LTIConfigurations(
        name=name,
        comments='auto-initialized by manage.py'
    )
    configuration.save()

    for table in LTI_PARAMS_DEFAULT_CONFIGURATION:
        print('table: {table}'.format(table=table))
        params = LTI_PARAMS_DEFAULT_CONFIGURATION[table]
        for param in params:
            print('inserting: {table}, {param}, {value}'.format(
                table=table,
                param=param,
                value=params[param]
            ))
            configuration_parameter = LTIConfigurationParams(
                configuration=configuration,
                table_name=table,
                internal_field=param,
                external_field=params[param],
                comments='auto-generated by manage.py from constants.LTI_PARAMS_DEFAULT_CONFIGURATION'
            )
            configuration_parameter.save()

def get_default_lti_configuration():
    """Return the default LTI Configuration object if it exists,
    otherwise create it and return it.

    Returns:
        [LTIConfigurations]: the default LTI Configuration object
    """
    config_name = "Default LTI Configuration"
    lti_configuration = LTIConfigurations.objects.filter(name=config_name).first()
    if lti_configuration: return lti_configuration

    initialize_lti_configuration(config_name)
    return LTIConfigurations.objects.filter(name=config_name).first()

def get_parent(item, block_type):
    """traverse up the course structure until we reach a block of type 'block_type'
    """
    parent = item
    while True:
        parent = parent.get_parent()
        if parent.location.block_type == block_type:
            return parent

def get_assignment(item):
    """traverse the course structure to return the parent Assignment

    Args:
        item (xBlock): a problem block
        item = modulestore().get_item(block_usage_key)

    Returns:
        [xBlock]: the assignment that contains the problem
    """
    return get_parent(item, 'sequential')

def get_chapter(item):
    """traverse the course structure to return the parent Chapter

    Args:
        item (BlockUsageKey): a problem block
        item = modulestore().get_item(block_usage_key)

    Returns:
        [BlockUsageKey]: the chapter that contains the problem
    """
    return get_parent(item, 'chapter')


def get_lti_courses(self, course):
    """evaluate course / user (both are optional) and query LTIInternalCourse

    Args:
        course: CourseOverview or None

    Returns: list of LTIInternalCourse records
    """

    if (LTIInternalCourse.objects.count() == 0):
        print('LTIInternalCourses table is empty.')
        return None

    if course is None:
        return LTIInternalCourse.objects.all()
    else:
        return LTIInternalCourse.objects.filter(course_fk__in=course)

