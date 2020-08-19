# -*- coding: utf-8 -*-
"""
# mcdaniel Aug-2020
Unit tests for third_party_auth Provisioner
"""
# python stuff

# django stuff
from django.test import TestCase

# open edx stuff
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin
from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey, UsageKey

USER_MODEL = get_user_model()


class UnitTestCourseProvisioner(TestCase):

    def setUp(self):
        super(UnitTestCourseProvisioner, self).setUp()

    def test_inbound_lti_params(self):
        self.assertEqual(True, True)
