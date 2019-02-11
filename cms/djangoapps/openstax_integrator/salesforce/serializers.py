from __future__ import absolute_import
import os
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Campaign, Contact
from course_creators.models import CourseCreator


class UserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = get_user_model()
        fields = (u'username', u'first_name', u'last_name', u'email', u'last_login', u'date_joined', u'is_active', u'is_superuser', u'is_staff')
        read_only_fields = (u'username', u'first_name', u'last_name', u'email', u'last_login', u'date_joined', u'is_active', u'is_superuser', u'is_staff')

class CourseCreatorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta(object):
        model = CourseCreator
        fields = u'__all__'

class CampaignSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Campaign
        fields = u'__all__'

class ContactSerializer(serializers.ModelSerializer):
    user = CourseCreatorSerializer(read_only=True)
    campaign = CampaignSerializer(read_only=True)

    class Meta(object):
        model = Contact
        fields = u'__all__'
        depth = 1
        read_only_fields = (u'created', u'updated', )
