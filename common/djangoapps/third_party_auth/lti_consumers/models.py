#from __future__ import absolute_import
# -*- coding: utf-8 -*-
"""
  LTI Integration for Willo Labs Grade Sync.
  Models used to implement LTI External support in third_party_auth

  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020
"""

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from model_utils.models import TimeStampedModel

# mcdaniel may-2020: field was refactored in juniper.rc3
#-----------------
#from lms.djangoapps.coursewarehistoryextended.fields import UnsignedBigIntAutoField
from lms.djangoapps.courseware.fields import UnsignedBigIntAutoField
#-----------------

from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from .constants import LTI_CACHE_TABLES_LIST
"""
https://github.com/edx/opaque-keys
https://github.com/edx/edx-platform/wiki/Opaque-Keys-(Locators)

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
courses_summary = modulestore().get_course_summaries()
"""

import logging
log = logging.getLogger(__name__)
DEBUG = settings.ROVER_DEBUG

"""
LTI Grade Sync - Phase II models
"""
class LTIConfigurations(TimeStampedModel):
    """
    LTI configuration master record for field-to-field mapping data.
    Phase II model. provides a way to support multiple versions of
    LTI integration field-level mapping.
    """
    id = models.AutoField(primary_key=True)

    name = models.CharField(
        help_text="Example: KU - Willo Labs - Blackboard",
        max_length=255,
        blank=True,
        null=False,
        )

    comments = models.TextField()

    class Meta(object):
        verbose_name = "LTI Configurations"
        verbose_name_plural = verbose_name
        #ordering = ('-fetched_at', )

    def __str__(self):
        return self.name

class LTIConfigurationParams(TimeStampedModel):
    """
    LTI configuration detail field-to-field mapping data.
    Phase II model. provides a way to support multiple versions of
    LTI integration field-level mapping.
    """
    id = models.AutoField(primary_key=True)

    configuration = models.ForeignKey(LTIConfigurations, on_delete=models.CASCADE)

    table_name = models.CharField(
        help_text="Example: LTIExternalCourseEnrollment",
        max_length=255,
        choices=LTI_CACHE_TABLES_LIST,
        blank=True,
        null=False,
        )

    internal_field = models.CharField(
        help_text="Example: ext_wl_launch_key",
        max_length=255,
        blank=True,
        null=False,
        )

    external_field = models.CharField(
        help_text="Example: ext_wl_launch_key",
        max_length=255,
        blank=True,
        null=False,
        )

    comments = models.TextField()

    class Meta(object):
        verbose_name = "LTI Configuration Parameters"
        verbose_name_plural = verbose_name
        #ordering = ('-fetched_at', )

    def __str__(self):
        return self.table_name + '.' + self.internal_field

class LTIInternalCourse(TimeStampedModel):
    """
    Rover course master record. Manually populated. Fk to Open edX course in modulestore.
    Phase II model. provides a way to explicitly enable/disable courses for LTI grade sync,
    and also provides a way to support independent per-course LTI integration field mapping.
    """
    course_id = CourseKeyField(
        max_length=255,
        help_text="Rover Course Key (Opaque Key). " \
            "Based on Institution, Course, Section identifiers. Example: course-v1:edX+DemoX+Demo_Course",
        blank=False,
        default=None,
        primary_key=True
        )

    enabled = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="True if LTI Grade Sync should be enabled for courses in this institution."
        )

    lti_configuration = models.ForeignKey(
        LTIConfigurations,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Field mapping configuration to use for this Rover course."
        )

    class Meta(object):
        verbose_name = "LTI Internal Rover Course"
        verbose_name_plural = verbose_name + "s"
        #ordering = ('-fetched_at', )

    def __str__(self):
        return self.course_id.html_id()

    def clean(self, *args, **kwargs):
        """Improvising a way to do a Fk constraint on the course_id

        Raises:
            ValidationError: [description]
        """
        super(LTIInternalCourse, self).clean(*args, **kwargs)
        try:
            is_this_a_valid_course_key = CourseKey.from_string(self.course_id)
        except InvalidKeyError:
            raise ValidationError('Not a valid course key.')

