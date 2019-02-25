from __future__ import absolute_import
import os
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics
from rest_framework.response import Response
from .models import Campaign, Contact
from .serializers import ConfigurationSerializer


class ConfigurationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = ConfigurationSerializer
