# -*- coding: utf-8 -*-
"""
  Constants for LTI Willo Labs Grade Sync support in third_party_auth

  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020

"""
from __future__ import absolute_import
import os

WORKING_PATH = os.path.dirname(os.path.abspath(__file__))

# from the LTI role vocabulary
# https://www.imsglobal.org/specs/ltiv1p1/implementation-guide#toc-8
# you need to decide which roles you'll treat as instructor, but here is
# a reasonable starting point
WILLO_INSTRUCTOR_ROLES = set((
    'Instructor',
    'urn:lti:role:ims/lis/Instructor',
    'urn:lti:instrole:ims/lis/Instructor',
    'Faculty',
    'urn:lti:instrole:ims/lis/Faculty',
    'ContentDeveloper',
    'urn:lti:role:ims/lis/ContentDeveloper',
    'TeachingAssistant',
    'urn:lti:role:ims/lis/TeachingAssistant',
    'Administrator',
    'urn:lti:role:ims/lis/Administrator',
    'urn:lti:instrole:ims/lis/Administrator',
    'urn:lti:sysrole:ims/lis/Administrator'
))

# each of the following is an example of what can be expected in
# a single LTI message
WILLO_ROLES_PARAM_EXAMPLES = (
    'Learner',
    'urn:lti:instrole:ims/lis/Student,Student,urn:lti:instrole:ims/lis/Learner,Learner',
    'Instructor',
    'Instructor,urn:lti:sysrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Administrator',
    'TeachingAssistant',
    'urn:lti:instrole:ims/lis/Administrator'
)

WILLO_DOMAINS = (
    'test.willolabs.com', 
    'stage.willolabs.com', 
    'app.willolabs.com'
)

LTI_CACHE_TABLES = (
    'LTIExternalCourse', 
    'LTIExternalCourseEnrollment', 
    'LTIExternalCourseEnrollmentGrades',
    'LTIExternalCourseAssignments',
    'LTIExternalCourseAssignmentProblems'
)
