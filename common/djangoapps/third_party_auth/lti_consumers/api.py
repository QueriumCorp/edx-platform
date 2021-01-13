"""
LTI Grade Sync API calls and convenience functions for Willo Grade Sync.
Code samples: https://gist.github.com/matthanger-willo/36b8ca40bd0d30f795a63531be877e76

API calls:
------------------
def willo_api_create_column(ext_wl_outcome_service_url, data, operation="post"):
def willo_api_post_grade(ext_wl_outcome_service_url, data):
def willo_api_get_outcome(url, assignment_id, user_id):

Utils:
------------------
def willo_api_check_column_should_post():
def willo_api_check_column_does_exist(ext_wl_outcome_service_url, data):
def willo_api_column_due_date_has_changed(response, data):
def willo_api_column_point_value_has_changed(response, data):
def willo_api_date(dte, format='%Y-%m-%d %H:%M:%S.%f'):
def willo_api_activity_id_from_string(activity_string):
def willo_api_headers(key, value):

def _float_value(val):
def _cache_pk(user_id=None, activity_id=None, id=None):
def _cache_get(user_id=None, activity_id=None, id=None):
def _cache_set(data, timeout=CACHE_DEFAULT_EXPIRATION, user_id=None, activity_id=None, id=None):
"""

# python stuff
import logging
import re
import datetime
import dateutil.parser
import json
import requests
from requests.models import PreparedRequest
import urllib.parse as urlparse
from urllib.parse import urlencode

# django stuff
from django.conf import settings
from django.core.cache import cache

# rover stuff
from .models import LTIExternalCourse
from .exceptions import LTIBusinessRuleError

# module constants
log = logging.getLogger(__name__)
WILLO_API_POST_IF_LOWER = False
WILLO_API_POST_GRADE_SKIPPED = -1
CACHE_VERSION = 1
CACHE_DEFAULT_EXPIRATION = 600
DEBUG = settings.ROVER_DEBUG

## dec-2020 DELETE ME.
DEBUG = True

def willo_api_post_grade(ext_wl_outcome_service_url, data, cached_results=True):
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

    if not ext_wl_outcome_service_url.endswith('/'):
        log.warning('api.willo_api_post_grade() - grade URL missing final slash: {url}'.format(
            url=ext_wl_outcome_service_url
        ))
        ext_wl_outcome_service_url += '/'

    data_json = json.dumps(data)

    ## check for cached results. if any exist then determine if its actually necesary
    ## to post this grade data to Willo.
    willo_outcome = willo_api_get_outcome(url=url, assignment_id=assignment_id, user_id=user_id, cached_results=cached_results)
    if not willo_api_check_column_should_post(
                rover_date=data_json.get('result_date'), 
                rover_grade=data_json.get('score'), 
                willo_date=willo_outcome[0].get('timestamp'),
                willo_grade=willo_outcome[0].get('score')
                ):
        return WILLO_API_POST_GRADE_SKIPPED

    headers = willo_api_headers(key='Content-Type', value='application/vnd.willolabs.outcome.result+json')
    response = requests.post(url=ext_wl_outcome_service_url, data=data_json, headers=headers)
    if 200 <= response.status_code <= 299:
        if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_post_grade() - successfully posted grade data: {grade_data}'.format(
            grade_data = data_json
        ))
        _cache_clear(user_id=user_id, activity_id=assignment_id, id=url)
    else:
        log.error('lti_consumers.willolabs.api.willo_api_post_grade() - encountered an error while attempting to post a grade. url: {ext_wl_outcome_service_url}, headers: {headers}, data: {grade_column_data}, which generated the following response: {response}. Msg: {msg} Text: {text}'.format(
            ext_wl_outcome_service_url=ext_wl_outcome_service_url,
            headers=headers,
            grade_column_data = data_json,
            response = response.status_code,
            msg=response.reason,
            text=response.text
        ))

    return response.status_code


