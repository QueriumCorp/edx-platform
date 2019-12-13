import logging
from django.contrib.auth.models import User

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------------------
# mcdaniel dec-2019
# LTI Integration for Willo Labs Grade Sync
# --------------------------------------------------------------------------------------------------

class LTIWilloLabsGradeSynCourse(TimeStampedModel):
    """
    Course data originating from Willo Labs LTI authentications by students entering Rover
    from a third party LMS like Canvas, Moodle, Blackboard, etc.
    """
    context_id = models.CharField(
        verbose_name="Context ID",
        help_text="This is the unique identifier of the Willo Labs integration, passed via" \
            "from tpa-lti-params. Course runs from external LMS' are intended to be unique." \
            "Example: e14751571da04dd3a2c71a311dda2e1b",
        max_length=255, 
        primary_key=True
        )  # This is the key for lookups in this table

    course_id = CourseKeyField(max_length=255, db_index=True)

    context_title = models.CharField(
        verbose_name="Context Title",
        help_text="Name of the Willo Lab integration. Example: Rover by Openstax Gradesync Testing",
        max_length=50,
        default=None, 
        blank=True, 
        null=True
        )
    context_label = models.CharField(
        verbose_name="Context Label",
        help_text="Example: Rover",
        max_length=50
        )
	ext_wl_launch_key = models.CharField(
        verbose_name="External WilloLab Launch Key",
        help_text="Example: QcTz6q",
        max_length=50
        )
	ext_wl_launch_url = models.URLField(
        verbose_name="External WilloLab Launch URL",
        help_text="Example: https://stage.willolabs.com/launch/QcTz6q/8cmzcd",
        )
	ext_wl_version = models.CharField(
        verbose_name="External WilloLab Version",
        help_text="Example: 1.0",
        max_length=25
        )
	ext_wl_outcome_service_url = models.URLField(
        verbose_name="External WilloLabs Outcome Service URL"
        help_text="Example: https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/",
        )
	custom_canvas_api_domain = models.CharField(
        verbose_name="Custom Canvas API Domain",
        help_text="Example: willowlabs.instructure.com",
        max_length=255
        )
	custom_canvas_course_id = models.CharField(
        verbose_name="Custom Canvas Course ID",
        help_text="Example: 421",
        max_length=50
        )
	custom_canvas_course_startat = models.DateTimeField(
        verbose_name="Custom Canvas Course Start At",
        help_text="Example: 2019-12-11 16:18:01 -0500",
        db_index=False,
        null=False
        )
	tool_consumer_info_product_family_code = models.CharField(
        verbose_name="Tool Consumer - Product Family Code",
        help_text="Example: canvas",
        max_length=50
        )
    tool_consumer_info_version = models.CharField(
        verbose_name="Tool Consumer - Version",
        help_text="Example: cloud",
        max_length=50
        )
    tool_consumer_instance_contact_email = models.EmailField(
        verbose_name="Tool Consumer - Contact Email Address",
        help_text="Example: notifications@instructure.com"
    )
    tool_consumer_instance_guid = models.CharField(
        verbose_name="Tool Consumer - Instance GUID",
        help_text="Example: 7M58pE4F4Y56gZHUe6jaxhQ1csaktjA00ZiVNQb7:canvas-lms",
        max_length=100
        )
    tool_consumer_instance_name = models.CharField(
        verbose_name="Tool Consumer - Instance Name",
        help_text="Example: Willo Labs",
        max_length=50
        )

    #public_key = models.TextField()


    class Meta(object):
        app_label = "lti_willolabs_grade_sync_course"
        verbose_name = "LTI Willo Labs Grade Sync - Course"
        verbose_name_plural = verbose_name
        unique_together = [['context_id', 'course_id']]
        #ordering = ('-fetched_at', )



