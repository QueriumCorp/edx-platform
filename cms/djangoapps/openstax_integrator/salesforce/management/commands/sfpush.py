from __future__ import with_statement
from __future__ import absolute_import
from django.core.management.base import BaseCommand
from django.utils import timezone
from openstax_integrator.salesforce.models import Contact, Campaign
from openstax_integrator.salesforce.connector import Connection
from pprint import pprint
import datetime

u"""
  salesforce.com upserts.
  Example code: https://stackoverflow.com/questions/43286524/how-can-one-make-salesforce-bulk-api-calls-via-simple-salesforce
"""
class Command(BaseCommand):
    help = u"Insert/Update salesforce.com campaign contacts (ie Instructors)."

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument(u'-i', u'--insert', action=u'store_true', help=u'Insert new salesforce contacts.')
        parser.add_argument(u'-u', u'--update', action=u'store_true', help=u'Update existing salesforce contacts.')

    def handle(self, *args, **kwargs):
        insert = kwargs[u'insert']
        update = kwargs[u'update']


        self.sf_insert()
        self.sf_update()


    def sf_insert(self):
        self.stdout.write(self.style.NOTICE(u"salesforce.com interface: insert new CampaignMembers"))

        u"""
        Insert salesforce.com CampaignMembers from AM Contacts.
        """
        try:
            campaign = Campaign.objects.filter(active=True).first()
        except:
            raise EmptyResultSet(u"No salesforce campaign found. Hint: use " \
                                    u"Django Admin to create a Salesforce Campaign.")


        sf_inserts = []
        #contacts = Contact.objects.filter(salesforce_insert_pending=True)
        contacts = Contact.objects.all()
        for contact in contacts:
            sf_campaign_member = {
                u'accounts_uuid__c': contact.contact_id,
                u'ContactID': contact.contact_id,
                u'CampaignID': campaign.salesforce_id,
                u'Status': 'Sent'
                }
            sf_inserts.append(sf_campaign_member)

        self.stdout.write(self.style.NOTICE(u"Connecting to salesforce ..."))
        with Connection() as sf:
            self.stdout.write(self.style.SUCCESS(u"Connected."))

            self.stdout.write(self.style.NOTICE(u"Sending {} CampaignMember inserts to salesforce.com ...".format(len(sf_inserts))))
            results = sf.bulk.CampaignMember.insert(sf_inserts)

            self.stdout.write(self.style.SUCCESS(u"salesforce batch processing completed. Evaluating query results ..."))
            for result in results:
                # results:  [{'errors': [], 'success': True, 'created': False, 'id': 'object_id_1'}]
                if result['success']:
                    self.stdout.write(self.style.SUCCESS(u"Successfully inserted Contact Id {}".format(result['id'])))
                else:
                    for error in result['errors']:
                        if (error['statusCode'] == u"DUPLICATE_VALUE"):
                            self.stdout.write(self.style.SUCCESS(u"CampaignMember already exists."))
                        else:
                            self.stdout.write(self.style.ERROR(u"Please note the following statusCode: {}".format(error['statusCode'])))

            msg = u"Finished processing {} records. Note any record-level " \
                    "information/errors above that might have been reported " \
                    "by salesforce api.".format(len(sf_inserts))
            self.stdout.write(self.style.SUCCESS(msg))

    def sf_update(self):
        self.stdout.write(self.style.NOTICE(u"salesforce.com interface: update CampaignMembers"))

        u"""
        Update salesforce.com CampaignMembers from AM Contacts.
        """
        try:
            campaign = Campaign.objects.filter(active=True).first()
        except:
            raise EmptyResultSet(u"No salesforce campaign found. Hint: use " \
                                    u"Django Admin to create a Salesforce Campaign.")


        sf_updates = []
        contacts = Contact.objects.all()
        for contact in contacts:
            sf_campaign_member = {
                u'accounts_uuid__c': contact.contact_id,
                u'Initial_Sign_in_Date__c': self.serialDate(contact.user.user.date_joined),
                u'Most_recent_sign_in_date__c': self.serialDate(contact.user.user.last_login),
                u'Completed_Training_Wheels_date__c': self.serialDate(contact.completed_training_wheels_date),
                u'Started_Assignment_date__c': self.serialDate(contact.started_assignment_date),
                u'Completed_Assignment_date__c': self.serialDate(contact.completed_assignment_date),
                u'Soft_Ask_Decision__c': contact.soft_ask_decision,
                u'Soft_Ask_Decision_date__c': self.serialDate(contact.soft_ask_decision_date),
                u'Estimated_Enrollment__c': contact.estimated_enrollment,
                u'real_course_created_at__c': self.realCourseCreated(),
                u'latest_adoption_decision__c': contact.latest_adoption_decision
                }
            sf_updates.append(sf_campaign_member)

        self.stdout.write(self.style.NOTICE(u"Connecting to salesforce ..."))
        with Connection() as sf:
            self.stdout.write(self.style.SUCCESS(u"Connected."))

            self.stdout.write(self.style.NOTICE(u"Sending {} CampaignMember updates to salesforce.com ...".format(len(sf_updates))))
            results = sf.bulk.CampaignMember.upsert(sf_updates, "accounts_uuid__c")

            self.stdout.write(self.style.SUCCESS(u"salesforce batch processing completed. Evaluating query results ..."))
            for result in results:
                # results:  [{'errors': [], 'success': True, 'created': False, 'id': 'object_id_1'}]
                if result['success']:
                    self.stdout.write(self.style.SUCCESS(u"Successfully updated Contact Id {}".format(result['id'])))
                else:
                    self.stdout.write(self.style.ERROR(u"Some errors were encountered for Contact Id {}".format(result['id'])))
                    pprint(result['errors'])

            msg = u"Finished processing {} records. Note any record-level " \
                    "information/errors above that might have been reported " \
                    "by salesforce api.".format(len(sf_updates))
            self.stdout.write(self.style.SUCCESS(msg))

    def realCourseCreated(self):
        u"""
          Fix note: needs a real value.
          The date a real course is created, or once they start actually setting it up
        """
        return self.serialDate(timezone.now())

    def serialDate(self, o):
        if isinstance(o, datetime.datetime):
            #convert datetime object to a string, then strip off and return only the date characters.
            return o.__str__()[0:10]

        return None
