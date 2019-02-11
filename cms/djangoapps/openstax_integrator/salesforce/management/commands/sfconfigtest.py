from __future__ import with_statement
from __future__ import absolute_import
from django.core.management.base import BaseCommand
from openstax_integrator.salesforce.connector import Connection


class Command(BaseCommand):
    help = u"Tests Django Admin Salesforce/Configuration settings."

    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.NOTICE(u"Connecting to salesforce.com ..."))
        with Connection() as sf:
            self.stdout.write(self.style.SUCCESS(u"Successfully connected to salesforce.com. Your configuration works."))
