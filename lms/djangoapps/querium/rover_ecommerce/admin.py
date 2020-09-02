# -*- coding: utf-8 -*-
"""
  Rover Ecommerce Configuration

  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Aug-2020
"""
from __future__ import absolute_import
from django.contrib import admin

from lms.djangoapps.querium.rover_ecommerce.models import (
    Configuration,
    EOPWhitelist,
    )

class ConfigurationAdmin(admin.ModelAdmin):
    """
    Rover Ecommerce Configuration
    """
    search_fields = ('course_id', )
    list_display = (
        'course_id',
        'payment_deadline_date',
        'created',
        'modified',
    )
    readonly_fields=('created', 'modified' )

admin.site.register(Configuration, ConfigurationAdmin)

class EOPWhitelistAdmin(admin.ModelAdmin):
    """
    Rover Ecommerce Configuration for EOP Student Exemptions
    """
    search_fields = ('user_email', 'type', )
    list_display = (
        'id',
        'user_email',
        'type',
        'created',
        'modified',
    )

admin.site.register(EOPWhitelist, EOPWhitelistAdmin)
