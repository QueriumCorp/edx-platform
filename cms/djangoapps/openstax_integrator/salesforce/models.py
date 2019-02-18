from __future__ import absolute_import
import os
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils.translation import ugettext as _
from course_creators.models import CourseCreator


# Create your models here.
class Campaign(models.Model):

    class Meta(object):
        ordering = [u'active']

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    active = models.BooleanField(default=True,
                                 null=False,
                                 help_text=_(u"True if this is the current campaign to which new salesforce contacts should be added."))

    name = models.CharField(max_length=50)
    salesforce_id = models.CharField(max_length=50,
                                     default=None,
                                     blank=True,
                                     null=True,
                                     help_text=_(u"Example: 7010m0000002pARAAY from the following URL: https://cs65.lightning.force.com/lightning/r/Campaign/7010m0000002pARAAY/view"))

    def __str__(self):
        return self.name

class Contact(models.Model):
    u"""
    Creates the salesforce integration custom tracking fields table.
    """

    class Meta(object):
        ordering = [u'-created']

    # Django user fields
    user = models.ForeignKey(CourseCreator, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


    #email
    # email (will come from user)
    # initial_sign_in_date (will come from user)
    # most_recent_sign_id_date (will come from user)
    real_course_created_at = models.DateTimeField(blank=True, null=True)

    # From custom Django Campaigns object
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)

    # salesforce-generated contact_id
    contact_id = models.CharField(max_length=50, blank=True, null=True)
    salesforce_push_pending = models.BooleanField(blank=True, default=True)


    # Training Wheels fields
    completed_training_wheels_date = models.DateTimeField(blank=True, null=True)
    started_assignment_date = models.DateTimeField(blank=True, null=True)
    completed_assignment_date = models.DateTimeField(blank=True, null=True)

    # TBD 3rd party system
    soft_ask_decision = models.CharField(max_length=255, blank=True, null=True)
    soft_ask_decision_date = models.DateTimeField(blank=True, null=True)
    estimated_enrollment = models.IntegerField(blank=True, null=True)
    latest_adoption_decision = models.CharField(max_length=255, blank=True, null=True)

    def clean_salesforce_push_pending(self):
        # Set flag to True so that this record will be included in 'pending' to salesforce
        return True

    def __str__(self):
        return self.user.user.email

class Configuration(models.Model):
    u"""
    Creates the salesforce integration configuration table.
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
                            choices=configuration_type, default=DEVELOP,
                            unique=True,
                            help_text=_(u"Type of Open edX environment in which this configuration will be used."))

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # From custom Django Campaigns object
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)

    email_notification = models.EmailField(
                            help_text=_(u"Email address for notifications: errors, completed operations."))

    url = models.URLField(max_length=255, blank=False, help_text=_(u"salesforce api account login URL."))

    username = models.CharField(max_length=255, blank=False,
                            help_text=_(u"salesforce api account username."))

    password = models.CharField(max_length=255, blank=False,
                            help_text=_(u"salesforce api account password."))

    security_token = models.CharField(max_length=255, blank=False,
                            help_text=_(u"salesforce api security token."))

    sandbox = models.BooleanField(blank=False, default=True,
                            help_text=_(u"True if you want this configuration to connect to the salesforce api Sandbox instead of the production data store."))


    def __str__(self):
        return self.type
