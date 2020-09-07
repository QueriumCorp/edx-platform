"""
# mcdaniel Aug-2020
Unit tests for LTICacheManager cache objects

Reference: https://docs.python.org/3/library/unittest.html
"""
# python stuff

# django stuff
from django.test import TestCase

# open edx stuff
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin
from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey, UsageKey

USER_MODEL = get_user_model()


class UnitTestLTICacheManager(TestCase):

    def setUp(self):
        super(UnitTestLTICacheManager, self).setUp()

    def test_inbound_lti_params(self):
        self.assertEqual(True, True)
