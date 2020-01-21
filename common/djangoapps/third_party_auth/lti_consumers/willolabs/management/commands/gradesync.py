from __future__ import with_statement
from __future__ import absolute_import
from django.core.management.base import BaseCommand

u"""
  Willo Labs Grade Sync.
  Process all assignment grades from all students enrolled in course_id
"""
class Command(BaseCommand):
    help = u"Willo Labs Grade Sync. Post all assignment grades from all students enrolled in course_id."

    def add_arguments(self, parser):
        parser.add_argument('course_id', 
            type=str,
            action=u'store_true',
            required=True,
            dest=u'course_id'
            help=u'Course_id (a string representation of a CourseKey) of Rover course to Gradesync with Willo Labs.'
            )

    def handle(self, *args, **kwargs):
        results = parser.parse_args()
        log.info(u'gradesync.py - {course_id}'.format(
            course_id=results.course_id
        ))
