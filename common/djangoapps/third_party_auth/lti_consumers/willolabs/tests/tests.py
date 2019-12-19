# -*- coding: utf-8 -*-
"""
# mcdaniel dec-2019
Unit tests for third_party_auth LTI - Willo Labs Grade Sync
"""

from __future__ import absolute_import
import os
import json
from collections import OrderedDict

#import requests
#from oauthlib.common import Request
#from third_party_auth.lti import LTI_PARAMS_KEY, LTIAuthBackend
from django.test import TestCase

from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin
from django.contrib.auth import get_user_model
from third_party_auth.lti_consumers.willolabs.provisioners import CourseProvisioner
from third_party_auth.lti_consumers.willolabs.tasks import post_grades
from third_party_auth.lti_consumers.willolabs.utils import is_willo_lti
from opaque_keys.edx.keys import CourseKey

LTI_PARAMS_KEY = 'tpa-lti-params'
LTI_PARAMS_JSON_FILE = 'data/tpa-lti-params-willo-canvas-learner.json'
USER_MODEL = get_user_model()

class UnitTestLTIWilloLabGradeSync(TestCase):
    """
    Unit tests for third_party_auth LTI auth providers
    """
    def __init__(self):
        print('setup()')
        self.PATH = os.path.dirname(__file__) + '/'
        self.provisioner = None
        self.init()

    def init(self):
        with open(self.PATH + LTI_PARAMS_JSON_FILE) as json_file:
            data = json.load(json_file)
        self.lti_params = data[LTI_PARAMS_KEY]

    def runTest(self):
        print('runTest()')
        self.provisioner_instantiation()
        self.test_lti_params()
        self.test_user()
        self.test_context_id()
        self.is_willo_lti()
        self.is_not_willo_lti()

    def provisioner_instantiation(self):
        user = USER_MODEL.objects.get(username="mcdaniel")
        course_id = CourseKey.from_string('course-v1:ABC+OS9471721_9626+01')
        lti_params = self.lti_params

        self.provisioner = CourseProvisioner(
            user=user, 
            lti_params=lti_params, 
            course_id=course_id
            )
        self.provisioner.check_enrollment()

    def test_post_grades(self):
        user = USER_MODEL.objects.get(username="mcdaniel")
        lti_params = self.lti_params

        course_id = 'course-v1:ABC+OS9471721_9626+01'
        course_key = CourseKey.from_string(course_id)
        username = user.username
        subsection_usage_key = "SHOOBY DOOBY DO WAH"
        subsection_grade={
            'this': '0',            
            'that': '1',            
            'the_other_thing': '2',            
        }

        """
        recalculate_subsection_grade_kwargs = OrderedDict([
            ('user_id', user.id),
            ('course_id', unicode('course-v1:ABC+OS9471721_9626+01')),
            ('usage_id', unicode(self.problem.location)),
            ('anonymous_user_id', 5),
            ('only_if_higher', None),
            ('expected_modified_time', self.frozen_now_timestamp),
            ('score_deleted', False),
            ('event_transaction_id', unicode(get_event_transaction_id())),
            ('event_transaction_type', u'willolabs.post_grades'),
            ('score_db_table', ScoreDatabaseTableEnum.courseware_student_module),
        ])
        """

        post_grades(
            username=username,
            course_id=course_id,
            subsection_usage_key=subsection_usage_key,
            subsection_grade=subsection_grade,
        )

    def test_lti_params(self):
        self.assertEquals(self.provisioner.lti_params['context_id'], u'e14751571da04dd3a2c71a311dda2e1b')
        self.assertEquals(self.provisioner.lti_params['tool_consumer_info_product_family_code'], u'canvas')
        self.assertEquals(self.provisioner.lti_params['lis_person_contact_email_primary'], u'rover_student@willolabs.com')
        
    def test_user(self):
        self.assertEquals(user, self.provisioner.user)

    def test_context_id(self):
        self.assertEquals(self.provisioner.context_id, u'e14751571da04dd3a2c71a311dda2e1b')

    def is_willo_lti(self):
        self.init()
        is_willo = is_willo_lti(lti_params)
        self.assertEquals(is_willo, True)

    def is_not_willo_lti(self):
        self.init()

        if 'ext_wl_launch_url' in lti_params: 
            del lti_params['ext_wl_launch_url']

        is_willo = is_willo_lti(lti_params)
        self.assertEquals(is_willo, False)
        self.init()