def willo_api_get_outcome(url, assignment_id, user_id, cached_results=True):
    """
     Willo Grade Sync api.
     Retrieve a grade record (list) for one student for one assignment
     returns http response as a json dict

    Curl equivalent:
    -------------------------
    Get a single user's grade (now with a score in Canvas)
    curl -X GET "https://stage.willolabs.com/api/v1/outcomes/xW6w6N/e5e96b2726984abb948d58cb51387eb8/?id=tutorial-avoiding-plagiarism&user_id=f4fbc0fdf7f64daab7f5e1b09a9ebe55" \
        -H "Accept: application/vnd.willolabs.outcome.result+json" \
        -H "Authorization: Token YOURSUPERDUPERENCRYPTEDTOKEN"

    Response
    [
        {
            "activity_id": "tutorial-avoiding-plagiarism",
            "user_id": "f4fbc0fdf7f64daab7f5e1b09a9ebe55",
            "links": [
                {
                    "href": "https://stage.willolabs.com/api/v1/outcomes/xW6w6N/e5e96b2726984abb948d58cb51387eb8/?user_id=f4fbc0fdf7f64daab7f5e1b09a9ebe55&id=tutorial-avoiding-plagiarism",
                    "rel": "self"
                }
            ],
            "platform_id": "21463",
            "score": 77.0,
            "timestamp": "2021-01-06T21:40:34Z",
            "type": "result"
        }
    ]

    """
    if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_get_outcome()')
    if cached_results:
        cached_data = _cache_get(user_id=user_id, activity_id=assignment_id, id=url)
        if cached_data:
            return cached_data

    if not url.endswith('/'):
        log.warning('api.willo_get_api() - grade URL missing final slash: {url}'.format(
            url=url
        ))
        url += '/'

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
        if DEBUG: log.info('willo_api_get_outcome() - successfully retrieved grade data for user_id: {user_id}, assignment id: {assignment_id}. The response was: {response}'.format(
                assignment_id = assignment_id,
                user_id = user_id,
                response = response.json()
            ))
        _cache_set(data=response.json(), user_id=user_id, activity_id=assignment_id, id=url)
        return response.json()
    else:
        log.error('willo_api_get_outcome() - encountered an error while attempting to retrieve grade data for user_id: {user_id}, assignment id: {assignment_id}. The response was: {response}. Msg: {msg} Text: {text}'.format(
            assignment_id = assignment_id,
            user_id = user_id,
            response = response.status_code,
            msg=response.reason,
            text=response.text
        ))

    return None


def willo_api_create_column(ext_wl_outcome_service_url, data, operation="post"):
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

    operation: "post" or "patch"

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

    if operation == "post" and willo_api_check_column_does_exist(ext_wl_outcome_service_url, data):
        return 200

    if not ext_wl_outcome_service_url.endswith('/'):
        log.warning('api.willo_api_create_column() - grade URL missing final slash: {url}'.format(
            url=ext_wl_outcome_service_url
        ))
        ext_wl_outcome_service_url += '/'

    headers = willo_api_headers(
        key = 'Content-Type',
        value = 'application/vnd.willolabs.outcome.activity+json'
        )
    data_json = json.dumps(data)

    if operation == "post":
        log.info('willo_api_create_column() - posting grade column')
        response = requests.post(url=ext_wl_outcome_service_url, data=data_json, headers=headers)
    else:
        if operation == "patch":
            log.info('willo_api_create_column() - patching grade column')
            response = requests.patch(url=ext_wl_outcome_service_url, data=data_json, headers=headers)

    if 200 <= response.status_code <= 299:
        if response.status_code == 200:
            if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_create_column() - successfully {operation}ed grade column: {grade_column_data}'.format(
                    operation=operation,
                    grade_column_data = data_json
                ))
        if response.status_code == 201:
            if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_create_column() - successfully {operation}ed grade column: {grade_column_data}'.format(
                    operation=operation,
                    grade_column_data = data_json
                ))
        if response.status_code not in (200, 201):
            if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_create_column() - return code: {response} grade column: {grade_column_data}'.format(
                    grade_column_data = data_json,
                    response=response.status_code
                ))

    else:
        log.error('lti_consumers.willolabs.api.willo_api_create_column() - encountered an error while attempting to create a new grade column. url: {ext_wl_outcome_service_url}, headers: {headers}, data: {grade_column_data}, which generated the following response: {response}. Msg: {msg} Text: {text}'.format(
            ext_wl_outcome_service_url=ext_wl_outcome_service_url,
            headers=headers,
            grade_column_data = data_json,
            response = response.status_code,
            msg=response.reason,
            text=response.text
        ))

    return response.status_code



