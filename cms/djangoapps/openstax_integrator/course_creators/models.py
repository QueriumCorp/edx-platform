from __future__ import absolute_import
from django.db import models

u"""
Copied from https://raw.githubusercontent.com/edx/edx-platform/master/cms/djangoapps/course_creators/models.py
Table for storing information about whether or not Studio users have course creation privileges.
"""
from django.db import models
from django.utils.translation import ugettext as _

from ..users.models import User


class CourseCreator(models.Model):
    u"""
    Creates the database table model.
    """
    UNREQUESTED = u'unrequested'
    PENDING = u'pending'
    GRANTED = u'granted'
    DENIED = u'denied'

    # Second value is the "human-readable" version.
    STATES = (
        (UNREQUESTED, _(u'unrequested')),
        (PENDING, _(u'pending')),
        (GRANTED, _(u'granted')),
        (DENIED, _(u'denied')),
    )

    user = models.OneToOneField(User, help_text=_(u"AM user"), on_delete=models.CASCADE)
    state_changed = models.DateTimeField(u'state last updated', auto_now_add=True,
                                         help_text=_(u"The date when state was last updated"))
    state = models.CharField(max_length=24, blank=False, choices=STATES, default=UNREQUESTED,
                             help_text=_(u"Current course creator state"))
    note = models.CharField(max_length=512, blank=True, help_text=_(u"Optional notes about this user (for example, "
                                                                    u"why course creation access was denied)"))

    def __str__(self):
        return u"{0} | {1}".format(self.user, self.state)
