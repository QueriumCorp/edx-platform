from __future__ import absolute_import
import os
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Configuration


class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Configuration
        fields = u'__all__'
