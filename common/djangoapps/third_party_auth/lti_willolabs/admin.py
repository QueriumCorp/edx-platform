"""
mcdaniel dec-2019
Willo LTI Grade Sync tables
"""
from django.contrib import admin

from third_party_auth.lti_willolabs.models import (
    LTIWilloLabsGradeSynCourse,
    LTIWilloLabsGradeSynCourseEnrollment,
    LTIWilloLabsGradeSynCourseEnrollmentGrades
    )


class LTIWilloLabsGradeSynCourseAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course
    """
    readonly_fields=(u'created', u'updated', )

admin.site.register(LTIWilloLabsGradeSynCourse, LTIWilloLabsGradeSynCourseAdmin)

class LTIWilloLabsGradeSynCourseEnrollmentAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Enrollment
    """
    readonly_fields=(u'created', u'updated', )

admin.site.register(LTIWilloLabsGradeSynCourseEnrollment, LTIWilloLabsGradeSynCourseEnrollmentAdmin)

class LTIWilloLabsGradeSynCourseEnrollmentGradesAdmin(admin.ModelAdmin):
    """
    LTI Willo Labs - Course Enrollment, Grades
    """
    readonly_fields=(u'created', u'updated', )

admin.site.register(LTIWilloLabsGradeSynCourseEnrollmentGrades, LTIWilloLabsGradeSynCourseEnrollmentGradesAdmin)
