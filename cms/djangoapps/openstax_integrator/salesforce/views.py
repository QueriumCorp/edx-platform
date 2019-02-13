from __future__ import absolute_import
import os
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics
from rest_framework.response import Response
from .models import Campaign, Contact
from .serializers import CampaignSerializer, ContactSerializer, CourseCreatorSerializer
from course_creators.models import CourseCreator

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer

    # make the contact list searchable by username instead of the int ID pk of the model.
    def retrieve(self, request, pk=None):
        queryset = Contact.objects.select_related(u'user').filter(user__user__username=pk)
        contact = get_object_or_404(queryset, pk=1)
        serializer = ContactSerializer(contact)
        return Response(serializer.data)

class AllContactViewSet(ContactViewSet):
    queryset = Contact.objects.select_related(u'user').filter(user__state=u'granted')

class PendingContactViewSet(ContactViewSet):
    valid_contacts = Contact.objects.select_related(u'user').filter(user__state=u'granted')
    queryset = valid_contacts.filter(salesforce_push_pending=True).filter(contact_id__isnull=False)

class NewContactViewSet(ContactViewSet):
    valid_contacts = Contact.objects.select_related(u'user').filter(user__state=u'granted')
    queryset = valid_contacts.filter(contact_id__isnull=True)

class CourseCreatorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CourseCreator.objects.all()
    serializer_class = CourseCreatorSerializer

class CampaignViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
