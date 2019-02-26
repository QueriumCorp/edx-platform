"""
Public views
"""
from django.conf import settings
from django.template.context_processors import csrf
from django.urls import reverse
from django.shortcuts import redirect
from django.views.decorators.clickjacking import xframe_options_deny
from django.views.decorators.csrf import ensure_csrf_cookie

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.external_auth.views import redirect_with_get, ssl_get_cert_from_request, ssl_login_shortcut
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from waffle.decorators import waffle_switch
from contentstore.config import waffle

# mcdaniel - feb-2019
# imports for oAuth to openstax
import third_party_auth
from third_party_auth import pipeline
from third_party_auth.decorators import xframe_allow_whitelisted
from django.utils.translation import ugettext as _
from openedx.core.djangoapps.external_auth.login_and_register import login as external_auth_login
from openedx.core.djangoapps.external_auth.login_and_register import register as external_auth_register
from student.helpers import get_next_url_for_login_page
from django.contrib import messages
from student.helpers import (
    auth_pipeline_urls,
    get_next_url_for_login_page
)


__all__ = ['signup', 'login_page', 'howitworks', 'accessibility']


@ensure_csrf_cookie
@xframe_options_deny
def signup(request):
    """
    Display the signup form.
    """
    csrf_token = csrf(request)['csrf_token']
    if request.user.is_authenticated:
        return redirect('/course/')
    if settings.FEATURES.get('AUTH_USE_CERTIFICATES_IMMEDIATE_SIGNUP'):
        # Redirect to course to login to process their certificate if SSL is enabled
        # and registration is disabled.
        return redirect_with_get('login', request.GET, False)

    return render_to_response('register.html', {'csrf': csrf_token})


@ssl_login_shortcut
@ensure_csrf_cookie
@xframe_options_deny
def login_page(request):
    """
    Display the login form.
    """
    if (settings.FEATURES['AUTH_USE_CERTIFICATES'] and
            ssl_get_cert_from_request(request)):
        # SSL login doesn't require a login view, so redirect
        # to course now that the user is authenticated via
        # the decorator.
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('/course/')
    if settings.FEATURES.get('AUTH_USE_CAS'):
        # If CAS is enabled, redirect auth handling to there
        return redirect(reverse('cas-login'))

    # mcdaniel feb-2019: oAuth code from LMS login view
    #   /edx/app/edxapp/edx-platform/common/djangoapps/student/views/login.py signin_user()
    #   /edx/app/edxapp/edx-platform/lms/djangoapps/student_account/views.py  login_and_registration_form()
    # ---------------------------------------------------
    # Determine the URL to redirect to following login/registration/third_party_auth
    redirect_to = get_next_url_for_login_page(request)

    # ---------------------------------------------------
    if request.user.is_authenticated:
        return redirect(redirect_to)


    context = _get_login_context(request)
    return render_to_response('login.html', context)


def howitworks(request):
    "Proxy view"
    if request.user.is_authenticated:
        return redirect('/home/')
    else:
        context = _get_login_context(request)
        return render_to_response('howitworks.html', context)


@waffle_switch('{}.{}'.format(waffle.WAFFLE_NAMESPACE, waffle.ENABLE_ACCESSIBILITY_POLICY_PAGE))
def accessibility(request):
    """
    Display the accessibility accommodation form.
    """

    return render_to_response('accessibility.html', {
        'language_code': request.LANGUAGE_CODE
    })


