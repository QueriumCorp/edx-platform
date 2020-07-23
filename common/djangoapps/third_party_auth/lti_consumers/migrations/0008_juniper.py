# McDaniel july-2020: split squashed migration into pre and post juniper.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import lms.djangoapps.courseware.fields
import model_utils.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    dependencies = [
        ('lti_consumers', '0001_squashed_0007'),
    ]

    operations = [
        migrations.CreateModel(
            name='LTIConfigurations',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, help_text='Example: KU - Willo Labs - Blackboard', max_length=255)),
                ('comments', models.TextField()),
            ],
            options={
                'verbose_name': 'LTI Configurations',
                'verbose_name_plural': 'LTI Configurations',
            },
        ),
        migrations.CreateModel(
            name='LTIInternalCourse',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(default=None, help_text='Rover Course Key (Opaque Key). Based on Institution, Course, Section identifiers. Example: course-v1:edX+DemoX+Demo_Course', max_length=255, primary_key=True, serialize=False)),
                ('enabled', models.BooleanField(default=False, help_text='True if LTI Grade Sync should be enabled for courses in this institution.')),
                ('lti_configuration', models.ForeignKey(help_text='Field mapping configuration to use for this Rover course.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='lti_consumers.LTIConfigurations')),
            ],
            options={
                'verbose_name': 'LTI Internal Rover Course',
                'verbose_name_plural': 'LTI Internal Rover Courses',
            },
        ),
        migrations.CreateModel(
            name='LTIConfigurationParams',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('table_name', models.CharField(blank=True, choices=[('LTIExternalCourse', 'LTIExternalCourse'), ('LTIExternalCourseEnrollment', 'LTIExternalCourseEnrollment'), ('LTIExternalCourseEnrollmentGrades', 'LTIExternalCourseEnrollmentGrades'), ('LTIExternalCourseAssignments', 'LTIExternalCourseAssignments'), ('LTIExternalCourseAssignmentProblems', 'LTIExternalCourseAssignmentProblems')], help_text='Example: LTIExternalCourseEnrollment', max_length=255)),
                ('internal_field', models.CharField(blank=True, help_text='Example: ext_wl_launch_key', max_length=255)),
                ('external_field', models.CharField(blank=True, help_text='Example: ext_wl_launch_key', max_length=255)),
                ('comments', models.TextField()),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti_consumers.LTIConfigurations')),
            ],
            options={
                'verbose_name': 'LTI Configuration Parameters',
                'verbose_name_plural': 'LTI Configuration Parameters',
            },
        ),
    ]
