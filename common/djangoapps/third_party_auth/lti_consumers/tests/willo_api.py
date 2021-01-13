"""
Jan-2021
Willo api enhancements

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
import datetime
import json

from ..api import (
    willo_api_check_column_should_post,
    willo_api_check_column_does_exist,
    willo_api_column_due_date_has_changed,
    willo_api_column_point_value_has_changed,

    willo_api_date,
    willo_api_activity_id_from_string,
    _float_value,
    _cache_pk,
    _cache_get,
    _cache_set,
    _cache_clear
    )


def test_float():
    flt = _float_value('1.123')
    print("type of flt is {tpe}. value of flt is {val}".format(
        tpe=type(flt),
        val=flt
    ))

    flt = _float_value(456)
    print("type of flt is {tpe}. value of flt is {val}".format(
        tpe=type(flt),
        val=flt
    ))

def test_cache():
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

def test_willo_api_date():
    dte = datetime.datetime.now()
    willo_date = willo_api_date(dte)
    print("dte={dte} / willo date={willo_date}".format(
        dte=dte,
        willo_date=willo_date
    ))

def test_willo_api_check_column_should_post():
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


def test_willo_api_check_column_does_exist():
    return None
