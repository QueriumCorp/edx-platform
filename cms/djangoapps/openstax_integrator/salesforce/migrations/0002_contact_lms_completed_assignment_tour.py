# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-08-07 18:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salesforce', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='lms_completed_assignment_tour',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
