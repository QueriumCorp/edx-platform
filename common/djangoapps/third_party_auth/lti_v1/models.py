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
        Course,
        on_delete=models.CASCADE,
        primary_key=True
        )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
        )
        
    context_id = models.CharField(
        max_length=32,
        unique=True,
        help_text=(
            'Uniquely identify a course from an LTI consumer LMS. Provided an' \
            ' a tpa_lti_params parameter during LTI authentication.'
        )
    )

    @property
    def name(self):
        """ Return course name. """
        course_id = CourseKey.from_string(unicode(self.id))

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
