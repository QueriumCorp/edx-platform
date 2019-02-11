from __future__ import with_statement
from __future__ import absolute_import
import os
from django.core.management.base import BaseCommand
from openstax_integrator.salesforce.models import Contact, Campaign
from openstax_integrator.salesforce.connector import Connection

if os.environ[u"DJANGO_CONFIGURATION"] != u"Local":
    # if our run-time environment is something other than Local
    # then use the Open edX CourseCreator model
    from  cms.djangoapps.course_creators.models import CourseCreator
else:
    # otherwise use our local simplified representation
    from openstax_integrator.course_creators.models import CourseCreator


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
            campaign = Campaign.objects.order_by(u'-id')[0]
        except:
            raise EmptyResultSet(u"No salesforce campaign found. Hint: use " \
                                    u"Django Admin to create a Salesforce Campaign.")

        # CourseCreator rows with no corresponding master record in Contacts
        self.stdout.write(self.style.NOTICE(u"Looking for new Contact records to add..."))
        new_instructors = CourseCreator.objects.filter(state=u'granted').filter(contact__isnull=True)

        if new_instructors.count() > 0:
            for instructor in new_instructors:
                self.stdout.write(u"adding new Instructor: " + instructor.user.username)
                contact = Contact(user=instructor, campaign=campaign)
                contact.save()

            self.stdout.write(self.style.SUCCESS(u"Finished adding new " \
                                u"Instructors to Contact records."))
        else:
            self.stdout.write(self.style.NOTICE(u"No new Contact records to add."))

        # Add salesforce ContactID values to our contacts
        self.stdout.write(self.style.NOTICE(u"Synching Contact records with salesforce.com ..."))
        contacts = Contact.objects.filter(contact_id__isnull=True)
        if contacts.count() == 0:
            self.stdout.write(self.style.SUCCESS(u"Good news: Didn't find any " \
                                u"Contact records with missing salesforce.com ContactID's."))
        else:
            self.stdout.write(self.style.NOTICE(u"Connecting to salesforce.com ..."))
            with Connection() as sf:
                self.stdout.write(self.style.SUCCESS(u"Connected."))

                response = sf.query_all(u"SELECT Email, ContactID FROM CampaignMember")
                sf_campaign_members = response[u'records']

                if not sf_campaign_members:
                    self.stdout.write(self.style.NOTICE(u"No CampaignMember records found in salesforce.com. Exiting."))
                else:
                    records_updated = 0
                    for sf_campaign_member in sf_campaign_members:
                        email = sf_campaign_member[u'Email']
                        self.stdout.write(self.style.NOTICE(u"Checking CampaignMember {}".format(email)))
                        contact = Contact.objects.select_related(u'user').filter(user__user__email=email)
                        if contact:
                            records_updated += 1
                            self.stdout.write(self.style.NOTICE(u"CampaignMember {} was found in contacts".format(email)))

                    response = self.style.SUCCESS(u"Updated {} Contacts with " \
                                    u"salesforce.com ContactID values.".format(records_updated))
                    self.stdout.write(response)
