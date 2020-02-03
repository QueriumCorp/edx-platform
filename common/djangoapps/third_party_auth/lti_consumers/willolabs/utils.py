# -*- coding: utf-8 -*-
from __future__ import absolute_import
"""
  written by:   Lawrence McDaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com 

                Matt Hangar, Willo Labs
                matt.hanger@willolabs.com

  Date:         June-2019
                Jan-2020

  Usage:        determine whether an LTI-authenticated user is faculty.


"""

import re
import datetime
import json
import requests
from django.conf import settings
from common.djangoapps.third_party_auth.lti_consumers.willolabs.constants import (
    WILLO_INSTRUCTOR_ROLES, 
    WILLO_DOMAINS
    )
from common.djangoapps.third_party_auth.lti_consumers.willolabs.models import (
    LTIExternalCourse,
    LTIExternalCourseEnrollment,
    LTIExternalCourseAssignments,
    LTIExternalCourseEnrollmentGrades,
    )
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.contrib.auth import get_user_model
USER_MODEL = get_user_model()

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


import logging
log = logging.getLogger(__name__)

def is_lti_gradesync_enabled(course_key):
    try:
        return LTIExternalCourse.objects.filter(course_id = course_key).exists()
    except:
        return False

    return False

def is_lti_cached_user(user, context_id):
    """
     Test to see if there is cached LTI enrollment data for this user.

     user: a Django user model
     course_id: a Opaque Key object.
    """
    try:
        ret = LTIExternalCourseEnrollment.objects.get(
            course=LTIExternalCourse.objects.get(context_id=context_id),
            user=user
            )
        return ret is not None
    except LTIExternalCourseEnrollment.DoesNotExist:
        return False

def willo_date(dte, format='%Y-%m-%d %H:%M:%S.%f'):
    """
     Returns a string representation of a datetime in this format: "2019-06-01T00:00:00+04:00"

     dte: either a datetime or a string representation of datetime in this format: %Y-%m-%d %H:%M:%S.%f
    """

    if dte is None: return None

    if type(dte) == datetime.datetime: return dte.isoformat()

    if type(dte) == str: return datetime.datetime.strptime(date_string=dte, format=format).isoformat()
        
    log.error('willo_date() - received an expected data type: {type}, value: {value}'.format(
        type=type(dte),
        value=dte
    ))
    return None


def get_lti_cached_result_date(
            course_id,
            username, 
            section_url,
            section_completed_date=None, 
            section_due_date=None
            ):
    """
      Try to retrieve an assignment completion date from the LTI cache.

      course_id: course key that contains the assignment
      username: Rover user who completed the assignment
      lti_id: the LTI unique identifier for the assignment, created from the Rover resource key (right-most segment of URL path)
      section_completed_date: an alternative date that is potentially supplied by the Rover grades api.
      section_due_date: ditto.
    """

    # need to consider that there might be more than one course with this course_id 
    user = USER_MODEL.objects.get(username=username)
    course_key = CourseKey.from_string(course_id)

    # must take into consideration that course_id is not unique
    # for LTIExternalCourse given that multiple external LMS'
    # could potentially share a common Rover course.
    courses = LTIExternalCourse.objects.filter(course_id = course_key)
    for course in courses:
        try:
            course_assignment=LTIExternalCourseAssignments.objects.get(
                course=course,
                url=section_url
            )
            course_enrollment=LTIExternalCourseEnrollment.objects.get(
                course=course,
                user=user
            )
            res = LTIExternalCourseEnrollmentGrades.objects.filter(
                course_assignment=course_assignment,
                course_enrollment=course_enrollment
            ).order_by('-created').first()
            if res is not None: return res.created
        except:
            pass

    if section_completed_date is not None: return section_completed_date
    if section_due_date is not None:  return section_due_date
    return datetime.datetime.now()

def willo_id_from_url(url):
    """
     Strip right-most segment of a URL path to use as a unique id for 
     Willo Labs api grades posts.

     Example:
     url = https://dev.roverbyopenstax.org/courses/course-v1:OpenStax+PCL101+2020_Tmpl_RevY/courseware/aa342d9db424426f8c6c550935e8716a/249dfef365fd434c9f5b98754f2e2cb3
     path = /courses/course-v1:OpenStax+PCL101+2020_Tmpl_RevY/courseware/aa342d9db424426f8c6c550935e8716a/249dfef365fd434c9f5b98754f2e2cb3
     return value = '249dfef365fd434c9f5b98754f2e2cb3'
    """
    parsed_url = urlparse(url)
    return parsed_url.path.rsplit('/', 1)[-1]

