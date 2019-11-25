import logging
from django.contrib.auth.models import User

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = logging.getLogger(__name__)


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
        app_label = "lti_v1"
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
        app_label = "lti_v1"
        verbose_name = "LTI Context Course Sub-sections tracking data"
        verbose_name_plural = verbose_name
        ordering = ('-fetched_at', )