"""
---------------------------------------------------------------------------------------------------------
LTI Grade Sync - Phase I models
---------------------------------------------------------------------------------------------------------
"""
class LTIExternalCourse(TimeStampedModel):
    """
    Phase I model
    Course data originating from Willo Labs LTI authentications by students entering Rover
    from a third party LMS like Canvas, Moodle, Blackboard, etc.
    """
    context_id = models.CharField(
        #verbose_name="Context ID",
        help_text="This is the unique identifier of the Willo Labs integration, passed via" \
            "from tpa-lti-params. Course runs from external LMS' are intended to be unique." \
            "Example: e14751571da04dd3a2c71a311dda2e1b",
        max_length=255,
        blank=False,
        primary_key=True
        )  # This is the key for lookups in this table

    enabled = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="True if grade results for this course should be posted to Willo Labs Grade Sync API."
        )

    course_id = models.ForeignKey(
        LTIInternalCourse,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Rover Course Key (Opaque Key). " \
            "Based on Institution, Course, Section identifiers. Example: course-v1:edX+DemoX+Demo_Course"
        )

    context_title = models.CharField(
        #verbose_name="Context Title",
        help_text="Name of the Willo Lab integration. Example: Willo Labs Test Launch for KU Blackboard Rover Grade Testing",
        max_length=255,
        default=None,
        blank=True,
        null=True
        )

    context_label = models.CharField(
        #verbose_name="Context Label",
        help_text="Example: willolabs-launch-test-ku-blackboard-rover-grade-testing",
        max_length=255,
        blank=True,
        null=True,
        )

    ext_wl_launch_key = models.CharField(
        #verbose_name="External WilloLab Launch Key",
        help_text="Example: QcTz6q",
        max_length=50,
        blank=True,
        null=True,
        )

    ext_wl_launch_url = models.URLField(
        #verbose_name="External WilloLab Launch URL",
        help_text="Example: https://stage.willolabs.com/launch/QcTz6q/8cmzcd",
        blank=True,
        null=True
        )

    ext_wl_version = models.CharField(
        #verbose_name="External WilloLab Version",
        help_text="Example: 1.0",
        max_length=25,
        blank=True,
        null=True,
        )

    ext_wl_outcome_service_url = models.URLField(
        #verbose_name="External  Outcome Service URL",
        help_text="Example: https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/",
        blank=True,
        null=True,
        )

    custom_tpa_next = models.URLField(
        #verbose_name="LTI Params - custom_tpa_next",
        help_text="/account/finish_auth?course_id=course-v1%3AKU%2BOS9471721_108c%2BSpring2020_Fuka_Sample1&enrollment_action=enroll&email_opt_in=false",
        max_length=255,
        blank=True,
        null=True,
        )

    custom_orig_context_id = models.CharField(
        #verbose_name="custom_orig_context_id",
        help_text="Context_id from the original source system (ie Canvas, Blackboard). Example: 9caf71ef12da4d2993f8929242d93922",
        max_length=50,
        blank=True,
        null=True,
        )

    custom_profile_url = models.URLField(
        #verbose_name="custom_profile_url",
        help_text="URL pointing to user profile in the original source system. Example: https://courseware.ku.edu/learn/api/v1/lti/profile?lti_version=LTI-1p0",
        max_length=50,
        blank=True,
        null=True,
        )

    tool_consumer_instance_description = models.CharField(
        #verbose_name="tool_consumer_instance_description",
        help_text="Example: The University of Kansas",
        max_length=50,
        blank=True,
        null=True,
        )

    custom_api_domain = models.CharField(
        #verbose_name="Custom Canvas API Domain",
        help_text="Example: willowlabs.instructure.com",
        max_length=255,
        blank=True,
        null=True,
        )

    custom_course_id = models.CharField(
        #verbose_name="Custom Course ID",
        help_text="Example: 421",
        max_length=50,
        blank=True,
        null=True,
        )

    custom_course_startat = models.DateTimeField(
        #verbose_name="Custom Canvas Course Start At",
        help_text="Example: 2019-12-11 16:18:01 -0500",
        db_index=False,
        blank=True,
        null=True,
        )

    tool_consumer_info_product_family_code = models.CharField(
        #verbose_name="Tool Consumer - Product Family Code",
        help_text="Example: canvas",
        max_length=50,
        blank=True,
        null=True,
        )

    tool_consumer_info_version = models.CharField(
        #verbose_name="Tool Consumer - Version",
        help_text="Example: cloud",
        max_length=50,
        blank=True,
        null=True,
        )

    tool_consumer_instance_contact_email = models.EmailField(
        #verbose_name="Tool Consumer - Contact Email Address",
        help_text="Example: notifications@instructure.com",
        blank=True,
        null=True,
    )

    tool_consumer_instance_guid = models.CharField(
        #verbose_name="Tool Consumer - Instance GUID",
        help_text="Example: 7M58pE4F4Y56gZHUe6jaxhQ1csaktjA00ZiVNQb7:canvas-lms",
        max_length=100,
        blank=True,
        null=True,
        )

    tool_consumer_instance_name = models.CharField(
        #verbose_name="Tool Consumer - Instance Name",
        help_text="Example: Willo Labs",
        max_length=50,
        blank=True,
        null=True,
        )

    def __str__(self):
        return self.course_id.html_id()

    class Meta(object):
        verbose_name = "LTI External Course"
        unique_together = [['context_id', 'course_id']]
        #ordering = ('-fetched_at', )