## ----------------------------------------------------------------------------
## Utility Functions
## ----------------------------------------------------------------------------
def willo_api_check_column_should_post(rover_date, rover_grade, willo_date, willo_grade):
    """
    Determine if we should post the grade data to Willo.

    If grade data already exists in Willo, and, the Willo grade timestamp is later than 
    the timestamp in Rover then this indicates that the instructor/admin has manually 
    overriden the grade data in the upstream LMS and we should therefore NOT post
    our grade data to Willo.

    In any other case we assume that we should post our grade to Willo.
    """

    ## normalize the inputs so that we can do comparative analysis
    rover_date = willo_api_date(rover_date)
    rover_grade = _float_value(rover_grade)
    willo_date = willo_api_date(willo_date)
    willo_grade = _float_value(willo_grade)

    ## if any of the grade data is missing in Willo then we definitely 
    ## should post our data.
    if willo_date is None or willo_grade is None: return True 

    ## otherwise, if the grade has not changed then we definitely
    ## should not post our data. 
    if rover_grade == willo_grade: 
        if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_check_column_should_post() - Grade data has not changed. returning False.')
        return False

    ## if our grade is lower than the grade in Willo then 
    ## we should only post our data if WILLO_API_POST_IF_LOWER is True
    if rover_grade < willo_grade:
        if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_check_column_should_post() - rover_grade < willo_grade. returning {param}'.format(
            param=WILLO_API_POST_IF_LOWER
        ))
        return WILLO_API_POST_IF_LOWER

    ## otherwise if the Willo timestamp is later than our the we definitely
    ## should post our data.
    if willo_date > rover_date: 
        if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_check_column_should_post() - willo_date > rover_date. returning False.')
        return False

    ## otherwise lets assume that we should post our data.
    return True

def willo_api_check_column_does_exist(ext_wl_outcome_service_url, data, cached_results=True):
    """
    Payload:
        data = {
            'due_date': '2020-04-29T04:59:00+00:00',
            'description': u'Lesson 4.5',
            'title': u'Lesson 4.5',
            'points_possible': 5.0,
            'type': ,
            'id': u'd7f67eb52e424909ba5ae7154d767a13'
        }

        curl -v -X GET "https://app.willolabs.com/api/v1/outcomes/DKGSf3/e42f27081648428f8995b1bca2e794ad/?id=d7f67eb52e424909ba5ae7154d767a13" \
            -H "Accept: application/vnd.willolabs.outcome.activity+json" \
            -H "Authorization: Token replaceaccesstokenhere"

    Response:
        {
            "platform_id": "21463",
            "due_date": "2019-05-31T20:00:00Z",
            "description": "sample description",
            "links": [
                {
                    "href": "https://stage.willolabs.com/api/v1/outcomes/xW6w6N/e5e96b2726984abb948d58cb51387eb8/?id=tutorial-avoiding-plagiarism",
                    "rel": "self"
                }
            ],
            "title": "Tutorial: Avoiding Plagiarism",
            "points_possible": 100.0,
            "type": "activity",
            "id": "tutorial-avoiding-plagiarism"
        }

    Arguments:
        ext_wl_outcome_service_url {[type]} -- [description]
        data {[type]} -- [description]
    """
    if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_check_column_does_exist() - Checking assignment column: {id}-{assignment}'.format(
            id=data.get('id'),
            assignment=data.get('title')
        ))

    if not ext_wl_outcome_service_url:
        raise LTIBusinessRuleError('api.willo_api_check_column_does_exist() - internal error: ext_wl_outcome_service_url has not been set for this course. Cannot continue.')

    if not data:
        raise LTIBusinessRuleError('api.willo_api_check_column_does_exist() - internal error: data dict is missing or null. Cannot continue.')

    if not ext_wl_outcome_service_url.endswith('/'):
        log.warning('api.willo_api_check_column_does_exist() - grade URL missing final slash: {url}'.format(
            url=ext_wl_outcome_service_url
        ))
        ext_wl_outcome_service_url += '/'

    req = requests.models.PreparedRequest()
    headers = willo_api_headers(
        key = 'Accept',
        value = 'application/vnd.willolabs.outcome.activity+json'
        )
    params = {
        u'id': data.get('id')
    }
    req.prepare_url(ext_wl_outcome_service_url, params)

    if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_check_column_does_exist() - headers: {headers} / url: {url}'.format(
            headers=headers,
            url=req.url
        ))
    
    if cached_results:
        cached_data = _cache_get(id=req.url)
        if cached_data:
            return True

    response = requests.get(url=req.url, headers=headers)

    if 200 <= response.status_code <= 299:

        if DEBUG: log.info('lti_consumers.willolabs.api.willo_api_check_column_does_exist() - Found assignment column: {id}-{assignment}'.format(
                id=data.get('id'),
                assignment=data.get('title')
            ))

        _cache_set(data=response.json(), id=req.url)
        # check to see if the due_date has changed.
        changed = willo_api_column_due_date_has_changed(response, data)
        changed = changed or willo_api_column_point_value_has_changed(response, data)
        if changed:
            log.info('lti_consumers.willolabs.api.willo_api_check_column_does_exist() - grade column has changed.')
            willo_api_create_column(
                ext_wl_outcome_service_url=ext_wl_outcome_service_url,
                data=data,
                operation="patch"
            )

        return True

    log.error('lti_consumers.willolabs.api.willo_api_check_column_does_exist() - Did not find assignment column: {id}-{assignment}. Return code: {status_code}. Msg: {msg} Text: {text}'.format(
        id=data.get('id'),
        assignment=data.get('title'),
        status_code=response.status_code,
        msg=response.reason,
        text=response.text
    ))
    return False

