"""
# mcdaniel Aug-2020
Unit tests for LTIParams parser

Reference: https://docs.python.org/3/library/unittest.html
"""

# python stuff

# django stuff
from django.test import TestCase

# open edx stuff
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin
from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey, UsageKey

# our stuff
from common.djangoapps.third_party_auth.lti_consumers.lti_params import LTIParams
from .util import s3_list_contents, lti_params_from_s3, lti_params_from_fs

LTI_PARAMS_S3_BUCKET = 'tests.roverbyopenstax.org'
LTI_PARAMS_S3_PATH = 'common/djangoapps/third_party_auth/lti_consumers/tests/data/tpa_lti_params/'
USER_MODEL = get_user_model()


def test_all_s3_files():
    """Sequentially download and test
    all tpa_lti_params test files
    """
    test_files = s3_list_contents(
        bucket_name=LTI_PARAMS_S3_BUCKET,
        path=LTI_PARAMS_S3_PATH
        )

    for filename in test_files:
        full_filename = LTI_PARAMS_S3_PATH + filename
        lti_params = lti_params_from_s3(
            bucket=LTI_PARAMS_S3_BUCKET,
            file_name=full_filename
            )

        print('Testing {filename}'.format(
            filename=filename
        ))

        unit_test = UnitTestLTIParams(lti_params=lti_params)

        # these are our basic structural integrity and value validations
        # for an incoming lti_params json object originating from
        # an LTI Consumer of Rover
        unit_test.test_validity()
        unit_test.test_required_parameters()
        unit_test.is_willo_lti()
        unit_test.test_faculty_status()


class UnitTestLTIParams(TestCase):
    """
    Unit tests for third_party_auth LTI auth providers. Tests parsing of JSON objects
    passed to Rover by LTI clients during authentication.

    Runs as a Django Unit Test if no lti_params object is provided
    """
    def __init__(self, lti_params=None):
        self.lti_params = None

        if lti_params:
            self.lti_params = LTIParams(lti_params)

    def setUp(self):
        super(UnitTestLTIParams, self).setUp()

    def test_generic_values(self):
        lti_params = LTIParams(lti_params_from_fs('generic.json'))
        # basic property value testing
        self.assertEqual(lti_params.context_id, 'dcabeb60badb4385ae0ad0635f243acc')
        self.assertEqual(lti_params.context_label, '4199-11983')
        self.assertEqual(lti_params.custom_tpa_next, '/account/finish_auth?course_id=course-v1%3AKU%2BMATH101%2BSpring2020_Sample_Section1&enrollment_action=enroll&email_opt_in=false')
        self.assertEqual(lti_params.ext_wl_launch_url, 'https://app.willolabs.com/launch/DKGSf3/3VNbxq')

        # derived property values
        self.assertEqual(lti_params.faculty_status, 'no_faculty_info')
        self.assertEqual(lti_params.course_id, 'course-v1:AKU+BMATH101+BSpring2020_Sample_Section1')
        self.assertTrue(lti_params.is_valid)
        self.assertTrue(lti_params.is_willolabs)

    def test_invalid(self):
        lti_params = LTIParams(lti_params_from_fs('invalid.json'))
        self.assertFalse(lti_params.is_valid)

    def test_instructor(self):
        lti_params = LTIParams(lti_params_from_fs('instructor.json'))
        self.assertEqual(lti_params.faculty_status, 'confirmed_faculty')

    def test_not_willo(self):
        lti_params = LTIParams(lti_params_from_fs('not-willo.json'))
        self.assertFalse(lti_params.is_willolabs)

    def test_validity(self):
        if not self.lti_params: return
        self.assertIsInstance(self.lti_params.dictionary, dict)
        self.assertTrue(self.lti_params.is_valid)

    def test_required_parameters(self):
        if not self.lti_params: return

        # class properties
        self.assertIsNotNone(self.lti_params.course_id)
        self.assertIsNotNone(self.lti_params.faculty_status)
        self.assertIsNotNone(self.lti_params.dictionary)

        # lti parameters from json dict
        self.assertIsNotNone(self.lti_params.context_id)
        self.assertIsNotNone(self.lti_params.context_label)
        self.assertIsNotNone(self.lti_params.context_title)
        self.assertIsNotNone(self.lti_params.custom_tpa_next)
        self.assertIsNotNone(self.lti_params.ext_wl_launch_key)
        self.assertIsNotNone(self.lti_params.ext_wl_launch_url)
        self.assertIsNotNone(self.lti_params.ext_wl_outcome_service_url)
        self.assertIsNotNone(self.lti_params.lis_person_contact_email_primary)
        self.assertIsNotNone(self.lti_params.lis_person_name_family)
        self.assertIsNotNone(self.lti_params.lis_person_name_full)
        self.assertIsNotNone(self.lti_params.lis_person_name_given)
        self.assertIsNotNone(self.lti_params.lti_version)
        self.assertIsNotNone(self.lti_params.oauth_consumer_key)
        self.assertIsNotNone(self.lti_params.oauth_nonce)
        self.assertIsNotNone(self.lti_params.oauth_signature_method)
        self.assertIsNotNone(self.lti_params.oauth_timestamp)
        self.assertIsNotNone(self.lti_params.oauth_version)
        self.assertIsNotNone(self.lti_params.roles)
        self.assertIsNotNone(self.lti_params.user_id)

    def is_willo_lti(self):
        if not self.lti_params: return
        self.assertTrue(self.lti_params.is_willolabs)

    def test_faculty_status(self):
        if not self.lti_params: return
        valid_responses = ['confirmed_faculty', 'no_faculty_info']
        self.assertIsInstance(self.lti_params.faculty_status, valid_responses)
