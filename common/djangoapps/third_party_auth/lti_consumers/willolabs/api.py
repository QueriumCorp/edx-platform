"""Willo Labs Grade Sync API calls
and convenience functions.
"""

import logging
import re
import datetime
import json
import requests

from django.conf import settings
from .models import LTIExternalCourse

from .exceptions import LTIBusinessRuleError

log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG


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


def willo_activity_id_from_string(activity_string):
    """
     Strip activity_string to alphanumeric characters.
     return value is used as the activity_id and id values for Willo Labs grade and column post api.
    """
    return re.sub(r'\W+', '', activity_string).lower()     # alphanumeric
    #return re.sub(r'/^[a-zA-Z0-9-_]+$/', '', activity_string).lower()


def willo_api_create_column(ext_wl_outcome_service_url, data):
    """
     Willo Grade Sync api.
     Add a new grade column to the LMS grade book. 
     returns True if the return code is 200 or 201, False otherwise.

    ext_wl_outcome_service_url: 
        Provided by tpa_params dictionary from an LTI authentication, and cached in LTIExternalCourse.
        The URL endpoint to use when posting/syncing results from Rover to the host LMS.
        example:  https://app.willolabs.com/api/v1/outcomes/DKGSf3/e42f27081648428f8995b1bca2e794ad/

    Payload format:
        data = {
            'due_date': '2020-04-29T04:59:00+00:00', 
            'description': u'Lesson 4.5', 
            'title': u'Lesson 4.5', 
            'points_possible': 5.0, 
            'type': , 
            'id': u'd7f67eb52e424909ba5ae7154d767a13'
        }

    Curl equivalent:
    -------------------------     
    curl -v -X POST https://app.willolabs.com/api/v1/outcomes/DKGSf3/e42f27081648428f8995b1bca2e794ad/ \
        -H "Content-Type: application/vnd.willolabs.outcome.activity+json" \
        -H "Authorization: Token sampleaccesstoken" \
        -d \
    '{
            'due_date': '2020-04-29T04:59:00+00:00', 
            'description': u'Lesson 4.5', 
            'title': u'Lesson 4.5', 
            'points_possible': 5.0, 
            'type': 'activity', 
            'id': u'd7f67eb52e424909ba5ae7154d767a13'
    }'

    """
    if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_create_column() - assignment: {assignment}'.format(
            assignment=data.get('title')
        ))

    if not ext_wl_outcome_service_url:
        raise LTIBusinessRuleError('api.willo_api_create_column() - internal error: ext_wl_outcome_service_url has not been set for this course. Cannot continue.')
    
    if not data:
        raise LTIBusinessRuleError('api.willo_api_create_column() - internal error: data dict is missing or null. Cannot continue.')

    headers = willo_api_headers(
        key = 'Content-Type',
        value = 'application/vnd.willolabs.outcome.activity+json'
        )
    data_json = json.dumps(data)
    response = requests.post(url=ext_wl_outcome_service_url, data=data_json, headers=headers)
    if 200 <= response.status_code <= 299:
        if response.status_code == 200:
            if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_create_column() - successfully created grade column: {grade_column_data}'.format(
                    grade_column_data = data_json
                ))
        if response.status_code == 201:
            if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_create_column() - successfully updated grade column: {grade_column_data}'.format(
                    grade_column_data = data_json
                ))
        if response.status_code not in (200, 201):
            if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_create_column() - return code: {response} grade column: {grade_column_data}'.format(
                    grade_column_data = data_json,
                    response=response.status_code
                ))

    else:
        log.error('lti_consumers.willolabs.api.willo_api_create_column() - encountered an error while attempting to create a new grade column: {grade_column_data}, which generated the following response: {response}'.format(
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
        example: https://app.willolabs.com/api/v1/outcomes/DKGSf3/e42f27081648428f8995b1bca2e794ad/


    Payload format:
        data = {
            'activity_id': u'lesson45', 
            'user_id': u'7010d877b3b74f39a6cbf89f9c3819ce', 
            'points_possible': 5.0, 
            'score': 0.5, 
            'result_date': '2020-04-24T19:12:19.454723+00:00', 
            'type': 'result', 
            'id': u'd7f67eb52e424909ba5ae7154d767a13'
        }

    Curl equivalent: (effective 25-Apr-2020 per conversation with Matt Hanger)
    -------------------------
        curl -v -X POST https://app.willolabs.com/api/v1/outcomes/DKGSf3/e42f27081648428f8995b1bca2e794ad/ \
        -H "Content-Type: application/vnd.willolabs.outcome.result+json" \
        -H "Authorization: Token replaceaccesstokenhere" \
        -d \
        '{
            "activity_id": "d7f67eb52e424909ba5ae7154d767a13",
            "id": "block-v1:OpenStax+PCL101+2020_Tmpl_RevY+type@problem+block@669e8abe089b4a69b3a2565402d27cad",
            "points_possible": 5.0,
            "result_date": "2020-04-24T19:12:19.454723+00:00",
            "score": 0.5,
            "type": "result",
            "user_id": "7010d877b3b74f39a6cbf89f9c3819ce"
        }'
    
    """
    if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_post_grade()')

    headers = willo_api_headers(
        key='Content-Type',
        value='application/vnd.willolabs.outcome.result+json'
        )
    data_json = json.dumps(data)
    response = requests.post(url=ext_wl_outcome_service_url, data=data_json, headers=headers)
    if 200 <= response.status_code <= 299:
        if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_post_grade() - successfully posted grade data: {grade_data}'.format(
            grade_data = data_json
        ))
    else:
        log.error('lti_consumers.willolabs.api.willo_api_post_grade() - encountered an error while attempting to post the following grade: {grade_data} which generated the following response: {response}'.format(
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
    if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_get()')

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
        if DEBUG: log.info('willo_api_get() - successfully retrieved grade data for user_id: {user_id}, assignment id: {assignment_id}. The response was: {response}'.format(
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
    if DEBUG: log.info('willo_api_authorization_token()')

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

    if DEBUG: log.info('willo_api_headers() - {headers}'.format(
            headers = json.dumps(headers)
        ))

    return headers

