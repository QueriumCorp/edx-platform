# -*- coding: utf-8 -*-
"""
  Willo LTI Grade Sync tables

  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020
"""
from __future__ import absolute_import
from django.contrib import admin

from .models import (
    LTIExternalCourse,
    LTIExternalCourseEnrollment,
    LTIExternalCourseEnrollmentGrades,
    LTIExternalCourseAssignments,
    LTIExternalCourseAssignmentProblems,
    )


class LTIExternalCourseAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course
    """
    list_display = (
        'context_id',
        'enabled',
        'course_id',
        'context_title',
        'context_label',
        'created',
        'modified',
        'ext_wl_launch_key',
        'ext_wl_launch_url',
        'ext_wl_version',
        'ext_wl_outcome_service_url',
        'custom_api_domain',
        'custom_course_id',
        'custom_course_startat',
        'tool_consumer_info_product_family_code',
        'tool_consumer_info_version',
        'tool_consumer_instance_contact_email',
        'tool_consumer_instance_guid',
        'tool_consumer_instance_name',
    )
    readonly_fields=(u'created', u'modified' )

admin.site.register(LTIExternalCourse, LTIExternalCourseAdmin)

class LTIExternalCourseEnrollmentAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Enrollment
    """
    list_display = (
        'course',
        'user',
        'created',
        'modified',
        'user_id',
        'custom_user_id',
        'custom_user_login_id',
        'custom_person_timezone',
        'ext_roles',
        'ext_wl_privacy_mode',
        'lis_person_contact_email_primary',
        'lis_person_name_family',
        'lis_person_name_full',
        'lis_person_name_given',
    )      
    readonly_fields=(u'created', u'modified' )

admin.site.register(LTIExternalCourseEnrollment, LTIExternalCourseEnrollmentAdmin)

class LTIExternalCourseEnrollmentGradesAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Enrollment, Grades
    """
    list_display = (
        'id',
        'created',
        'modified',
        'synched',
        'course_enrollment',
        'usage_key',
        'section_url',
        'earned_all',
        'possible_all',
        'earned_graded',
        'possible_graded'
    )
    readonly_fields=(u'created', u'modified' )

admin.site.register(LTIExternalCourseEnrollmentGrades, LTIExternalCourseEnrollmentGradesAdmin)


class LTIExternalCourseAssignmentProblemsAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Assignment Problems
    """
    list_display = (
        'course_assignment',
        'usage_key',
        'created',
        'modified'
    )
    readonly_fields=(u'created', u'modified')

admin.site.register(LTIExternalCourseAssignmentProblems, LTIExternalCourseAssignmentProblemsAdmin)

class LTIExternalCourseAssignmentsAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Assignments
    """
    list_display = (
        'course',
        'url',
        'display_name',
        'created',
        'modified'
    )
    readonly_fields=(u'created', u'modified')

admin.site.register(LTIExternalCourseAssignments, LTIExternalCourseAssignmentsAdmin)