"""
    ----------------------------------------------------------------------
    Code copied from
    /edx/app/edxapp/edx-platform/lms/djangoapps/student_account/views.py
"""
def _third_party_auth_context(request, redirect_to, tpa_hint=None):
    """Context for third party auth providers and the currently running pipeline.

    Arguments:
        request (HttpRequest): The request, used to determine if a pipeline
            is currently running.
        redirect_to: The URL to send the user to following successful
            authentication.
        tpa_hint (string): An override flag that will return a matching provider
            as long as its configuration has been enabled

    Returns:
        dict

    """
    context = {
        "currentProvider": None,
        "providers": [],
        "secondaryProviders": [],
        "finishAuthUrl": None,
        "errorMessage": None,
        "registerFormSubmitButtonText": _("Create Account"),
        "syncLearnerProfileData": False,
        "pipeline_user_details": {}
    }

    if third_party_auth.is_enabled():
        for enabled in third_party_auth.provider.Registry.displayed_for_login(tpa_hint=tpa_hint):
            info = {
                "id": enabled.provider_id,
                "name": enabled.name,
                "iconClass": enabled.icon_class or None,
                "iconImage": enabled.icon_image.url if enabled.icon_image else None,
                "loginUrl": pipeline.get_login_url(
                    enabled.provider_id,
                    pipeline.AUTH_ENTRY_LOGIN,
                    redirect_url=redirect_to,
                ),
                "registerUrl": pipeline.get_login_url(
                    enabled.provider_id,
                    pipeline.AUTH_ENTRY_REGISTER,
                    redirect_url=redirect_to,
                ),
            }
            context["providers" if not enabled.secondary else "secondaryProviders"].append(info)

        running_pipeline = pipeline.get(request)
        if running_pipeline is not None:
            current_provider = third_party_auth.provider.Registry.get_from_pipeline(running_pipeline)
            user_details = running_pipeline['kwargs']['details']
            if user_details:
                context['pipeline_user_details'] = user_details

            if current_provider is not None:
                context["currentProvider"] = current_provider.name
                context["finishAuthUrl"] = pipeline.get_complete_url(current_provider.backend_name)
                context["syncLearnerProfileData"] = current_provider.sync_learner_profile_data

                if current_provider.skip_registration_form:
                    # As a reliable way of "skipping" the registration form, we just submit it automatically
                    context["autoSubmitRegForm"] = True

        # Check for any error messages we may want to display:
        for msg in messages.get_messages(request):
            if msg.extra_tags.split()[0] == "social-auth":
                # msg may or may not be translated. Try translating [again] in case we are able to:
                context['errorMessage'] = _(unicode(msg))  # pylint: disable=translation-of-non-string
                break

    return context

def _external_auth_intercept(request, mode):
    """Allow external auth to intercept a login/registration request.

    Arguments:
        request (Request): The original request.
        mode (str): Either "login" or "register"

    Returns:
        Response or None

    """
    if mode == "login":
        return external_auth_login(request)
    elif mode == "register":
        return external_auth_register(request)


def _get_login_context(request):
    # mcdaniel feb-2019: oAuth code from LMS login view
    #   /edx/app/edxapp/edx-platform/common/djangoapps/student/views/login.py signin_user()
    #   /edx/app/edxapp/edx-platform/lms/djangoapps/student_account/views.py  login_and_registration_form()
    # ---------------------------------------------------
    # Determine the URL to redirect to following login/registration/third_party_auth
    redirect_to = get_next_url_for_login_page(request)

    # Allow external auth to intercept and handle the request
    ext_auth_response = _external_auth_intercept(request, "login")
    if ext_auth_response is not None:
        return ext_auth_response

    third_party_auth_error = None
    for msg in messages.get_messages(request):
        if msg.extra_tags.split()[0] == "social-auth":
            # msg may or may not be translated. Try translating [again] in case we are able to:
            third_party_auth_error = _(text_type(msg))  # pylint: disable=translation-of-non-string
            break


    # Our ?next= URL may itself contain a parameter 'tpa_hint=x' that we need to check.
    # If present, we display a login page focused on third-party auth with that provider.
    csrf_token = csrf(request)['csrf_token']
    third_party_auth_hint = None
    third_party_auth = _third_party_auth_context(request, redirect_to, third_party_auth_hint)
    platform_name = configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME)
    context = {
        ## mcdaniel: preserved from THIS template
        ## ----------------------
        'csrf': csrf_token,
        'forgot_password_link': "//{base}/login#forgot-password-modal".format(base=settings.LMS_BASE),
        'platform_name': platform_name,
        'login_redirect_url': redirect_to,  # This gets added to the query string of the "Sign In" button in the header
        ## ----------------------

        # Bool injected into JS to submit form if we're inside a running third-
        # party auth pipeline; distinct from the actual instance of the running
        # pipeline, if any.
        'pipeline_running': 'true' if pipeline.running(request) else 'false',
        'pipeline_url': auth_pipeline_urls(pipeline.AUTH_ENTRY_LOGIN, redirect_url=redirect_to),
        'third_party_auth': third_party_auth,
        'third_party_auth_hint': third_party_auth_hint or '',
        'third_party_auth_error': third_party_auth_error,
        # this "data" dictionary structure is copied from the lms view.
        # still do not know which (context body or data dict) is the right way
        # to send these params.
        'data': {
            'login_redirect_url': redirect_to,
            'third_party_auth': third_party_auth,
            'third_party_auth_hint': third_party_auth_hint or '',
            'platform_name': platform_name,
        },

    }
    # end of code copied from common and lms login views
    # ---------------------------------------------------
    return context
