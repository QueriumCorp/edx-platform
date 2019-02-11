from __future__ import absolute_import
from django.contrib import admin

from .models import Campaign, Contact, Configuration



class ContactAdmin(admin.ModelAdmin):
    list_display = (
        u'user',
        u'real_course_created_at',
        u'campaign',
        u'contact_id',
        u'salesforce_push_pending',
        u'completed_training_wheels_date',
        u'started_assignment_date',
        u'completed_assignment_date',
        u'soft_ask_decision',
        u'soft_ask_decision_date',
        u'estimated_enrollment',
        u'latest_adoption_decision'
    )
    readonly_fields=(u'created', u'updated', )

class ConfigurationAdmin(admin.ModelAdmin):
    readonly_fields=(u'created', u'updated', )


admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(Campaign)
admin.site.register(Contact, ContactAdmin)
