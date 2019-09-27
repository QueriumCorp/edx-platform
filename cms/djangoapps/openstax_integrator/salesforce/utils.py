from course_creators.models import CourseCreator
from openstax_integrator.salesforce.models import Contact, Campaign
import logging
log = logging.getLogger(__name__)

def add_contact(user):
    """
      check to see if this user IS a course creator but does NOT yet have a
      salesforce contact record.
    """
    if CourseCreator.objects.filter(state=u'granted').filter(user=user).filter(contact__isnull=True):
        campaign = Campaign.objects.filter(active=True).first()
        if not campaign:
            log.warning(u"openstax_integrator add_contact(): " \
                        u"No salesforce campaign found. Hint: use " \
                        u"Django Admin to create a Salesforce Campaign.")
            return

        contact_user = CourseCreator.objects.filter(state=u'granted').filter(user=user).get()
        contact = Contact(user=contact_user, campaign=campaign)
        contact.save()
        log.info('add_contact() - added blank salesforce contact for {username}'.format(
                username=user.username)
                )
