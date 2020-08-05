# python
from __future__ import absolute_import

# django
from django.db import models
from django.utils.translation import ugettext as _

# open edx
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField

class Configuration(TimeStampedModel):
    """
    Course-level ecommerce configurations.
    """
    course_id = CourseKeyField(
        max_length=255,
        help_text="Rover Course Key (Opaque Key). " \
            "Based on Institution, Course, Section identifiers. Example: course-v1:edX+DemoX+Demo_Course",
        blank=False,
        default=None,
        primary_key=True
        )

    payment_deadline_date = models.DateTimeField(
        help_text="The date after which the paywall will rise for enrolled students who have not yet paid.",
        null=True,
        blank=True,
        )

    class Meta(object):
        verbose_name = "Rover E-Commerce Configuration"
        verbose_name_plural = verbose_name + "s"

    def __str__(self):
        return self.course_id.html_id()


class EOPWhitelist(TimeStampedModel):
    """
    Course-level EOP student lists for payment exemptions.
    """
    EOP = 'eop_student'
    TESTER = 'tester'
    RETAKE = 'free_retake'

    whitelist_type = (
        (EOP, _('EOP Student')),
        (TESTER, _('Rover Tester')),
        (RETAKE, _('Free Retake')),
    )

    user_email = models.EmailField(
        unique=True
    )

    type = models.CharField(max_length=24, blank=False,
                            choices=whitelist_type,
                            default=EOP,
                            help_text=_(u"Type of E-Commerce whitelist user."))

    class Meta(object):
        verbose_name = "Rover E-Commerce Payment Exemption"
        verbose_name_plural = verbose_name + "s"
