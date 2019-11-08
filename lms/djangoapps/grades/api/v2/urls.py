""" Grades API v1 URLs. """
from django.conf import settings
from django.conf.urls import url

from lms.djangoapps.grades.api.v2.views import CourseGradeView
from lms.djangoapps.grades.api.v2.views import SubsectionGradesView
from lms.djangoapps.grades.api.v2.views import ChapterGradesView
from lms.djangoapps.grades.api.v2.views import ProblemGradeView

from lms.djangoapps.grades.api.views import CourseGradingPolicy

urlpatterns = [

    #------------------------------------------------------------------------
    #   DEPRECATED!!!
    #------------------------------------------------------------------------
    #url(
    #    r'^courses/$',
    #    views.CourseGradesView.as_view(), name='course_grades'
    #),

    url(
        r'^courses/{course_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
        ),
        CourseGradeView.as_view(),
        name='course_grades'
    ),
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
        r'^courses/{course_id}/{subsection_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
            subsection_id='subsections',
        ),
        SubsectionGradesView.as_view(),
        name='course_grades_subsection'
    ),
    url(
        r'^courses/{course_id}/{chapter_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
            chapter_id='chapters',
        ),
        ChapterGradesView.as_view(),
        name='course_grades_chapters'
    ),
    url(
        r'^courses/{course_id}/{problem_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
            problem_id='problems',
        ),
        ProblemGradeView.as_view(),
        name='course_grades_problems'
    ),
    # ----------------------------------------------------------------------


]
