"""
The native course export command that is invoked from the AM Course Export menu.
This command will export a course to a tar.gz file.

If <filename> is '-', it pipes the file to stdout.

At present, it differs from Studio exports in several ways:

* It does not include static content.
* The top-level directory in the resulting tarball is a "safe"
  (i.e. ascii) version of the course_key, rather than the word "course".
* It only supports the export of courses.  It does not export libraries.
"""
from textwrap import dedent

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from cms.djangoapps.contentstore.tasks import CourseExportTask, export_olx


User = get_user_model()


class Command(BaseCommand):
    """
    Call CMS native course export.
    This is the same code that is invoked from the AM Course Export menu option.

    For reference see: cms.djangoapps.contentstore.views.import_export.export_handler()
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            'course_id',
            help=u"a valid CourseKey string. Example: course-v1:KNCL+DemoX_3930+Fall2020_KNCL_Test"
        )
        parser.add_argument(
            'username',
            help=u"a valid active Rover username with admin/superuser privileges. Example: admin"
            )

    def handle(self, *args, **options):
        course_id = options['course_id']
        username = options['username']

        print('Course_id: {course_id}, username: {username}'.format(
            course_id=course_id,
            username=username
        ))
        user = User.objects.get(username=username)
        language_code = 'en'
        export_olx.delay(user.id, course_id, language_code)
