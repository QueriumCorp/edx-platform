from __future__ import absolute_import
import os
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils.translation import ugettext as _


# Create your models here.
class Configuration(models.Model):
    u"""
    Creates the Rover Stepwise configuration table.
    """
    DEVELOP = u'dev'
    TEST = u'test'
    PRODUCTION = u'prod'

    configuration_type = (
        (DEVELOP, _(u'Development')),
        (TEST, _(u'Testing / QA')),
        (PRODUCTION, _(u'Production')),
    )

    type = models.CharField(max_length=24, blank=False,
                            primary_key=True,
                            choices=configuration_type, default=DEVELOP,
                            unique=True,
                            help_text=_(u"Type of Open edX environment in which this configuration will be used."))

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    stepwise_host = models.URLField(max_length=255, blank=True, help_text=_(u"the URL pointing to the Querium Stepwise Server."))


    def __str__(self):
        return self.type