def willo_activity_id_from_string(activity_string):
    """
     Strip activity_string to alphanumeric characters.
     return value is used as the activity_id and id values for Willo Labs grade and column post api.
    """
    return re.sub(r'\W+', '', activity_string).lower()     # alphanumeric
    #return re.sub(r'/^[a-zA-Z0-9-_]+$/', '', activity_string).lower()

def get_lti_user_id(course_id, username, context_id=None):
    """
     Retrieve the Willo Labs user_id assigned to Rover username for course_id.
     This is passed in tpa_params during LTI authentication and cached.
    """

    #msg='get_lti_user_id() - course_id: {course_id}, username: {username}'.format(
    #    course_id=course_id,
    #    username=username
    #)
    #print(msg)

    user = USER_MODEL.objects.get(username=username)
    course_key = CourseKey.from_string(course_id)
    if context_id is not None:
        course = LTIExternalCourse.objects.get(context_id=context_id)
        if course is not None and user is not None:
            try:
                course_enrollment = LTIExternalCourseEnrollment.objects.get(
                    course = course,
                    user = user
                )
                return course_enrollment.lti_user_id
            except:
                pass
        else: return None

    # if there's not a context_id then we will still must 
    # take into consideration that course_id may not be unique
    # for LTIExternalCourse given that multiple external LMS'
    # could potentially share a common Rover course.
    courses = LTIExternalCourse.objects.filter(course_id = course_key)
    for course in courses:
        try:
            course_enrollment = LTIExternalCourseEnrollment.objects.get(
                course = course,
                user = user
            )
            if course_enrollment is not None: return course_enrollment.lti_user_id
        except:
            pass
    return None

def get_ext_wl_outcome_service_url(course_id, context_id=None):
    """
     Retrieve a Willo Labs outcome service URL from the LTI cache.
     This is passed in tpa_params during LTI authentication and cached.
    """
    if context_id is not None:
        course = LTIExternalCourse.objects.get(context_id=context_id)
    return course.ext_wl_outcome_service_url

    course_key = CourseKey.from_string(course_id)
    course = LTIExternalCourse.objects.filter(course_id=course_key).first()
    return course[0].ext_wl_outcome_service_url

def willo_api_create_column(ext_wl_outcome_service_url, data):
    """
     Willo Grade Sync api.
     Add a new grade column to the LMS grade book. 
     returns True if the return code is 200 or 201, False otherwise.

    ext_wl_outcome_service_url: 
        Provided by tpa_params dictionary from an LTI authentication, and cached in LTIExternalCourse.
        The URL endpoint to use when posting/syncing results from Rover to the host LMS.
        example: https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/

    Payload format:
        data = {
        "type": "activity",
        "id": "123456",
        "title": "Getting to Know Rover Review Assignment",
        "description": "Getting to Know Rover Review Assignment",
        "due_date": "2019-06-01T00:00:00+04:00",
        "points_possible": 100
        }

    Curl equivalent:
    -------------------------     
    curl -v -X POST https://stage.willolabs.com/api/v1/outcomes/BBKQyB/4469701c1aad450891edf449942cb25b/ \
        -H "Content-Type: application/vnd.willolabs.outcome.activity+json" \
        -H "Authorization: Token sampleaccesstoken" \
        -d \
    '{
        "type": "activity",
        "id": "tutorial-avoiding-plagiarism",
        "title": "Tutorial: Avoiding Plagiarism",
        "description": "sample description",
        "due_date": "2019-06-01T00:00:00+04:00",
        "points_possible": 100
    }'

    """
    log.debug('willo_api_create_column() - assignment: {assignment}'.format(
        assignment=data.get('title')
    ))

    headers = willo_api_headers(
        key = 'Content-Type',
        value = 'application/vnd.willolabs.outcome.activity+json'
        )
    data_json = json.dumps(data)
    response = requests.post(url=ext_wl_outcome_service_url, data=data_json, headers=headers)
    if 200 <= response.status_code <= 299:
        if response.status_code == 200:
            log.debug('willo_api_create_column() - successfully created grade column: {grade_column_data}'.format(
                grade_column_data = data_json
            ))
        if response.status_code == 201:
            log.debug('willo_api_create_column() - successfully updated grade column: {grade_column_data}'.format(
                grade_column_data = data_json
            ))
    else:
        log.error('willo_api_create_column() - encountered an error while attempting to create a new grade column: {grade_column_data}, which generated the following response: {response}'.format(
            grade_column_data = data_json,
            response = response.status_code
        ))

    return response.status_code

