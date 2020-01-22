from django.core.management.base import BaseCommand

from student.models import CourseEnrollment

from opaque_keys.edx.keys import CourseKey
#from common.djangoapps.third_party_auth.lti_consumers.willolabs.exceptions import LTIBusinessRuleError
#from opaque_keys.edx.locator import BlockUsageLocator

from lms.djangoapps.grades.api.v2.views import InternalCourseGradeView

u"""
  Willo Labs Grade Sync.
  Process all assignment grades from all students enrolled in course_id

  Run from the command line like this:
  cd /edx/app/edxapp/edx-platform
  sudo -u www-data /edx/bin/python.edxapp ./manage.py lms --settings aws gradesync course-v1:ABC+OS9471721_9626+01

"""
class Command(BaseCommand):
    help = u"Willo Labs Grade Sync. Post all assignment grades from all students enrolled in course_id."
    course_key = None
    course_id = None

    def add_arguments(self, parser):
        parser.add_argument('course_id', 
            type=str,
            help=u'A string representation of a CourseKey. Example: course-v1:ABC+OS9471721_9626+01'
            )

    def handle(self, *args, **kwargs):
        self.course_id = kwargs['course_id']

        self.stdout.write(self.style.NOTICE(u"gradesync.py ..."))

        self.course_key = self.set_course()
        if not self.course_key: 
            return None

        self.iterate_students()

        self.stdout.write(self.style.SUCCESS(u'gradesync.py - {course_id}'.format(
            course_id=self.course_id
        )))


    def iterate_students(self):
        """
         Iterate thru collection of students enrolled in course_id.
         Post grades to Willo Labs api.
        """
        students = CourseEnrollment.objects.users_enrolled_in(self.course_key)
        for student in students:
            self.post_student_grades(student)

        return None

    def post_student_grades(self, student):
        """
         Retrieve a json object of grade data for student.
         Iterate through chapters / assignments for the course.
         Post each assignment grade to Willo Labs api.

         https://dev.roverbyopenstax.org/grades_api/v2/courses/course-v1:ABC+OS9471721_9626+01/
        """

        self.stdout.write(u'post_student_grades() - retrieving username: {username}.'.format(
            username=student.username
        ))

        course_grades = InternalCourseGradeView()
        grades = course_grades.get(course_id=self.course_id, username=student.username)

        self.stdout.write(u'post_student_grades() - username: {username}. grades: {grades}'.format(
            username=student.username,
            grades=grades
        ))

    
    def set_course(self):
        try:
            key = CourseKey.from_string(self.course_id)
            return key
        except Exception as err:
            self.stdout.write(self.style.ERROR(u'set_course() - Not a valid course_id: {course_id}. {err}'.format(
                course_id=self.course_id,
                err=err
            )))
            return False
        


"""
    self.stdout.write(self.style.ERROR('error - A major error.'))
    self.stdout.write(self.style.NOTICE('notice - A minor error.'))
    self.stdout.write(self.style.SUCCESS('success - A success.'))
    self.stdout.write(self.style.WARNING('warning - A warning.'))
    self.stdout.write(self.style.SQL_FIELD('sql_field - The name of a model field in SQL.'))
    self.stdout.write(self.style.SQL_COLTYPE('sql_coltype - The type of a model field in SQL.'))
    self.stdout.write(self.style.SQL_KEYWORD('sql_keyword - An SQL keyword.'))
    self.stdout.write(self.style.SQL_TABLE('sql_table - The name of a model in SQL.'))
    self.stdout.write(self.style.HTTP_INFO('http_info - A 1XX HTTP Informational server response.'))
    self.stdout.write(self.style.HTTP_SUCCESS('http_success - A 2XX HTTP Success server response.'))
    self.stdout.write(self.style.HTTP_NOT_MODIFIED('http_not_modified - A 304 HTTP Not Modified server response.'))
    self.stdout.write(self.style.HTTP_REDIRECT('http_redirect - A 3XX HTTP Redirect server response other than 304.'))
    self.stdout.write(self.style.HTTP_NOT_FOUND('http_not_found - A 404 HTTP Not Found server response.'))
    self.stdout.write(self.style.HTTP_BAD_REQUEST('http_bad_request - A 4XX HTTP Bad Request server response other than 404.'))
    self.stdout.write(self.style.HTTP_SERVER_ERROR('http_server_error - A 5XX HTTP Server Error response.'))
    self.stdout.write(self.style.MIGRATE_HEADING('migrate_heading - A heading in a migrations management command.'))
    self.stdout.write(self.style.MIGRATE_LABEL('migrate_label - A migration name.'))

"""