class LTIWilloLabsGradeSynCourseEnrollment(TimeStampedModel):
    """
    Course Enrollment data originating from Willo Labs LTI authentications by students entering Rover
    from a third party LMS like Canvas, Moodle, Blackboard, etc.

    """
    context_id = models.ForeignKey('LTIWilloLabsGradeSynCourse', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    user_id = models.CharField(
        verbose_name="User ID",
        help_text="User ID provided by WilloLabs. Example: ab3e190fae668d925d007d79219fbfce90afba6d",
        max_length=255
        )

	custom_canvas_user_id = models.CharField(
        verbose_name="Canvas User ID",
        help_text="Canvas User ID provided to WilloLabs. Example: 394",
        max_length=25,
        default=None, 
        blank=True, 
        null=True
        )

	custom_canvas_user_login_id = models.CharField(
        verbose_name="Canvas Username",
        help_text="Canvas Username provided to WilloLabs. Example: rover_student",
        max_length=50,
        default=None, 
        blank=True, 
        null=True
        )

	custom_canvas_person_timezone = models.CharField(
        verbose_name="Canvas user time zone",
        help_text="Canvas time zone from user's profile, provided to Willo Labs. Example: America/New_York"
        max_length=50,
        default=None, 
        blank=True, 
        null=True
        )

	ext_roles = models.CharField(
        verbose_name="External System Roles",
        help_text="User permitted roles in external system. Example: urn:lti:instrole:ims/lis/Student,urn:lti:role:ims/lis/Learner,urn:lti:sysrole:ims/lis/User"
        max_length=255,
        default=None, 
        blank=True, 
        null=True
        )

	ext_wl_privacy_mode = models.CharField(
        verbose_name="External WilloLab Privacy Mode",
        help_text="Privacy settings from external system, provided to Willo Lab. Example: allow-pii-all"
        max_length=50,
        default=None, 
        blank=True, 
        null=True
        )

	lis_person_contact_email_primary = models.EmailField(
        verbose_name="User - Primary Email Address",
        help_text="Example: rover_student@willolabs.com"
    )

	lis_person_name_family = models.CharField(
        verbose_name="User Family Name",
        help_text="Example: Thornton"
        max_length=50,
        default=None, 
        blank=True, 
        null=True
        )

	lis_person_name_full = models.CharField(
        verbose_name="User Family Name",
        help_text="Example: Billy Bob Thornton"
        max_length=255,
        default=None, 
        blank=True, 
        null=True
        )

	lis_person_name_given = models.CharField(
        verbose_name="User Given Name",
        help_text="Example: Billy Bob"
        max_length=255,
        default=None, 
        blank=True, 
        null=True
        )

    class Meta(object):
        app_label = "lti_willolabs_grade_sync_course_enrollment"
        verbose_name = "LTI Willo Labs Grade Sync - Course Enrollment"
        verbose_name_plural = verbose_name
        unique_together = [['context_id', 'user']]
        #ordering = ('-fetched_at', )


class LTIWilloLabsGradeSynCourseEnrollmentGrades(TimeStampedModel):
    """
    Grade output from Course Enrollments originating from Willo Labs LTI authentications by students entering Rover
    from a third party LMS like Canvas, Moodle, Blackboard, etc.

    This schema is modeled around grades.models.PersistentSubsectionGrade
    not inheriting bc the base class contains lots of superfluous properties and internal methods.
    """
    # primary key will need to be large for this table
    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name

    # First, insert the record. If we get a 200 response then update the record with the posting date.
    synched = models.DateTimeField(
        verbose_name="Willo Posting Date",
        help_text="The timestamp when this grade record was successfully posted to Willo Grade Sync."
        null=True, 
        blank=True
        )

    context_id = models.ForeignKey('LTIWilloLabsGradeSynCourse', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    #user_id = models.IntegerField(blank=False)
    # mcdaniel: this is redundant. it's stored in the table def above at the corse level.
    # adding it only to maintain continuity with the original model grades.models.PersistentSubsectionGrade(TimeStampedModel)
    course_id = CourseKeyField(
        verbose_name="Course ID",
        help_text="Open edX Opaque Key course_id"
        blank=False, 
        max_length=255
        )

    # note: the usage_key may not have the run filled in for
    # old mongo courses.  Use the full_usage_key property
    # instead when you want to use/compare the usage_key.
    usage_key = UsageKeyField(
        verbose_name="Usage Key",
        help_text="Open edX Course subsection key. Points to this homework assignment"
        blank=False, 
        max_length=255
        )

    # Information relating to the state of content when grade was calculated
     course_version = models.CharField(
         help_text="Guid of latest course version", 
         blank=True, 
         max_length=255
         )

    # earned/possible refers to the number of points achieved and available to achieve.
    # graded refers to the subset of all problems that are marked as being graded.
    earned_all = models.FloatField(blank=False)
    possible_all = models.FloatField(blank=False)
    earned_graded = models.FloatField(blank=False)
    possible_graded = models.FloatField(blank=False)

    # timestamp for the learner's first attempt at content in
    # this subsection. If null, indicates no attempt
    # has yet been made.
    first_attempted = models.DateTimeField(
        help_text="timestamp for the learner's first attempt at content in this subsection. Should contain a value",
        )

    # track which blocks were visible at the time of grade calculation
    visible_blocks = models.ForeignKey(        
        VisibleBlocks, 
        help_text="track which blocks were visible at the time of grade calculation.",
        db_column='visible_blocks_hash', 
        to_field='hashed',
        on_delete=models.CASCADE
        )



    class Meta(object):
        app_label = "lti_willolabs_grade_sync_course_enrollment_grades"
        verbose_name = "LTI Willo Labs Grade Sync - Course Enrollment Grades"
        verbose_name_plural = verbose_name
        unique_together = [
            # * Specific grades can be pulled using all three columns,
            # * Progress page can pull all grades for a given (course_id, user_id)
            # * Course staff can see all grades for a course using (course_id,)
            ('context_id', 'user', 'usage_key'),
        ]
        # Allows querying in the following ways:
        # (modified): find all the grades updated within a certain timespan
        # (modified, course_id): find all the grades updated within a timespan for a certain course
        # (modified, course_id, usage_key): find all the grades updated within a timespan for a subsection
        #   in a course
        # (first_attempted, course_id, user_id): find all attempted subsections in a course for a user
        # (first_attempted, course_id): find all attempted subsections in a course for all users
        index_together = [
            ('modified', 'course_id', 'usage_key'),
            ('first_attempted', 'course_id', 'user_id')
        ]



"""
    TO DELETE ----------------------------------------------------------------------------------------
"""
class LTIContextCourse(models.Model):
    """
    Relationship of LTI tpa_lti_params.context_id to Rover course_id.
    """
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    course = models.ForeignKey(
        CourseOverview,
        on_delete=models.CASCADE,
        primary_key=True,
        )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        )

    context_id = models.CharField(
        max_length=32,
        unique=True,
        help_text=(
            'Uniquely identify a course from an LTI consumer LMS. Provided an' \
            ' a tpa_lti_params parameter during LTI authentication.'
        )
    )

    ext_wl_outcome_service_url = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            'Requests to the Grade Sync API must be made to a course-specific' \
            'service URL, which is supplied to tool providers on launches. The' \
            'service URL will be provided in the parameter.'
        )
    )

    @property
    def course_id(self):
        """ Return course id. """
        course_id = CourseKey.from_string(unicode(self.course.id))

        try:
            return str(CourseOverview.get_from_id(course_id).id)
        except CourseOverview.DoesNotExist:
            log.warning('Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    @property
    def name(self):
        """ Return course name. """
        course_id = CourseKey.from_string(unicode(self.course.id))

        try:
            return CourseOverview.get_from_id(course_id).display_name
        except CourseOverview.DoesNotExist:
            log.warning('Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    class Meta(object):
        app_label = "lti_willolabs"
        verbose_name = "LTI Context Course Map"
        verbose_name_plural = verbose_name
        ordering = ('-fetched_at', )

"""
    This is used to track LTI Grade Synch posts back to the LTI consumer LMS systems.
"""
class LTIContextCourseSection(models.Model):
    """
    Tracking data for individual course assignments to LTIContextCourse.
    """
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    lti_context_course = models.ForeignKey(
        LTIContextCourse,
        on_delete=models.CASCADE,
        primary_key=True
        )

    id = models.CharField(
        max_length=32,
        unique=True,
        help_text=(
            'Unique slug identifier of a course section from a Rover course.' \
            'Maps to section.url_name.'
            )
        )

    location = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            'Alternate unique identifier of a course section from a Rover course.' \
            'Maps to section.location.'
            )
        )

    title = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            'Title of Rover course section. Use course name????' \
            'Maps to course.name'
            )
        )

    description = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            'Text description of Rover course section.'
            )
        )

    points_possible = models.IntegerField(
        help_text=(
            'Gross points that can be earned from this assignment.' \
            'Maps to section_grade.section_grade_possible'
            )
        )

    class Meta(object):
        app_label = "lti_willolabs"
        verbose_name = "LTI Context Course Sub-sections tracking data"
        verbose_name_plural = verbose_name
        ordering = ('-fetched_at', )
