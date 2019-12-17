# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-12-17 16:41
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import lms.djangoapps.coursewarehistoryextended.fields
import model_utils.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LTIExternalCourse',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('context_id', models.CharField(help_text=b"This is the unique identifier of the Willo Labs integration, passed viafrom tpa-lti-params. Course runs from external LMS' are intended to be unique.Example: e14751571da04dd3a2c71a311dda2e1b", max_length=255, primary_key=True, serialize=False, verbose_name=b'Context ID')),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(blank=True, db_index=True, default=None, help_text=b'Rover Course Key (Opaque Key). Based on Institution, Course, Section identifiers. Example: course-v1:edX+DemoX+Demo_Course', max_length=255, null=True, verbose_name=b'Course Id')),
                ('context_title', models.CharField(blank=True, default=None, help_text=b'Name of the Willo Lab integration. Example: Rover by Openstax Gradesync Testing', max_length=50, null=True, verbose_name=b'Context Title')),
                ('context_label', models.CharField(help_text=b'Example: Rover', max_length=50, verbose_name=b'Context Label')),
                ('ext_wl_launch_key', models.CharField(help_text=b'Example: QcTz6q', max_length=50, verbose_name=b'External WilloLab Launch Key')),
                ('ext_wl_launch_url', models.URLField(help_text=b'Example: https://stage.willolabs.com/launch/QcTz6q/8cmzcd', verbose_name=b'External WilloLab Launch URL')),
                ('ext_wl_version', models.CharField(help_text=b'Example: 1.0', max_length=25, verbose_name=b'External WilloLab Version')),
                ('ext_wl_outcome_service_url', models.URLField(help_text=b'Example: https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/', verbose_name=b'External  Outcome Service URL')),
                ('custom_canvas_api_domain', models.CharField(help_text=b'Example: willowlabs.instructure.com', max_length=255, verbose_name=b'Custom Canvas API Domain')),
                ('custom_canvas_course_id', models.CharField(help_text=b'Example: 421', max_length=50, verbose_name=b'Custom Canvas Course ID')),
                ('custom_canvas_course_startat', models.DateTimeField(help_text=b'Example: 2019-12-11 16:18:01 -0500', verbose_name=b'Custom Canvas Course Start At')),
                ('tool_consumer_info_product_family_code', models.CharField(help_text=b'Example: canvas', max_length=50, verbose_name=b'Tool Consumer - Product Family Code')),
                ('tool_consumer_info_version', models.CharField(help_text=b'Example: cloud', max_length=50, verbose_name=b'Tool Consumer - Version')),
                ('tool_consumer_instance_contact_email', models.EmailField(help_text=b'Example: notifications@instructure.com', max_length=254, verbose_name=b'Tool Consumer - Contact Email Address')),
                ('tool_consumer_instance_guid', models.CharField(help_text=b'Example: 7M58pE4F4Y56gZHUe6jaxhQ1csaktjA00ZiVNQb7:canvas-lms', max_length=100, verbose_name=b'Tool Consumer - Instance GUID')),
                ('tool_consumer_instance_name', models.CharField(help_text=b'Example: Willo Labs', max_length=50, verbose_name=b'Tool Consumer - Instance Name')),
            ],
            options={
                'verbose_name': 'LTI External Course',
                'verbose_name_plural': 'LTI External Course',
            },
        ),
        migrations.CreateModel(
            name='LTIExternalCourseEnrollment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('lti_user_id', models.CharField(help_text=b'User ID provided by . Example: ab3e190fae668d925d007d79219fbfce90afba6d', max_length=255, verbose_name=b'User ID')),
                ('custom_canvas_user_id', models.CharField(blank=True, default=None, help_text=b'Canvas User ID provided to . Example: 394', max_length=25, null=True, verbose_name=b'Canvas User ID')),
                ('custom_canvas_user_login_id', models.CharField(blank=True, default=None, help_text=b'Canvas Username provided to . Example: rover_student', max_length=50, null=True, verbose_name=b'Canvas Username')),
                ('custom_canvas_person_timezone', models.CharField(blank=True, default=None, help_text=b"Canvas time zone from user's profile, provided to Willo Labs. Example: America/New_York", max_length=50, null=True, verbose_name=b'Canvas user time zone')),
                ('ext_roles', models.CharField(blank=True, default=None, help_text=b'User permitted roles in external system. Example: urn:lti:instrole:ims/lis/Student,urn:lti:role:ims/lis/Learner,urn:lti:sysrole:ims/lis/User', max_length=255, null=True, verbose_name=b'External System Roles')),
                ('ext_wl_privacy_mode', models.CharField(blank=True, default=None, help_text=b'Privacy settings from external system, provided to Willo Lab. Example: allow-pii-all', max_length=50, null=True, verbose_name=b'External WilloLab Privacy Mode')),
                ('lis_person_contact_email_primary', models.EmailField(help_text=b'Example: rover_student@willolabs.com', max_length=254, verbose_name=b'User - Primary Email Address')),
                ('lis_person_name_family', models.CharField(blank=True, default=None, help_text=b'Example: Thornton', max_length=50, null=True, verbose_name=b'User Family Name')),
                ('lis_person_name_full', models.CharField(blank=True, default=None, help_text=b'Example: Billy Bob Thornton', max_length=255, null=True, verbose_name=b'User Family Name')),
                ('lis_person_name_given', models.CharField(blank=True, default=None, help_text=b'Example: Billy Bob', max_length=255, null=True, verbose_name=b'User Given Name')),
                ('context_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='willolabs.LTIExternalCourse')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'LTI External Course Enrollment',
                'verbose_name_plural': 'LTI External Course Enrollment',
            },
        ),
        migrations.CreateModel(
            name='LTIExternalCourseEnrollmentGrades',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', lms.djangoapps.coursewarehistoryextended.fields.UnsignedBigIntAutoField(primary_key=True, serialize=False)),
                ('synched', models.DateTimeField(blank=True, help_text=b'The timestamp when this grade record was successfully posted to Willo Grade Sync.', null=True, verbose_name=b'Willo Posting Date')),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(help_text=b'Open edX Opaque Key course_id', max_length=255, verbose_name=b'Course ID')),
                ('usage_key', opaque_keys.edx.django.models.UsageKeyField(help_text=b'Open edX Course subsection key. Points to this homework assignment', max_length=255, verbose_name=b'Usage Key')),
                ('course_version', models.CharField(blank=True, help_text=b'Guid of latest course version', max_length=255)),
                ('earned_all', models.FloatField()),
                ('possible_all', models.FloatField()),
                ('earned_graded', models.FloatField()),
                ('possible_graded', models.FloatField()),
                ('first_attempted', models.DateTimeField(help_text=b"timestamp for the learner's first attempt at content in this subsection. Should contain a value")),
                ('context_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='willolabs.LTIExternalCourse')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'LTI External Course Enrollment Grades',
                'verbose_name_plural': 'LTI External Course Enrollment Grades',
            },
        ),
        migrations.AlterUniqueTogether(
            name='ltiexternalcourse',
            unique_together=set([('context_id', 'course_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='ltiexternalcourseenrollmentgrades',
            unique_together=set([('context_id', 'user', 'usage_key')]),
        ),
        migrations.AlterIndexTogether(
            name='ltiexternalcourseenrollmentgrades',
            index_together=set([('modified', 'course_id', 'usage_key'), ('first_attempted', 'course_id', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='ltiexternalcourseenrollment',
            unique_together=set([('context_id', 'user')]),
        ),
    ]                