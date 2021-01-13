"""
Jan-2021
Willo api enhancements

API calls:
------------------
willo_api_create_column(ext_wl_outcome_service_url, data, operation="post"):
willo_api_post_grade(ext_wl_outcome_service_url, data):
willo_api_get_outcome(url, assignment_id, user_id):

Utils:
------------------
- willo_api_check_column_should_post():
- willo_api_check_column_does_exist(ext_wl_outcome_service_url, data):
(PENDING) willo_api_column_due_date_has_changed(response, data):
(PENDING) willo_api_column_point_value_has_changed(response, data):
- willo_api_date(dte, format='%Y-%m-%d %H:%M:%S.%f'):
x willo_api_activity_id_from_string(activity_string):
x willo_api_headers(key, value):

- _float_value(val):
- _cache_pk(user_id=None, activity_id=None, id=None):
- _cache_get(user_id=None, activity_id=None, id=None):
- _cache_set(data, timeout=CACHE_DEFAULT_EXPIRATION, user_id=None, activity_id=None, id=None):

To run tests:
------------------------------------------------
1. open an Open edX Django shell, as follows:

sudo -H -u edxapp bash
cd ~
source edxapp_env
source venvs/edxapp/bin/activate
cd edx-platform
./manage.py lms shell

2. import this module to the shell, then execute test()
from common.djangoapps.third_party_auth.lti_consumers.willolabs.tests.willo_api import test
retval = test()
"""

import datetime
import json

from ..api import (
    # api methods
    willo_api_get_outcome,

    # mid-level utility methods
    willo_api_check_column_should_post,
    willo_api_check_column_does_exist,
    willo_api_column_due_date_has_changed,
    willo_api_column_point_value_has_changed,

    # low-level utility methods
    willo_api_date,
    willo_api_activity_id_from_string,
    _float_value,
    _cache_pk,
    _cache_get,
    _cache_set,
    _cache_clear
    )

def test():
    """
    execute complete test bank.
    """
    test_float()
    test_cache()
    test_willo_api_date()
    test_willo_api_check_column_should_post()
    test_willo_api_check_column_does_exist()
    test_willo_api_get_outcome()

def test_float():
    print("test_float() - BEGIN")
    flt = _float_value('1.123')
    print("Test 1: type of flt is {tpe}. value of flt is {val}".format(
        tpe=type(flt),
        val=flt
    ))

    flt = _float_value(456)
    print("Test 2: type of flt is {tpe}. value of flt is {val}".format(
        tpe=type(flt),
        val=flt
    ))

    flt = _float_value("ABC")
    print("Test 3: type of flt is {tpe}. value of flt is {val}".format(
        tpe=type(flt),
        val=flt
    ))
    print("test_float() - END")

def test_cache():
    print("test_cache() - BEGIN")
    user_id=123345
    activity_id="abcdefghijklmnop1234567890"
    id="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    data = {
        "id": 123456789,
        "stuff": "Some stuff goes here"
    }

    pk = _cache_pk(user_id=user_id, activity_id=activity_id, id=id)
    print("pk={pk}".format(pk=pk))

    _cache_set(data=data, user_id=user_id, activity_id=activity_id, id=id)
    cached_data = _cache_get(user_id=user_id, activity_id=activity_id, id=id)
    print("after setting cache cached_data={cached_data}".format(cached_data=cached_data))

    _cache_clear(user_id=user_id, activity_id=activity_id, id=id)
    cached_data = _cache_get(user_id=user_id, activity_id=activity_id, id=id)
    print("after clearing cache cached_data={cached_data}".format(cached_data=cached_data))
    print("test_cache() - END")

def test_willo_api_date():
    print("test_willo_api_date() - BEGIN")
    dte = datetime.datetime.now()
    willo_date = willo_api_date(dte)
    print("dte={dte} / willo date={willo_date}".format(
        dte=dte,
        willo_date=willo_date
    ))
    print("test_willo_api_date() - END")

