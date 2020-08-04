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
    RoverEcommerceConfiguration,
    RoverEcommerceEOPStudent,
    )

class RoverEcommerceEOPStudentAdmin(admin.ModelAdmin):
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

admin.site.register(RoverEcommerceConfiguration, RoverEcommerceEOPStudentAdmin)

class RoverEcommerceEOPStudentAdmin(admin.ModelAdmin):
    """
    Rover Ecommerce Configuration for EOP Student Exemptions
    """
    list_display = (
        'id',
        'course_id',
        'user_email'
    )
    readonly_fields=('id')

admin.site.register(RoverEcommerceEOPStudent, RoverEcommerceEOPStudentAdmin)
