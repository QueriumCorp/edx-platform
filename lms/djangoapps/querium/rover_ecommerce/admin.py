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

from .models import (
    Configuration,
    EOPWhitelist,
    )

class ConfigurationAdmin(admin.ModelAdmin):
    """
    Rover Ecommerce Configuration
    """
    list_display = (
        'course_id',
        'created',
        'modified',
        'payment_deadline_date',
    )
    readonly_fields=('created', 'modified' )

admin.site.register(Configuration, ConfigurationAdmin)

class EOPWhitelistAdmin(admin.ModelAdmin):
    """
    Rover Ecommerce Configuration for EOP Student Exemptions
    """
    list_display = (
        'id',
        'user_email',
        'type',
        'created',
        'modified',
    )

admin.site.register(EOPWhitelist, EOPWhitelistAdmin)
