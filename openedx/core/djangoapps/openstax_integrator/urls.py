from __future__ import absolute_import
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView

urlpatterns = [
    #re_path(ur'^$', RedirectView.as_view(url=u'salesforce/v1/docs/', permanent=False)),
    #path(u'admin/', admin.site.urls),
    #path(u'salesforce/v1/', include(u'openstax_integrator.salesforce.urls')),

    #url(u'admin/', admin.site.urls),
    url(u'salesforce/v1/', include(u'openstax_integrator.salesforce.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
