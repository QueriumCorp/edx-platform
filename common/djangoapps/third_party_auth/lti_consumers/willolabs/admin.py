# -*- coding: utf-8 -*-
"""
mcdaniel dec-2019
Willo LTI Grade Sync tables
"""
from __future__ import absolute_import
from django.contrib import admin

from .models import (
    LTIExternalCourse,
    LTIExternalCourseEnrollment,
    LTIExternalCourseEnrollmentGrades
    )


class LTIExternalCourseAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course
    """
    readonly_fields=(u'created', u'updated', )

admin.site.register(LTIExternalCourse, LTIExternalCourseAdmin)

class LTIExternalCourseEnrollmentAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Enrollment
    """
    readonly_fields=(u'created', u'updated', )

admin.site.register(LTIExternalCourseEnrollment, LTIExternalCourseEnrollmentAdmin)

class LTIExternalCourseEnrollmentGradesAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Enrollment, Grades
    """
    readonly_fields=(u'created', u'updated', )

admin.site.register(LTIExternalCourseEnrollmentGrades, LTIExternalCourseEnrollmentGradesAdmin)