class LTIExternalCourseAssignments(TimeStampedModel):
    course = models.ForeignKey(LTIExternalCourse, on_delete=models.CASCADE)
    url = models.URLField(
        #verbose_name="Homework Section URL",
        help_text="Open edX Course Assignment",
        max_length=255
    )
    display_name = models.CharField(
        #verbose_name="Display Name",
        help_text="Title text of the Rover assignment. Example: Chapter 5 Section 1 Quadratic Functions Sample Homework",
        max_length=255,
        )
    due_date = models.DateTimeField(
        #verbose_name="Due Date",
        help_text="The Rover assignment due date.",
        null=True,
        blank=True,
        )

    class Meta(object):
        verbose_name = "LTI External Course Assignments"
        verbose_name_plural = verbose_name
        unique_together = [['course', 'url']]
        #ordering = ('-fetched_at', )

    def __str__(self):
        return 'id: ' + str(self.id) + ' - ' + self.display_name


class LTIExternalCourseAssignmentProblems(TimeStampedModel):
    """
    Phase I model
    """
    course_assignment = models.ForeignKey(LTIExternalCourseAssignments, on_delete=models.CASCADE)
    usage_key = UsageKeyField(
        #verbose_name="Usage Key",
        help_text="Open edX Block usage key pointing to the homework problem that was graded, invoking the post_grades() api. Example: block-v1:ABC+OS9471721_9626+01+type@swxblock+block@c081d7653af211e98379b7d76f928163",
        blank=False,
        max_length=255,
        )
    class Meta(object):
        verbose_name = "LTI External Course Assignment Problems"
        verbose_name_plural = verbose_name
        unique_together = [['usage_key']]
        #ordering = ('-fetched_at', )

    def __str__(self):
        return 'block-v1:'+self.usage_key._to_string()


