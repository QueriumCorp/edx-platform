# McDaniel july-2020: these are the net migrations thru hawthorn end of life.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import lms.djangoapps.courseware.fields
import model_utils.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    replaces = [('lti_consumers', '0001_initial'), ('lti_consumers', '0002_auto_20200220_1718'), ('lti_consumers', '0003_auto_20200227_1448'), ('lti_consumers', '0004_auto_20200304_1443'), ('lti_consumers', '0005_ltiexternalcourse_enabled'), ('lti_consumers', '0006_auto_20200501_1434'), ('lti_consumers', '0007_auto_20200604_2124')]

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
                ('context_id', models.CharField(help_text="This is the unique identifier of the LTI Consumer integration, passed viafrom tpa-lti-params. Course runs from external LMS' are intended to be unique.Example: e14751571da04dd3a2c71a311dda2e1b", max_length=255, primary_key=True, serialize=False)),
                ('enabled', models.BooleanField(default=False, help_text='True if grade results for this course should be posted to LTI Grade Sync API.')),
                ('context_title', models.CharField(blank=True, default=None, help_text='Name of the LTI Consumer integration. Example: Willo Labs Test Launch for KU Blackboard Rover Grade Testing', max_length=255, null=True)),
                ('context_label', models.CharField(blank=True, help_text='Example: willolabs-launch-test-ku-blackboard-rover-grade-testing', max_length=255, null=True)),
                ('ext_wl_launch_key', models.CharField(blank=True, help_text='Example: QcTz6q', max_length=50, null=True)),
                ('ext_wl_launch_url', models.URLField(blank=True, help_text='Example: https://stage.willolabs.com/launch/QcTz6q/8cmzcd', null=True)),
                ('ext_wl_version', models.CharField(blank=True, help_text='Example: 1.0', max_length=25, null=True)),
                ('ext_wl_outcome_service_url', models.URLField(blank=True, help_text='Example: https://stage.willolabs.com/api/v1/outcomes/QcTz6q/e14751571da04dd3a2c71a311dda2e1b/', null=True)),
                ('custom_tpa_next', models.URLField(blank=True, help_text='/account/finish_auth?course_id=course-v1%3AKU%2BOS9471721_108c%2BSpring2020_Fuka_Sample1&enrollment_action=enroll&email_opt_in=false', max_length=255, null=True)),
                ('custom_orig_context_id', models.CharField(blank=True, help_text='Context_id from the original source system (ie Canvas, Blackboard). Example: 9caf71ef12da4d2993f8929242d93922', max_length=50, null=True)),
                ('custom_profile_url', models.URLField(blank=True, help_text='URL pointing to user profile in the original source system. Example: https://courseware.ku.edu/learn/api/v1/lti/profile?lti_version=LTI-1p0', max_length=50, null=True)),
                ('tool_consumer_instance_description', models.CharField(blank=True, help_text='Example: The University of Kansas', max_length=50, null=True)),
                ('custom_api_domain', models.CharField(blank=True, help_text='Example: willowlabs.instructure.com', max_length=255, null=True)),
                ('custom_course_id', models.CharField(blank=True, help_text='Example: 421', max_length=50, null=True)),
                ('custom_course_startat', models.DateTimeField(blank=True, help_text='Example: 2019-12-11 16:18:01 -0500', null=True)),
                ('tool_consumer_info_product_family_code', models.CharField(blank=True, help_text='Example: canvas', max_length=50, null=True)),
                ('tool_consumer_info_version', models.CharField(blank=True, help_text='Example: cloud', max_length=50, null=True)),
                ('tool_consumer_instance_contact_email', models.EmailField(blank=True, help_text='Example: notifications@instructure.com', max_length=254, null=True)),
                ('tool_consumer_instance_guid', models.CharField(blank=True, help_text='Example: 7M58pE4F4Y56gZHUe6jaxhQ1csaktjA00ZiVNQb7:canvas-lms', max_length=100, null=True)),
                ('tool_consumer_instance_name', models.CharField(blank=True, help_text='Example: Willo Labs', max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'LTI External Course',
            },
        ),
        migrations.CreateModel(
            name='LTIExternalCourseAssignments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('url', models.URLField(help_text='Open edX Course Assignment', max_length=255)),
                ('display_name', models.CharField(help_text='Title text of the Rover assignment. Example: Chapter 5 Section 1 Quadratic Functions Sample Homework', max_length=255)),
                ('due_date', models.DateTimeField(blank=True, help_text='The Rover assignment due date.', null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti_consumers.LTIExternalCourse')),
            ],
            options={
                'unique_together': {('course', 'url')},
                'verbose_name': 'LTI External Course Assignments',
                'verbose_name_plural': 'LTI External Course Assignments',
            },
        ),
        migrations.CreateModel(
            name='LTIExternalCourseEnrollment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('lti_user_id', models.CharField(help_text='User ID provided by . Example: ab3e190fae668d925d007d79219fbfce90afba6d', max_length=255)),
                ('custom_user_id', models.CharField(blank=True, default=None, help_text='User ID provided to LTI Consumer. Example: 394', max_length=25, null=True)),
                ('custom_user_login_id', models.CharField(blank=True, default=None, help_text='Login ID provided to LTI Consumer. Example: rover_lti_consumers', max_length=50, null=True)),
                ('custom_person_timezone', models.CharField(blank=True, default=None, help_text="Source system time zone from user's profile, provided to LTI Consumer. Example: America/New_York", max_length=50, null=True)),
                ('ext_roles', models.CharField(blank=True, default=None, help_text='User permitted roles in external system. Example: urn:lti:instrole:ims/lis/lti_consumers,urn:lti:role:ims/lis/Learner,urn:lti:sysrole:ims/lis/User', max_length=255, null=True)),
                ('ext_wl_privacy_mode', models.CharField(blank=True, default=None, help_text='Privacy settings from external system, provided to LTI Consumer. Example: allow-pii-all', max_length=50, null=True)),
                ('lis_person_contact_email_primary', models.EmailField(help_text='Example: rover_lti_consumers@willolabs.com', max_length=254, null=True)),
                ('lis_person_name_family', models.CharField(blank=True, default=None, help_text='Example: Thornton', max_length=50, null=True)),
                ('lis_person_name_full', models.CharField(blank=True, default=None, help_text='Example: Billy Bob Thornton', max_length=255, null=True)),
                ('lis_person_name_given', models.CharField(blank=True, default=None, help_text='Example: Billy Bob', max_length=255, null=True)),
                ('lis_person_sourcedid', models.CharField(blank=True, default=None, help_text='Example: _tonn_test5', max_length=255, null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti_consumers.LTIExternalCourse')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('course', 'user')},
                'verbose_name': 'LTI External Course Enrollment',
            },
        ),
        migrations.CreateModel(
            name='LTIExternalCourseEnrollmentGrades',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', lms.djangoapps.courseware.fields.UnsignedBigIntAutoField(primary_key=True, serialize=False)),
                ('synched', models.DateTimeField(blank=True, help_text='The timestamp when this grade record was successfully posted to LTI Grade Sync.', null=True)),
                ('section_url', models.URLField(help_text='Open edX Course Assignment', max_length=255)),
                ('usage_key', opaque_keys.edx.django.models.UsageKeyField(help_text='Open edX Block usage key pointing to the homework problem that was graded, invoking the post_grades() api.', max_length=255)),
                ('earned_all', models.FloatField()),
                ('possible_all', models.FloatField()),
                ('earned_graded', models.FloatField()),
                ('possible_graded', models.FloatField()),
                ('course_assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti_consumers.LTIExternalCourseAssignments')),
                ('course_enrollment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti_consumers.LTIExternalCourseEnrollment')),
            ],
            options={
                'verbose_name': 'LTI External Course Enrollment Grades',
                'verbose_name_plural': 'LTI External Course Enrollment Grades',
            },
        ),
        migrations.AddField(
            model_name='ltiexternalcourse',
            name='course_id',
            field=models.ForeignKey(help_text='Rover Course Key (Opaque Key). Based on Institution, Course, Section identifiers. Example: course-v1:edX+DemoX+Demo_Course', null=True, on_delete=django.db.models.deletion.SET_NULL, to='lti_consumers.LTIInternalCourse'),
        ),
        migrations.CreateModel(
            name='LTIExternalCourseAssignmentProblems',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('usage_key', opaque_keys.edx.django.models.UsageKeyField(help_text='Open edX Block usage key pointing to the homework problem that was graded, invoking the post_grades() api. Example: block-v1:ABC+OS9471721_9626+01+type@swxblock+block@c081d7653af211e98379b7d76f928163', max_length=255)),
                ('course_assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti_consumers.LTIExternalCourseAssignments')),
            ],
            options={
                'unique_together': {('usage_key',)},
                'verbose_name': 'LTI External Course Assignment Problems',
                'verbose_name_plural': 'LTI External Course Assignment Problems',
            },
        ),
        migrations.AlterUniqueTogether(
            name='ltiexternalcourse',
            unique_together={('context_id', 'course_id')},
        ),
    ]
