"""
Grades API URLs.
"""

from django.conf import settings
from django.conf.urls import include, url

"""
from lms.djangoapps.grades.api import views

urlpatterns = [
    url(
        r'^v0/course_grade/{course_id}/users/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
        ),
        views.UserGradeView.as_view(), name='user_grade_detail'
    ),
    url(
        r'^v0/courses/{course_id}/policy/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
        ),
        views.CourseGradingPolicy.as_view(), name='course_grading_policy'
    ),
    url(r'^v1/', include('grades.api.v1.urls', namespace='v1')),
]
"""

# mcdaniel feb-2020: only include grades api if feature flag is set.
if settings.ROVER_ENABLE_GRADES_API:
    urlpatterns = [
        url(r'^v2/', include('querium.grades_api.v2.urls', namespace='v2'))
    ]