class LTIExternalCourseEnrollment(TimeStampedModel):
    """
    Phase I model
    Course Enrollment data originating from Willo Labs LTI authentications by students entering Rover
    from a third party LMS like Canvas, Moodle, Blackboard, etc.

    """
    course = models.ForeignKey(LTIExternalCourse, on_delete=models.CASCADE)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    lti_user_id = models.CharField(
        #verbose_name="User ID",
        help_text="User ID provided by . Example: ab3e190fae668d925d007d79219fbfce90afba6d",
        max_length=255,
        )

    custom_user_id = models.CharField(
        #verbose_name="Canvas User ID",
        help_text="User ID provided to Willo Labs. Example: 394",
        max_length=25,
        default=None,
        blank=True,
        null=True,
        )

    custom_user_login_id = models.CharField(
        #verbose_name="Canvas Username",
        help_text="Login ID provided to Willo Labs. Example: rover_student",
        max_length=50,
        default=None,
        blank=True,
        null=True,
        )

    custom_person_timezone = models.CharField(
        #verbose_name="Canvas user time zone",
        help_text="Source system time zone from user's profile, provided to Willo Labs. Example: America/New_York",
        max_length=50,
        default=None,
        blank=True,
        null=True,
        )

    ext_roles = models.CharField(
        #verbose_name="External System Roles",
        help_text="User permitted roles in external system. Example: urn:lti:instrole:ims/lis/Student,urn:lti:role:ims/lis/Learner,urn:lti:sysrole:ims/lis/User",
        max_length=255,
        default=None,
        blank=True,
        null=True,
        )

    ext_wl_privacy_mode = models.CharField(
        #verbose_name="External WilloLab Privacy Mode",
        help_text="Privacy settings from external system, provided to Willo Lab. Example: allow-pii-all",
        max_length=50,
        default=None,
        blank=True,
        null=True,
        )

    lis_person_contact_email_primary = models.EmailField(
        #verbose_name="User - Primary Email Address",
        help_text="Example: rover_student@willolabs.com",
        null=True,
        )

    lis_person_name_family = models.CharField(
        #verbose_name="User Family Name",
        help_text="Example: Thornton",
        max_length=50,
        default=None,
        blank=True,
        null=True,
        )

    lis_person_name_full = models.CharField(
        #verbose_name="User Family Name",
        help_text="Example: Billy Bob Thornton",
        max_length=255,
        default=None,
        blank=True,
        null=True,
        )

    lis_person_name_given = models.CharField(
        #verbose_name="User Given Name",
        help_text="Example: Billy Bob",
        max_length=255,
        default=None,
        blank=True,
        null=True,
        )

    lis_person_sourcedid = models.CharField(
        #verbose_name="Source system Username",
        help_text="Example: _tonn_test5",
        max_length=255,
        default=None,
        blank=True,
        null=True,
        )

    class Meta(object):
        verbose_name = "LTI External Course Enrollment"
        unique_together = [['course', 'user']]
        #ordering = ('-fetched_at', )

    def __str__(self):
        return self.course.course_id.html_id() + ' - ' + self.user.username

class LTIExternalCourseEnrollmentGrades(TimeStampedModel):
    """
    Phase I model
    Grade output from Course Enrollments originating from Willo Labs LTI authentications by students entering Rover
    from a third party LMS like Canvas, Moodle, Blackboard, etc.

    This schema is modeled around grades.models.PersistentSubsectionGrade
    not inheriting bc the base class contains lots of superfluous properties and internal methods.
    """
    # primary key will need to be large for this table
    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name

    # First, insert the record. If we get a 200 response then update the record with the posting date.
    synched = models.DateTimeField(
        #verbose_name="Willo Posting Date",
        help_text="The timestamp when this grade record was successfully posted to Willo Grade Sync.",
        null=True,
        blank=True,
        )

    course_enrollment = models.ForeignKey(LTIExternalCourseEnrollment, on_delete=models.CASCADE)
    course_assignment = models.ForeignKey(LTIExternalCourseAssignments, on_delete=models.CASCADE)
    #user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    section_url = models.URLField(
        #verbose_name="Homework Section URL",
        help_text="Open edX Course Assignment",
        max_length=255
    )

    usage_key = UsageKeyField(
        #verbose_name="Usage Key",
        help_text="Open edX Block usage key pointing to the homework problem that was graded, invoking the post_grades() api.",
        blank=False,
        max_length=255,
        )

    # earned/possible refers to the number of points achieved and available to achieve.
    # graded refers to the subset of all problems that are marked as being graded.
    earned_all = models.FloatField(blank=False)
    possible_all = models.FloatField(blank=False)
    earned_graded = models.FloatField(blank=False)
    possible_graded = models.FloatField(blank=False)

    class Meta(object):
        verbose_name = "LTI External Course Enrollment Grades"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.course_enrollment.course.course_id.html_id() + ' - ' + self.course_assignment.display_name
