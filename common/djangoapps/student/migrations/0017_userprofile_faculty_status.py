# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-08-08 18:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0017_accountrecovery'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='faculty_status',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
    ]
