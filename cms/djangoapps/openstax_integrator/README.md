# openstax_integrator

[![Build Status](https://travis-ci.org/lpm0073/openstax_integrator.svg?branch=master)](https://travis-ci.org/lpm0073/openstax_integrator)
[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

Integrations for Rover OpenStax. **THIS IS THE REPO FOR LOCAL DEVELOPMENT**. openstax_integrator is intended to be packaged and installed to the Open edX platform via pip. [Built from Django REST Framework Cookie Cutter](https://github.com/agconti/cookiecutter-django-rest)


# salesforce.com
Provides a REST api to extract and manage sales data on instructors. The api is read-only to Open edX staff and provide full CRUD to superusers. Also provides a command-line utility callable from manage.py that pushes instructor sales data to salesforce.com.

Runs locally (DEBUG=True) as a self-contained Django project containing all necessary replicas of Open edX models. This same project can be packaged and installed to Open edX using pip.

Permissions: access to all REST api end points are limited to authenticated users marked as "Staff".

REST api
--------
- https://[your domain]/salesforce/v1/contacts/all
- https://[your domain]/salesforce/v1/contacts/new
- https://[your domain]/salesforce/v1/contacts/pending
- https://[your domain]/salesforce/v1/campaigns/
- https://[your domain]/salesforce/v1/coursecreators/
- https://[your domain]/salesforce/v1/docs/
- https://[your domain]/salesforce/v1/docs/schema/
- https://[your domain]/salesforce/v1/docs/swagger/

Django command-line utilities
--------
Local:
```
pipenv
python manage.py sfconfigtest   # test your Django admin Salesforce configuration parameters
python manage.py sfpull         # download & synch salesforce contactID values
python manage.py sfpush         # upload/update instructor "contacts" to salesforce.com
```

Open edX:
```
sudo -H -u edxapp bash << EOF
cd ~
source /edx/app/edxapp/edxapp_env

python /edx/app/edxapp/edx-platform/manage.py cms sfconfigtest --settings=aws   # test your Django admin Salesforce configuration parameters
python /edx/app/edxapp/edx-platform/manage.py cms sfpull --settings=aws         # download & synch salesforce contactID values
python /edx/app/edxapp/edx-platform/manage.py cms sfpush --settings=aws         # upload/update instructor "contacts" to salesforce.com

EOF
```

Django Admin console
--------
The salesforce integrations are fully maintainable from within the AM Django admin console.
![django admin console](https://raw.githubusercontent.com/QueriumCorp/openstax-integrator/master/docs/django_admin_screenshot.png)

Staff and/or Super Users can perform CRUD operations on contacts (aka Instructors).
![django admin contacts](https://raw.githubusercontent.com/QueriumCorp/openstax-integrator/master/docs/django_admin_contact.png)

Staff and/or Super Users can manage salesforce.com connectivity data. Modifications to the salesforce.com configuration parameters take effect immediately. You can test your salesforce.com connection parameters by using the Django command line utility ```python manage.py verifyconnectivity```
![django admin configuration](https://raw.githubusercontent.com/QueriumCorp/openstax-integrator/master/docs/django_admin_configuration.png)



# Installation
1. pip install yadda yadda
2. add these settings to INSTALLED_APPS
    ```
    INSTALLED_APPS += (
        ...
        # Third party apps
        'rest_framework',            # utilities for rest apis
        'rest_framework.authtoken',  # token authentication
        'django_filters',            # for filtering rest endpoints
        'rest_framework_swagger',

        # This project
        'openstax_integrator.users',
        'openstax_integrator.salesforce',
        'openstax_integrator.course_creators',
        ...
    )
    ```
3. add Django configurations for dev and production

# Back-port to Python 2.7
Open edX runs on Python 2.7 (yikes!). [You can read here](https://github.com/QueriumCorp/openstax-integrator/blob/python2.7/docs/legacy_installed.txt) about more about specific version requirements of installed pip packages.
