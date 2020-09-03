""" Grades API v2 URLs. """
from django.conf import settings
from django.conf.urls import url

from .views import CourseGradeView
from .views import ChapterGradeView
from .views import SectionGradeView
from lms.djangoapps.grades.rest_api.v1.views import CourseGradingPolicy


from rest_framework.documentation import include_docs_urls
# mcdaniel may-2020: swagger seems to have been removed in juniper.rc3
#from rest_framework_swagger.views import get_swagger_view

app_name = 'lms.djangoapps.querium.grades_api'

"""
  mcdaniel nov-2019
  i found the reference pattern

  COURSE_ID_PATTERN = r'(?P<course_id>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)'

  in openedx/core/constants.py

  the slugs for chapter and section are both 32-character length alphanumeric
  strings. Example: c0a9afb73af311e98367b7d76f928163

"""
SECTION_ID_PATTERN = r'(?P<section_id>\b[a-z0-9]{32}\b)'
CHAPTER_ID_PATTERN = r'(?P<chapter_id>\b[a-z0-9]{32}\b)'

# Note: include_docs_urls stopped working after the python backport
API_TITLE = u'Rover Grades API V2.00'
API_DESCRIPTION = u'A Web API for synchronizing grade data to external platforms. Mostly used with LTI and Willo Labs but could be used with any RESTful consumer.'
docs = include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)


urlpatterns = [

    url(
        r'^policy/courses/{course_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
        ),
        CourseGradingPolicy.as_view(),
        name='course_grading_policy'
    ),

    # ----------------------------------------------------------------------
    # mcdaniel nov-2019
    # Add fully formatted Swagger documentation
    #
    # may-2020: swagger seems to have been removed in juniper.rc3
    # ----------------------------------------------------------------------
    #url(u'docs/', get_swagger_view(title=API_TITLE)),

    # ----------------------------------------------------------------------
    # mcdaniel nov-2019
    # new more granular grade data end points
    # ----------------------------------------------------------------------
    url(
        r'^courses/{course_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN
        ),
        CourseGradeView.as_view(),
        name='course_grades'
    ),

    url(
        r'^courses/{course_id}/{chapter_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
            chapter_id=CHAPTER_ID_PATTERN,
        ),
        ChapterGradeView.as_view(),
        name='course_grades_chapter'
    ),
    url(
        r'^courses/{course_id}/{chapter_id}/{section_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
            chapter_id=CHAPTER_ID_PATTERN,
            section_id=SECTION_ID_PATTERN,
        ),
        SectionGradeView.as_view(),
        name='course_grades_section'
    ),
    # ----------------------------------------------------------------------


]
