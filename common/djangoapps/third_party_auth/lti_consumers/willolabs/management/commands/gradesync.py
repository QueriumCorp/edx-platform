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
            help=u'A string representation of a CourseKey. Example: course-v1:ABC+OS9471721_9626+01'
            )

    def handle(self, *args, **kwargs):
        course_id = kwargs['course_id']

        self.stdout.write(self.style.NOTICE(u"gradesync.py ..."))
        self.stdout.write(self.style.SUCCESS(u'gradesync.py - {course_id}'.format(
            course_id=course_id
        )))
