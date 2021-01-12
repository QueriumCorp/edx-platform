"""
  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         aug-2020

  LTI Grade Sync.
  Bulk initialize all course runs by upserting a record in LTIInternalCourse

  Usage:
    sudo -H -u edxapp bash
    cd ~
    source edxapp_env
    source venvs/edxapp/bin/activate
    cd edx-platform
    python manage.py lms bulk_initialize
"""
# python stuff
import six

# django stuff
from django.core.management.base import BaseCommand

# edx stuff
from xmodule.modulestore.django import modulestore
from xmodule.error_module import ErrorDescriptor
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

# our stuff
from common.djangoapps.third_party_auth.lti_consumers.models import LTIInternalCourse
from common.djangoapps.third_party_auth.lti_consumers.utils import get_default_lti_configuration


class Command(BaseCommand):
    help = u"LTI Grade Sync. Add all course runs to LTIInternalCourse"

    def handle(self, *args, **kwargs):

        def course_filter(course_summary):
            """
            Filter out unusable and inaccessible courses
            """
            # TODO remove this condition when templates purged from db
            if course_summary.location.course == 'templates':
                return False
            return True

        courses_summary = modulestore().get_course_summaries()
        courses_summary = six.moves.filter(course_filter, courses_summary)

        for course in courses_summary:
            if isinstance(course, ErrorDescriptor):
                continue

            course_overview = CourseOverview.get_from_id(course.id)
            lti_internal_course = LTIInternalCourse.objects.filter(course=course_overview).first()
            if lti_internal_course:
                print('verified course run {course_run}'.format(
                    course_run=str(course.id)
                ))
            else:
                print('adding course run {course_run}'.format(
                    course_run=str(course.id)
                ))
                lti_configuration = get_default_lti_configuration()

                lti_internal_course = LTIInternalCourse(
                    course_id=str(course.id),   # course.id: opaque_keys.edx.locator.CourseLocator
                    course=course_overview,
                    enabled=False,
                    lti_configuration=lti_configuration,
                    matching_function='TPA_NEXT'
                )
                lti_internal_course.save()
