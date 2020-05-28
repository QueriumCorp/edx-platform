from __future__ import absolute_import
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls
# may-2020: swagger seems to have been removed in juniper.rc3
#from rest_framework_swagger.views import get_swagger_view

from .views import ConfigurationViewSet

# Note: include_docs_urls stopped working after the python backport
API_TITLE = 'OpenStax Rover Stepwise api V1.00'
API_DESCRIPTION = 'A Web API for providing configuration data for Rover Stepwise'
docs = include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)

router = DefaultRouter(trailing_slash=False)

# add routes with default CRUD behavior here
router.register('configuration', ConfigurationViewSet)

# add customized routes here
urlpatterns = [
    # may-2020: swagger seems to have been removed in juniper.rc3
    #url(u'docs/', get_swagger_view(title=API_TITLE)), # formatted swagger documentation
] + router.urls
