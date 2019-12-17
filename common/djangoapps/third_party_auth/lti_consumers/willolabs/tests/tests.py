# -*- coding: utf-8 -*-
"""
# mcdaniel dec-2019
Unit tests for third_party_auth LTI - Willo Labs Grade Sync
"""

from __future__ import absolute_import
import unittest
import json

#import requests
#from oauthlib.common import Request
#from third_party_auth.lti import LTI_PARAMS_KEY, LTIAuthBackend

from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin
from django.contrib.auth import get_user_model
from third_party_auth.lti.willolabs.provisioners import CourseProvisioner
from third_party_auth.lti.willolabs.utils import is_willo_lti

LTI_PARAMS_KEY = 'tpa-lti-params'
LTI_PARAMS_JSON_FILE = 'data/tpa-lti-params-willo-canvas-learner.json'
USER_MODEL = get_user_model()

class UnitTestLTIWilloLabGradeSync(unittest.TestCase, ThirdPartyAuthTestMixin):
    """
    Unit tests for third_party_auth LTI auth providers
    """

    def test_course_provisioner_instantiation(self):
        user = USER_MODEL.objects.get(username="mcdaniel")
        with open(LTI_PARAMS_JSON_FILE) as json_file:
            data = json.load(json_file)
        lti_params = data[LTI_PARAMS_KEY]

        course_provisioner = CourseProvisioner(user, lti_params)
        course_provisioner.check_enrollment()

    def test_is_willo_lti(self):
        user = USER_MODEL.objects.get(username="mcdaniel")
        with open(LTI_PARAMS_JSON_FILE) as json_file:
            data = json.load(json_file)
        lti_params = data[LTI_PARAMS_KEY]

        is_willo = is_willo_lti(lti_params)
        self.assertEquals(is_willo, True)

    def test_is_not_willo_lti(self):
        with open(LTI_PARAMS_JSON_FILE) as json_file:
            data = json.load(json_file)
        lti_params = data[LTI_PARAMS_KEY]

        if 'ext_wl_launch_url' in lti_params: 
            del lti_params['ext_wl_launch_url']

        is_willo = is_willo_lti(lti_params)
        self.assertEquals(is_willo, False)


def local_tests():
    tests = UnitTestLTIWilloLabGradeSync()
    tests.test_course_provisioner_instantiation()
    tests.test_is_willo_lti()

if __name__ == "__main__":
    local_tests()

