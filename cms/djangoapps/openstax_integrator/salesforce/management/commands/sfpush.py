from __future__ import with_statement
from __future__ import absolute_import
from django.core.management.base import BaseCommand
from openstax_integrator.salesforce.models import Contact
from openstax_integrator.salesforce.connector import Connection
from pprint import pprint

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

        u"""
        Update or Insert salesforce.com CampaignMembers from AM Contacts.
        """
        self.sf_insert()


    def sf_insert(self):
        self.stdout.write(self.style.NOTICE(u"Begin updating salesforce.com CampaignMembers table ..."))

        u"""
            data = [
                  {'Id': '0000000000AAAAA', 'Email': 'examplenew2@example.com'},
                  {'Email': 'foo@foo.com'}
                ]

            sf.bulk.CampaignMember.upsert(data, 'Id')

            SELECT Email, CampaignID,
                  ContactID,
                  Initial_Sign_in_Date__c,
                  Most_recent_sign_in_date__c,
                  Completed_Training_Wheels_date__c,
                  Started_Assignment_date__c,
                  Completed_Assignment_date__c,
                  Soft_Ask_Decision__c,
                  Soft_Ask_Decision_date__c,
                  Estimated_Enrollment__c,
                  latest_adoption_decision__c FROM CampaignMember

            OrderedDict(
                [(u'totalSize', 2), (u'done', True),
                 (u'records',
                    [
                        OrderedDict([(u'attributes',
                        OrderedDict([(u'type', u'CampaignMember'),
                                     (u'url', u'/services/data/v38.0/sobjects/CampaignMember/00v0m000000NgWYAA0')
                                     ]
                                     )),
                                     (u'Email', u'denver@rice.edu'), (u'CampaignId', u'7010m0000002pARAAY'), (u'ContactId', u'0030m00000IzDI4AAN')]),

                        OrderedDict([(u'attributes',
                        OrderedDict([(u'type', u'CampaignMember'),
                                     (u'url', u'/services/data/v38.0/sobjects/CampaignMember/00v0m000000NgWZAA0')])),
                                     (u'Email', u'denver2@rice.edu'), (u'CampaignId', u'7010m0000002pARAAY'), (u'ContactId', u'0030m00000CMTuvAAH')])]
                                     )
                ]

                        )

        """

        sf_inserts = []
        contacts = Contact.objects.all()
        for contact in contacts:
            self.stdout.write(self.style.NOTICE(u"Preparing CampaignMember update for ContactID {}".format(contact.contact_id)))
            sf_campaign_member = {
                u'ContactID': contact.contact_id,
                u'CampaignID': '7010m0000002pARAAY',
                u'Initial_Sign_in_Date__c': '',
                u'Most_recent_sign_in_date__c': '',
                u'Completed_Training_Wheels_date__c': contact.completed_training_wheels_date,
                u'Started_Assignment_date__c': contact.started_assignment_date,
                u'Completed_Assignment_date__c': contact.completed_assignment_date,
                u'Soft_Ask_Decision__c': contact.soft_ask_decision,
                u'Soft_Ask_Decision_date__c': contact.soft_ask_decision_date,
                u'Students_Pell_Grant__c': '',
                u'Estimated_Enrollment__c': contact.estimated_enrollment,
                u'latest_adoption_decision__c': contact.latest_adoption_decision,
                }
            sf_inserts.append(sf_campaign_member)

        self.stdout.write(self.style.NOTICE(u"Connecting to salesforce ..."))
        with Connection() as sf:
            self.stdout.write(self.style.SUCCESS(u"Connected."))

            self.stdout.write(self.style.NOTICE(u"Sending {} inserts of CampaignMembers to salesforce.com ...".format(len(sf_inserts))))
            pprint(sf_inserts)
            results = sf.bulk.CampaignMember.insert(sf_inserts)
            # result should look like [{'errors': [], 'success': True, 'created': False, 'id': 'object_id_1'}]

            for result in results:
                if result['success']:
                    self.style.SUCCESS(u"Inserted Contact Id {}".format(result['id']))

                else:
                    pprint(result['errors'])
