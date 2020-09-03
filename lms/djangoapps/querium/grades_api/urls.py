"""
Grades API URLs.
"""

from django.conf import settings
from django.conf.urls import include, url


# mcdaniel feb-2020: only include grades api if feature flag is set.
if settings.ROVER_ENABLE_GRADES_API:
    urlpatterns = [
        url(r'^v1/', include('querium.grades_api.v1.urls', namespace='v2'))
    ]
