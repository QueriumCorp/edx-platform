"""
Utility functions for third_party_auth
"""


from django.contrib.auth.models import User


def user_exists(details):
    """
    Return True if user with given details exist in the system.
    Arguments:
        details (dict): dictionary containing user infor like email, username etc.
    Returns:
        (bool): True if user with given details exists, `False` otherwise.
    """
    user_queryset_filter = {}
    email = details.get('email')
    username = details.get('username')
    if email:
        user_queryset_filter['email'] = email
    elif username:
        user_queryset_filter['username__iexact'] = username

    if user_queryset_filter:
        return User.objects.filter(**user_queryset_filter).exists()

    return False

"""
    mcdaniel nov-2019

    there are a couple of odd authentication work flows where we want to redirect the user to/from AM -> LMS.
    in these cases, we generally build an oauth signin url of the form https://{domain}/auth/login/{backend}/.

    this method codifies querium's preferences for which oauth backend to use depending on the configuration
    of this instance.
"""
def preferred_querium_backend():
    backend = None
    providers = Registry.displayed_for_login()

    if not providers:
        return None

    if providers.count == 1:
        backend = providers[0].slug

    for provider in providers:
        backend = str(provider.slug).lower()
        if backend == 'roverbyopenstax':
            return provider.slug

    for provider in providers:
        backend = str(provider.slug).lower()
        if backend == 'openstax':
            return provider.slug

    backend = providers[0].slug
    return backend