def test_willo_api_check_column_should_post():
    print("test_willo_api_check_column_should_post() - BEGIN")
    dte_earlier = willo_api_date(datetime.datetime.now() - datetime.timedelta(days=1))
    dte_later = willo_api_date(datetime.datetime.now())

    rover_date = dte_later
    rover_grade = 10.0
    willo_date = None
    willo_grade = None
    retval = willo_api_check_column_should_post(rover_date=rover_date, rover_grade=rover_grade, willo_date=willo_date, willo_grade=willo_grade)
    print("test 1 - expecting True, returned {retval}".format(
        retval=retval
    ))

    rover_date = dte_later
    rover_grade = 10.0
    willo_date = rover_date
    willo_grade = rover_grade
    retval = willo_api_check_column_should_post(rover_date=rover_date, rover_grade=rover_grade, willo_date=willo_date, willo_grade=willo_grade)
    print("test 2 - expecting False, returned {retval}".format(
        retval=retval
    ))

    rover_date = dte_later
    rover_grade = 10.0
    willo_date = rover_date
    willo_grade = 11.0
    retval = willo_api_check_column_should_post(rover_date=rover_date, rover_grade=rover_grade, willo_date=willo_date, willo_grade=willo_grade)
    print("test 3 - expecting False, returned {retval}".format(
        retval=retval
    ))

    rover_date = dte_earlier
    rover_grade = 10.0
    willo_date = dte_later
    willo_grade = 11.0
    retval = willo_api_check_column_should_post(rover_date=rover_date, rover_grade=rover_grade, willo_date=willo_date, willo_grade=willo_grade)
    print("test 4 - expecting False, returned {retval}".format(
        retval=retval
    ))

    rover_date = dte_later
    rover_grade = 12.0
    willo_date = dte_earlier
    willo_grade = 11.0
    retval = willo_api_check_column_should_post(rover_date=rover_date, rover_grade=rover_grade, willo_date=willo_date, willo_grade=willo_grade)
    print("test 5 - expecting True, returned {retval}".format(
        retval=retval
    ))
    print("test_willo_api_check_column_should_post() - END")


def test_willo_api_check_column_does_exist():
    print("test_willo_api_check_column_does_exist() - BEGIN")
    data = {
        'due_date': '2020-04-29T04:59:00+00:00',
        'description': u'Lesson 4.5',
        'title': u'Lesson 4.5',
        'points_possible': 5.0,
        'type': ,
        'id': u'd7f67eb52e424909ba5ae7154d767a13'
    }

    ext_wl_outcome_service_url_good = "https://app.willolabs.com/api/v1/outcomes/DKGSf3/e42f27081648428f8995b1bca2e794ad/"
    ext_wl_outcome_service_url_bad = "https://app.willolabs.com/api/v1/outcomes/DKGSf3/e42f27081648428f8995XXXXXBAD-DATA/"

    retval = willo_api_check_column_does_exist(ext_wl_outcome_service_url=ext_wl_outcome_service_url_good, good_data, cached_results=True):
    print("test 1 - expecting True, returned {retval}".format(
        retval=retval
    ))
    retval = willo_api_check_column_does_exist(ext_wl_outcome_service_url=ext_wl_outcome_service_url_good, good_data, cached_results=False):
    print("test 2 - expecting True, returned {retval}".format(
        retval=retval
    ))

    retval = willo_api_check_column_does_exist(ext_wl_outcome_service_url=ext_wl_outcome_service_url_bad, bad_data, cached_results=True):
    print("test 3 - expecting False, returned {retval}".format(
        retval=retval
    ))
    retval = willo_api_check_column_does_exist(ext_wl_outcome_service_url=ext_wl_outcome_service_url_bad, bad_data, cached_results=False):
    print("test 4 - expecting False, returned {retval}".format(
        retval=retval
    ))
    print("test_willo_api_check_column_does_exist() - END")

def test_willo_api_get_outcome():
    data = {
        "activity_id": "d7f67eb52e424909ba5ae7154d767a13",
        "id": "block-v1:OpenStax+PCL101+2020_Tmpl_RevY+type@problem+block@669e8abe089b4a69b3a2565402d27cad",
        "points_possible": 5.0,
        "result_date": "2020-04-24T19:12:19.454723+00:00",
        "score": 0.5,
        "type": "result",
        "user_id": "7010d877b3b74f39a6cbf89f9c3819ce"
    }
    url = 'https://app.willolabs.com/api/v1/outcomes/DKGSf3/e42f27081648428f8995b1bca2e794ad/'
    assignment_id = data.get('activity_id')
    user_id = data.get('user_id')
    retval = willo_api_get_outcome(url=url, assignment_id=assignment_id, user_id=user_id)
    print("test_willo_api_get_outcome() - retval={retval}".format(
        retval=retval
    ))