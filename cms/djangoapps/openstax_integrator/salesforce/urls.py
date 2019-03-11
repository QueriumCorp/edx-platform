from __future__ import absolute_import
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls
from rest_framework_swagger.views import get_swagger_view

from .views import ContactViewSet, CampaignViewSet, CourseCreatorViewSet

# Note: include_docs_urls stopped working after the python backport
API_TITLE = u'OpenStax Salesforce api V1.00'
API_DESCRIPTION = u'A Web API for integrating AM instructor data to salesforce.com'
docs = include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)

router = DefaultRouter(trailing_slash=False)

# add routes with default CRUD behavior here
router.register(ur'contacts', ContactViewSet)
router.register(ur'campaigns', CampaignViewSet)
router.register(ur'coursecreators', CourseCreatorViewSet)

# add customized routes here
urlpatterns = [
    url(u'docs/', get_swagger_view(title=API_TITLE)), # formatted swagger documentation
] + router.urls
