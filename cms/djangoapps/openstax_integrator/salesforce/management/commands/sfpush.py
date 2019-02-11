from __future__ import with_statement
from __future__ import absolute_import
from django.core.management.base import BaseCommand
from openstax_integrator.salesforce.models import Contact
from openstax_integrator.salesforce.connector import Connection

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
        grab all salesforce.com CampaignMembers.

        FIX NOTE: OpenStax will send a CampaignID value which we'll need to use to filter this recordset.
        """
        self.stdout.write(self.style.NOTICE(u"Connecting to salesforce.com ..."))
        with Connection() as sf:
            self.stdout.write(self.style.SUCCESS(u"Connected."))
            self.stdout.write(self.style.NOTICE(u"Querying CampaignMembers ..."))
            query = u"SELECT Email, CampaignID, " \
                      u"ContactID, " \
                      u"Initial_Sign_in_Date__c, " \
                      u"Most_recent_sign_in_date__c, " \
                      u"Completed_Training_Wheels_date__c, " \
                      u"Started_Assignment_date__c, " \
                      u"Completed_Assignment_date__c, " \
                      u"Soft_Ask_Decision__c, " \
                      u"Soft_Ask_Decision_date__c, " \
                      u"Estimated_Enrollment__c, " \
                      u"latest_adoption_decision__c FROM CampaignMember"
            sf_campaign_members = sf.bulk.CampaignMember.query(query)

            if sf_campaign_members:
                records_updated = 0
                for sf_campaign_member in sf_campaign_members:
                    email = sf_campaign_member[u'Email']
                    contact = Contact.objects.select_related(u'user').filter(user__user__email=email)

                    if contact:
                        self.stdout.write(self.style.NOTICE(u"Updating CampaignMember {}".format(email)))
                        sf_campaign_member[u'Initial_Sign_in_Date__c'] = contact.Initial_Sign_in_Date__c
                        sf_campaign_member[u'Most_recent_sign_in_date__c'] = contact.Most_recent_sign_in_date__c
                        sf_campaign_member[u'Completed_Training_Wheels_date__c'] = contact.Completed_Training_Wheels_date__c
                        sf_campaign_member[u'Started_Assignment_date__c'] = contact.Started_Assignment_date__c
                        sf_campaign_member[u'Completed_Assignment_date__c'] = contact.Completed_Assignment_date__c
                        sf_campaign_member[u'Soft_Ask_Decision__c'] = contact.Soft_Ask_Decision__c
                        sf_campaign_member[u'Soft_Ask_Decision_date__c'] = contact.Soft_Ask_Decision_date__c
                        sf_campaign_member[u'Students_Pell_Grant__c'] = contact.Students_Pell_Grant__c
                        sf_campaign_member[u'Estimated_Enrollment__c'] = contact.Estimated_Enrollment__c
                        sf_campaign_member[u'latest_adoption_decision__c'] = contact.latest_adoption_decision__c

                        records_updated = records_updated + 1

                self.stdout.write(self.style.NOTICE(u"Sending bulk update of CampaignMembers to salesforce.com ..."))
                result = sf.bulk.CampaignMember.update(sf_campaign_members)
                # result should look like [{'errors': [], 'success': True, 'created': False, 'id': 'object_id_1'}]

                if result[u'errors'].count() == 0:
                    response = self.style.SUCCESS(u"Successfully updated {} schools".format(records_updated))
                    self.stdout.write(response)
                else:
                    self.stdout.write(self.style.ERROR(u"Some errors were encountered while processing updates:"))
                    for err in result[u'errors']:
                        self.stdout.write(self.style.ERROR(err))
            else:
                self.stdout.write(self.style.NOTICE(u"No matching CampaignMember records found. Nothing to do. Exiting."))
