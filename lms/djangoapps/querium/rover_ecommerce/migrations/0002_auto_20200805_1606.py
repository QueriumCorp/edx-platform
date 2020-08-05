# Generated by Django 2.2.13 on 2020-08-05 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rover_ecommerce', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eopwhitelist',
            options={'verbose_name': 'Rover E-Commerce Payment Exemption', 'verbose_name_plural': 'Rover E-Commerce Payment Exemptions'},
        ),
        migrations.AddField(
            model_name='eopwhitelist',
            name='type',
            field=models.CharField(choices=[('eop_student', 'EOP Student'), ('tester', 'Rover Tester'), ('free_retake', 'Free Retake')], default='eop_student', help_text='Type of E-Commerce whitelist user.', max_length=24, unique=True),
        ),
    ]