def willo_api_post_grade(ext_wl_outcome_service_url, data):
    """
    Willo Grade Sync api.

    Gist:  https://gist.github.com/matthanger-willo/4ab620e811c6da7c4412271945d85a6c
    Docs:  https://docs.google.com/document/d/1Q_dRXEpHnzWFti2j8R5CNtgOVIDMBXfRXWbf4fSHvBE/edit

    post grade scored for one student, for one homework assignment.
    Willo api returns 200 if the grade was posted.
    returns True if the return code is 200, False otherwise.

    ext_wl_outcome_service_url: 
        Provided by tpa_params dictionary from an LTI authentication, and cached in LTIExternalCourse.
        The URL endpoint to use when posting/syncing results from Rover to the host LMS.
        example: https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/

    Payload format:
        data = {
            "type": "result",
            "id": "block-v1:OpenStax+PCL101+2020_Tmpl_RevY+type@problem+block@669e8abe089b4a69b3a2565402d27cad",
            "activity_id": 123456,
            "user_id": 123456,
            "result_date": "2019-06-01T00:00:00+04:00",
            "score": 10,
            "points_possible": 10
        }

    Curl equivalent:
    -------------------------
        curl -v -X POST https://stage.willolabs.com/api/v1/outcomes/BBKQyB/4469701c1aad450891edf449942cb25b/ \
            -H "Content-Type: application/vnd.willolabs.outcome.result+json" \
            -H "Authorization: Token sampleaccesstoken" \
            -d \
        '{
            "type": "result",
            "id": "8627ec7e1215413385f10b20d0dde4f0",
            "activity_id": "tutorial-avoiding-plagiarism",
            "user_id": "523bd4baaf772a615a478397d560a1591c7e3347",
            "result_date": "2019-05-04T16:59:01.938229+00:00",
            "score": 100,
            "points_possible": 100
        }'
    """
    headers = willo_api_headers(
        key='Content-Type',
        value='application/vnd.willolabs.outcome.result+json'
        )
    data_json = json.dumps(data)
    response = requests.post(url=ext_wl_outcome_service_url, data=data_json, headers=headers)
    if 200 <= response.status_code <= 299:
        log.debug('willo_api_post_grade() - successfully posted grade data: {grade_data}'.format(
            grade_data = data_json
        ))
    else:
        log.error('willo_api_post_grade() - encountered an error while attempting to post the following grade: {grade_data} which generated the following response: {response}'.format(
            grade_data = data_json,
            response = response.status_code
        ))

    return response.status_code

    
def willo_api_get(url, assignment_id, user_id):
    """
     Willo Grade Sync api.
     Retrieve a grade record (list) for one student for one assignment
     returns http response as a json dict

    Curl equivalent:
    -------------------------
    curl -v -X GET "https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/?id=tutorial-avoiding-plagiarism&user_id=523bd4baaf772a615a478397d560a1591c7e3347" \
        -H "Accept: application/vnd.willolabs.outcome.result+json" \
        -H "Authorization: Token YOURSUPERDUPERENCRYPTEDTOKEN"

    """
    log.debug('willo_api_get()')

    params = {
        'id' : assignment_id,
        'user_id' : user_id
        }
    headers = willo_api_headers(
        key='Accept',
        value='application/vnd.willolabs.outcome.result+json'
        )

    response = requests.get(url=url, params=params, headers=headers)
    if response.status_code == 200:
        log.debug('willo_api_get() - successfully retrieved grade data for user_id: {user_id}, assignment id: {assignment_id}. The response was: {response}'.format(
            assignment_id = assignment_id,
            user_id = user_id,
            response = response.json()
        ))
        return response.json()
    else:
        log.error('willo_api_get() - encountered an error while attempting to retrieve grade data for user_id: {user_id}, assignment id: {assignment_id}. The response was: {response}'.format(
            assignment_id = assignment_id,
            user_id = user_id,
            response = response.status_code
        ))

    return None

def willo_api_authorization_token():
    """
     Returns a Willo Labs api authentication token
     example: qHT28EAgrxa1234567890abcdefghij2eRC8hdua
    """
    log.debug('willo_api_authorization_token()')

    token = settings.WILLO_API_AUTHORIZATION_TOKEN
    return token

