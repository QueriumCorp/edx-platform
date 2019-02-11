from __future__ import absolute_import
#from django.urls import path
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.views import get_swagger_view

from .views import AllContactViewSet, PendingContactViewSet, NewContactViewSet, CampaignViewSet, CourseCreatorViewSet

API_TITLE = u'OpenStax Salesforce api V1.00'
API_DESCRIPTION = u'A Web API for integrating AM instructor data to salesforce.com'
docs = include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)

router = DefaultRouter(trailing_slash=False)

# add routes with default CRUD behavior here

router.register(ur'contacts/all', AllContactViewSet)
router.register(ur'contacts/new', NewContactViewSet)
router.register(ur'contacts/pending', PendingContactViewSet)
router.register(ur'campaigns', CampaignViewSet)
router.register(ur'coursecreators', CourseCreatorViewSet)

# add customized routes here
urlpatterns = [
    #path(u'docs/', docs),        # core api documentation
    #path(u'docs/schema/', get_schema_view(title=API_TITLE)), # raw api schema data
    #path(u'docs/swagger/', get_swagger_view(title=API_TITLE)), # formatted swagger documentation

    url(u'docs/', docs),        # core api documentation
    url(u'docs/schema/', get_schema_view(title=API_TITLE)), # raw api schema data
    url(u'docs/swagger/', get_swagger_view(title=API_TITLE)), # formatted swagger documentation
] + router.urls
