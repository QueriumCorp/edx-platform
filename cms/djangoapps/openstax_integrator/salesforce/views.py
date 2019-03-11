from __future__ import absolute_import
import os
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics
from rest_framework.response import Response
from .models import Campaign, Contact
from .serializers import CampaignSerializer, ContactSerializer, CourseCreatorSerializer
from course_creators.models import CourseCreator

from logging import getLogger
logger = getLogger(__name__)


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    queryset = Contact.objects.select_related(u'user').filter(user__state=u'granted')

   # make the contact list searchable by username instead of the int ID pk of the model.
    def retrieve(self, request, pk=None):
        logger.info('ContactViewSet.retrieve() {}'.format(pk))

        queryset = Contact.objects.select_related(u'user').filter(user__user__username=pk)
        contact = get_object_or_404(queryset)
        serializer = ContactSerializer(contact)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.get('partial', False)
        pk = kwargs.get('pk', False)
        logger.info('ContactViewSet.update() kwargs: {kwargs}, pk: {pk}'.format(kwargs = kwargs, pk = pk))

        queryset = Contact.objects.select_related(u'user').filter(user__user__username=pk)
        instance = get_object_or_404(queryset)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class CourseCreatorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CourseCreator.objects.all()
    serializer_class = CourseCreatorSerializer

class CampaignViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