def willo_api_column_due_date_has_changed(response, data):
    """Compare the due_date in the Willo Grade Column against
    the due_date we received in the data json object.

    Args:
        response: http response. Example:
        {
            'description': '<p>MATH1081-Wk 3, Module 4 - Domain and Range</p>',
            'points_possible': 41.0,
            'type': 'activity',
            'title': 'MATH1081-Wk 3, Module 4 - Domain and Range',
            'links': [
                {
                    'href': 'https://app.willolabs.com/api/v1/outcomes/pY8QfS/79987a06bee1422a838a39d773c8e312/?id=7bbb00f7db1211ea8096f575723d2ea1',
                    'rel': 'self'
                }
                ],
            'due_date': None,
            'id': '7bbb00f7db1211ea8096f575723d2ea1'
        }

        data: json object with grade data

    Returns: boolean
    """
    try:
        log.info('lti_consumers.willolabs.api.willo_api_column_due_date_has_changed() - check due date')
        response_json = response.content.decode("utf-8")
        their_json = json.loads(response_json)
        their_due_date = willo_api_date(their_json.get('due_date'))
        our_due_date = willo_api_date(data.get('due_date'))

        if our_due_date != their_due_date:
            log.info('lti_consumers.willolabs.api.willo_api_column_due_date_has_changed() - NEED TO UPDATE DUE DATE.')
            log.info('lti_consumers.willolabs.api.willo_api_column_due_date_has_changed() - our_due_date: {our_due_date}, their_due_date: {their_due_date}, their_json: {their_json}'.format(
                our_due_date=our_due_date,
                their_due_date=their_due_date,
                their_json=their_json
            ))
            return True


    except Exception as e:
        log.info('lti_consumers.willolabs.api.willo_api_column_due_date_has_changed() - error checking dates: {e}'.format(
            e=str(e)
        ))
        pass

    return False

def willo_api_column_point_value_has_changed(response, data):
    """Compare the points_possible in the Willo Grade Column against
    the points_possible we received in the data json object.

    Args:
        response ([type]): [description]. Example:
        {
            'description': '<p>MATH1081-Wk 3, Module 4 - Domain and Range</p>',
            'points_possible': 41.0,
            'type': 'activity',
            'title': 'MATH1081-Wk 3, Module 4 - Domain and Range',
            'links': [
                {
                    'href': 'https://app.willolabs.com/api/v1/outcomes/pY8QfS/79987a06bee1422a838a39d773c8e312/?id=7bbb00f7db1211ea8096f575723d2ea1',
                    'rel': 'self'
                }
                ],
            'due_date': None,
            'id': '7bbb00f7db1211ea8096f575723d2ea1'
        }

        data ([type]): [description]

    Returns:
        [type]: [description]
    """
    try:
        response_json = response.content.decode("utf-8")
        their_json = json.loads(response_json)
        their_points = _float_value(their_json.get('points_possible'))
        our_points = _float_value(data.get('points_possible'))
        log.info('lti_consumers.willolabs.api.willo_api_column_point_value_has_changed() - check point value. Their points {their_points}, our points: {our_points}'.format(
            their_points=their_json.get('points_possible'),
            our_points=data.get('points_possible')
        ))
        if their_points != our_points:
            log.info('lti_consumers.willolabs.api.willo_api_column_point_value_has_changed() - NEED TO UPDATE POINT VALUE.')
            log.info('lti_consumers.willolabs.api.willo_api_column_due_date_has_changed() - our_points: {our_points}, their_points: {their_points}, their_json: {their_json}'.format(
                our_points=our_points,
                their_points=their_points,
                their_json=their_json
            ))
            log.info('lti_consumers.willolabs.api.willo_api_column_point_value_has_changed() - point value has changed. Their points: {their_points}, our points: {our_points}'.format(
                their_points=their_points,
                our_points=our_points
            ))
            return True


    except Exception as e:
        log.info('lti_consumers.willolabs.api.willo_api_column_point_value_has_changed() - error checking point values: {e}'.format(
            e=str(e)
        ))
        pass

    return False


def willo_api_date(dte, format='%Y-%m-%d %H:%M:%S.%f'):
    """
     Returns a string representation of a datetime in this format: "2019-06-01T00:00:00+04:00"

     dte: either a datetime or a string representation of datetime in this format: %Y-%m-%d %H:%M:%S.%f
    """

    if dte is None: return None

    if type(dte) == datetime.datetime:
        retval = dte - datetime.timedelta(microseconds=dte.microsecond)
        retval = dte.isoformat()
        return retval

    if type(dte) == str:
        try:
            # this was written to exactly coincide with the string representations of dates
            # originating from Open edX.
            retval = datetime.datetime.strptime(dte, format).isoformat()
        except:
            # if the above did not work then we probably received a string value
            # of a date from Willo Lab's REST api. These are returned in ISO 8601 format.
            retval = dateutil.parser.parse(dte)

        if type(retval) == datetime.datetime:
            retval = retval - datetime.timedelta(microseconds=retval.microsecond)
            return retval
        else:
            log.error('willo_api_date() - error converting string value {dte} to a datetime object. got value {retval} with type {tpe}'.format(
                dte=dte,
                retval=retval,
                tpe=type(retval)
            ))
            return None

    log.error('willo_api_date() - received an expected data type: {type}, value: {value}'.format(
        type=type(dte),
        value=dte
    ))
    return None


def willo_api_activity_id_from_string(activity_string):
    """
     Strip activity_string to alphanumeric characters.
     return value is used as the activity_id and id values for Willo Labs grade and column post api.
    """
    return re.sub(r'\W+', '', activity_string).lower()     # alphanumeric
    #return re.sub(r'/^[a-zA-Z0-9-_]+$/', '', activity_string).lower()


def willo_api_headers(key, value):
    """
     returns a Willo api request header
    """
    headers = {}
    headers['Authorization'] = 'Token {secret}'.format(
            secret = settings.LTI_CONSUMER_API_AUTHORIZATION_TOKEN
        )
    headers[key] = value

    if DEBUG: log.info('willo_api_headers() - {headers}'.format(
            headers = json.dumps(headers)
        ))

    return headers

def _float_value(val):
    """
    return a floating point equivalent to val
    """
    if val is None: return float(0)
    if type(val) == int: return float(val)
    if isinstance(val, str) or isinstance(val, unicode): return float(val)

    raise TypeError("invalid input type {value_type}".format(
        value_type=type(val)
    ))


# ---------------------------------------------------------
# Internal module caching. Intended to minimize superfluous 
# calls to Willo api. For example, queries to check existence
# of grade columns take upwards of 1,000 miliseconds round-trip.
# ---------------------------------------------------------
def _cache_pk(user_id=None, activity_id=None, id=None):
    """
    Create a standardized module-safe cache key from any combination
    of module data identifiers
    """
    return 'third_party_auth.lti_consumers.api.{user_id}.{activity_id}.{id}'.format(
        user_id=user_id,
        activity_id=activity_id,
        id=id
    )

def _cache_get(user_id=None, activity_id=None, id=None):
    """
    Query the cache using any combination of module data identifiers
    """
    cache_key = _cache_pk(user_id, activity_id, id)
    cached_data = cache.get(key=cache_key, default=None, version=CACHE_VERSION)
    if cached_data:
        return json.loads(cached_data)
    return None

def _cache_set(data, timeout=CACHE_DEFAULT_EXPIRATION, user_id=None, activity_id=None, id=None):
    """
    Clear cache of any existing data and reset with a new cache expiration
    """
    cache_key = _cache_pk(user_id, activity_id, id)
    cache.delete(key=cache_key, version=CACHE_VERSION)
    cache.set(key=cache_key, value=data, timeout=timeout, version=CACHE_VERSION)

def _cache_clear(user_id=None, activity_id=None, id=None):
    """
    Clear cache of any existing data and reset with a new cache expiration
    """
    cache_key = _cache_pk(user_id, activity_id, id)
    cache.delete(key=cache_key, version=CACHE_VERSION)
