from __future__ import absolute_import
from django.contrib import admin
from .models import Configuration


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'type',
        'stepwise_host',
        'created',
        'updated',
    )
    readonly_fields=(u'created', u'updated', )

admin.site.register(Configuration, ConfigurationAdmin)
