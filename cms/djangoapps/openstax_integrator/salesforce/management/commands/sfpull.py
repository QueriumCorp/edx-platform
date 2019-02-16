from __future__ import with_statement
from __future__ import absolute_import
import os
from django.core.management.base import BaseCommand
from openstax_integrator.salesforce.models import Contact, Campaign
from openstax_integrator.salesforce.connector import Connection
from course_creators.models import CourseCreator
from simple_salesforce import SFType
from simple_salesforce.exceptions import SalesforceError

class Command(BaseCommand):
    help = u"Create salesforce campaign contact master records new " \
                u"Course Creators (aka Instructors)."

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument(u'-i', u'--insert', action=u'store_true', help=u'Insert new salesforce contacts.')
        parser.add_argument(u'-u', u'--update', action=u'store_true', help=u'Update existing salesforce contacts.')



    def handle(self, *args, **kwargs):
        insert = kwargs[u'insert']
        update = kwargs[u'update']

        # Fix Note: how is the "default" campaign determined?

        try:
            campaign = Campaign.objects.filter(active=True).first()
        except:
            raise EmptyResultSet(u"No salesforce campaign found. Hint: use " \
                                    u"Django Admin to create a Salesforce Campaign.")

        self.add_am_contacts()
        self.update_am_contacts()

    def update_am_contacts(self):
        # Add salesforce ContactID values to our contacts
        am_new_contacts = Contact.objects.filter(contact_id__isnull=True)

        if am_new_contacts.count() == 0:
            self.stdout.write(self.style.SUCCESS(u"Good news: Didn't find any " \
                                u"Contact records with missing salesforce.com ContactID's."))
            return

        self.stdout.write(self.style.NOTICE(u"Found {} AM Contacts with missing" \
                                u"salesforce contact ID value.".format(am_new_contacts.count())))

        self.stdout.write(self.style.NOTICE(u"Connecting to salesforce.com ..."))
        with Connection() as sf:
            self.stdout.write(self.style.SUCCESS(u"Connected to salesforce.com"))
            records_updated = 0
            for am_contact in am_new_contacts:
                am_email = am_contact.user.user.email.lower()
                self.stdout.write(self.style.NOTICE(u"Looking up salesforce" \
                                        u" ContactID for {}".format(am_email)))

                response = sf.query(u"SELECT Id FROM Contact WHERE Email = '{}'".format(am_email))
                sf_contact = response[u'records']

                if sf_contact:
                    self.stdout.write(self.style.SUCCESS(u"Found salesforce Contact record found for {}".format(am_email)))
                    am_contact.contact_id = sf_contact[0][u'Id']
                    am_contact.save()
                    records_updated += 1
                else:
                    self.stdout.write(self.style.WARNING(u"No salesforce Contact record found for {}".format(am_email)))
                    self.stdout.write(self.style.NOTICE(u"Trying to add new Contact record to salesforce for {}".format(am_email)))
                    new_sf_contact_last = am_contact.user.user.last_name or 'Missing'
                    new_sf_contact_email = am_email
                    new_sf_contact_obj = {'LastName': new_sf_contact_last, 'Email': new_sf_contact_email}
                    new_sf_contact = sf.Contact.create(new_sf_contact_obj)
                    records_updated += 1
                    self.stdout.write(self.style.SUCCESS(u"Added new Contact record to salesforce for {}".format(am_email)))
                    am_contact.contact_id = new_sf_contact['id']
                    am_contact.save()
                    self.stdout.write(self.style.SUCCESS(u"Update AM Contact with new salesforce ContactID for {}".format(am_email)))

            response = self.style.SUCCESS(u"Done. Updated {} Contacts with " \
                            u"salesforce.com ContactID values.".format(records_updated))
            self.stdout.write(response)



    def add_am_contacts(self):
        # CourseCreator rows with no corresponding master record in Contacts
        self.stdout.write(self.style.NOTICE(u"Looking for new Contact records to add..."))
        new_instructors = CourseCreator.objects.filter(state=u'granted').filter(contact__isnull=True)

        if new_instructors.count() == 0:
            self.stdout.write(self.style.NOTICE(u"No new Contact records to add."))
            return

        for instructor in new_instructors:
            self.stdout.write(u"adding new Instructor: " + instructor.user.username)
            contact = Contact(user=instructor, campaign=campaign)
            contact.save()

        self.stdout.write(self.style.SUCCESS(u"Finished adding new " \
                            u"Instructors to Contact records."))
