from course_creators.models import CourseCreator
from openstax_integrator.salesforce.models import Contact, Campaign
import logging
log = logging.getLogger(__name__)

def add_contact(user):
    try:
        campaign = Campaign.objects.filter(active=True).first()
    except:
        raise EmptyResultSet(u"No salesforce campaign found. Hint: use " \
                                u"Django Admin to create a Salesforce Campaign.")

    if CourseCreator.objects.filter(state=u'granted').filter(user=user).filter(contact__isnull=True):
        log.info('add_contact() - adding blank salesforce contact')
        contact_user = CourseCreator.objects.filter(state=u'granted').filter(user=user).get()
        contact = Contact(user=contact_user, campaign=campaign)
        contact.save()
    else:
        log.info('add_contact() - found existing salesforce contact. exiting.')