def willo_api_headers(key, value):
    """
     returns a Willo api request header
    """
    headers = {}
    headers['Authorization'] = 'Token {secret}'.format(
            secret = willo_api_authorization_token()
        )
    headers[key] = value

    log.debug('willo_api_headers() - {headers}'.format(
        headers = json.dumps(headers)
    ))

    return headers


def is_willo_lti(lti_params):
    """
    Determine from data in the lti_params json object returns by LTI authentication
    whether the session originated from Willo Labs.

    True if there is a parameter named "ext_wl_launch_url" and the value is a 
    valid URL, and the hostname of the URL is contained in the set WILLO_DOMAINS
    """

    try:
        launch_domain = urlparse(lti_params.get("ext_wl_launch_url")).hostname
    except Exception as e:
        pass
        return False

    return launch_domain in WILLO_DOMAINS

def is_valid_course_id(value):

    # try to create an instance of CourseKey from the value passed
    try:
        course_key = CourseKey.from_string(value)
    except:
        pass
        return False

    # Verify that this course_id corresponds with a Rover course 
    if not CourseOverview.get_from_id(course_key):
        return False
    
    return True


def get_lti_faculty_status(lti_params):
    """
    Input parameters:
    ===================
    lti_params - a tpa_lti_params dictionary that is part of the http response body
    in an LTI authentication. see ./sample_data/tpa_lti_params.json for an example.

    Extract the LTI roles tuples parameter from lti_params, if it exists.
    Example:
    =======================
    roles_param = (
        'Learner',
        'urn:lti:instrole:ims/lis/Student,Student,urn:lti:instrole:ims/lis/Learner,Learner',
        'Instructor',
        'Instructor,urn:lti:sysrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Administrator',
        'TeachingAssistant',
        'urn:lti:instrole:ims/lis/Administrator'
    )
    """
    #log.info('get_lti_faculty_status() - start')


    roles_param = lti_params.get("roles_param", ())
    if roles_param != ():
        #log.info('get_lti_faculty_status() - found roles_param: {}'.format(roles_param))
        for role_param in roles_param:
            # build the lti_params dict similar to what exists in openedx third_party_auth LTIAuthBackend
            lti_params = {
                'email': 'matt.hanger@willolabs.com',
                'lis_person_name_full': 'Matt Hanger',
                'lis_person_name_given': 'Matt',
                'lis_person_name_family': 'Hanger',
                'roles': role_param
            }
            # extract the roles from lti_params
            user_roles = {x.strip() for x in lti_params.get('roles', '').split(',')}
            # check if the lti_params represent an instructor
            # use python set intersection operator "&" to simplify the check
            is_instructor = bool(user_roles & WILLO_INSTRUCTOR_ROLES)
            if is_instructor:
                return "confirmed_faculty"

    """
        mcdaniel oct-2019
        example from University of Kansas:
        "roles": "urn:lti:role:ims/lis/Instructor",

    """
    roles = lti_params.get("roles", None)
    if roles:
        log.info('get_lti_faculty_status() - found roles: {}'.format(roles))
        if roles in WILLO_INSTRUCTOR_ROLES:
            return "confirmed_faculty"

    return "no_faculty_info"

"""
  Output:

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: Learner
    Extracted roles:
    	Learner
    Is instructor: False

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: urn:lti:instrole:ims/lis/Student,Student,urn:lti:instrole:ims/lis/Learner,Learner
    Extracted roles:
    	Learner
    	Student
    	urn:lti:instrole:ims/lis/Learner
    	urn:lti:instrole:ims/lis/Student
    Is instructor: False

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: Instructor
    Extracted roles:
    	Instructor
    Is instructor: True

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: Instructor,urn:lti:sysrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Administrator
    Extracted roles:
    	Instructor
    	urn:lti:instrole:ims/lis/Administrator
    	urn:lti:sysrole:ims/lis/Administrator
    Is instructor: True

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: TeachingAssistant
    Extracted roles:
    	TeachingAssistant
    Is instructor: True

    LTI parameters:
    	email: matt.hanger@willolabs.com
    	lis_person_name_family: Hanger
    	lis_person_name_full: Matt Hanger
    	lis_person_name_given: Matt
    	roles: urn:lti:instrole:ims/lis/Administrator
    Extracted roles:
    	urn:lti:instrole:ims/lis/Administrator
    Is instructor: True
"""
