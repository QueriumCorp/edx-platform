"""
mcdaniel dec-2019
Willo LTI Grade Sync tables
"""
from django.contrib import admin

from third_party_auth.lti.willolabs.models import (
    LTIWilloLabsExternalCourse,
    LTIWilloLabsExternalCourseEnrollment,
    LTIWilloLabsExternalCourseEnrollmentGrades
    )


class LTIWilloLabsExternalCourseAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course
    """
    readonly_fields=(u'created', u'updated', )

admin.site.register(LTIWilloLabsExternalCourse, LTIWilloLabsExternalCourseAdmin)

class LTIWilloLabsExternalCourseEnrollmentAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Enrollment
    """
    readonly_fields=(u'created', u'updated', )

admin.site.register(LTIWilloLabsExternalCourseEnrollment, LTIWilloLabsExternalCourseEnrollmentAdmin)

class LTIWilloLabsExternalCourseEnrollmentGradesAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Enrollment, Grades
    """
    readonly_fields=(u'created', u'updated', )

admin.site.register(LTIWilloLabsExternalCourseEnrollmentGrades, LTIWilloLabsExternalCourseEnrollmentGradesAdmin)
