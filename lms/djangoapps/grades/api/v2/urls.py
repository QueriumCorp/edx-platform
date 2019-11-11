""" Grades API v2 URLs. """
from django.conf import settings
from django.conf.urls import url

from lms.djangoapps.grades.api.v2.views import CourseGradeView
from lms.djangoapps.grades.api.v2.views import ChapterGradeView
from lms.djangoapps.grades.api.v2.views import SectionGradeView

from lms.djangoapps.grades.api.views import CourseGradingPolicy


from rest_framework.documentation import include_docs_urls
from rest_framework_swagger.views import get_swagger_view

COURSE_ID_PATTERN = r'(?P<course_id>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)'
SECTION_ID_PATTERN = r'(?P<section_id>\b[a-z0-9]{32}\b)'
CHAPTER_ID_PATTERN = r'(?P<chapter_id>\b[a-z0-9]{32}\b)'

# Note: include_docs_urls stopped working after the python backport
API_TITLE = u'Rover Grades API V2.00'
API_DESCRIPTION = u'A Web API for synchronizing grade data to external platforms. Mostly used with LTI and Willo Labs but could be used with any RESTful consumer.'
docs = include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)


urlpatterns = [

    url(u'docs/', get_swagger_view(title=API_TITLE)), # formatted swagger documentation
    url(
        r'^policy/courses/{course_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
        ),
        CourseGradingPolicy.as_view(),
        name='course_grading_policy'
    ),

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
