# openstax_integrator: Integrations for Rover OpenStax.

[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

Installation
--------
1. Copy this folder into /edx/app/edxapp/edx-platform/cms/djangoapps/

2. add the following to cms.env.json
    ```
    "ADDL_INSTALLED_APPS": [
           "openstax_integrator.salesforce"
        ],
    ```
    ![cms.env.json configuration](docs/cms.env.json-config.png)

3. Add the following to /edx/app/edxapp/edx-platform/cms/urls.py on or around row 35
    ```
    urlpatterns = [
        # make this the first array entry. there will be around 75 existing entries in this array.
        url(r'^salesforce/v1/', include('openstax_integrator.salesforce.urls')),
    ```

    ![cms urls.py configuration](docs/cms-urls.py-config.png)

4. Run initial database migrations with this command. This is a Django thing to complete the app "registration").
    ```
    sudo -H -u edxapp -s bash
    cd ~
    source /edx/app/edxapp/edxapp_env
    python /edx/app/edxapp/edx-platform/manage.py cms makemigrations salesforce --settings=aw
    ```
    ![django makemigrations initial](docs/django-makemigrations-initial.png)


4. Run full Open edX migrations with this command from the Ubuntu command line as root
    ```
    sudo /root/edx.platform-migrations.sh
    ```
    ![open edx django migrations](docs/platform-migrations-installation.png)

5. Add a salesforce configuration using Django Admin Console: https://am.roveropenstax.com/admin/salesforce/configuration/

    ![django admin configuration](docs/django-admin-config.png)



Integrations for salesforce.com
--------
Provides a REST api to extract and manage sales data on instructors. The api is read-only to Open edX staff and provide full CRUD to superusers. Also provides a command-line utility callable from manage.py that pushes instructor sales data to salesforce.com.

Runs locally (DEBUG=True) as a self-contained Django project containing all necessary replicas of Open edX models. This same project can be packaged and installed to Open edX using pip.

Permissions: access to all REST api end points are limited to authenticated users marked as "Staff".

![salesforce Integrations diagram](docs/salesforce-integrations-diagram.png)
![salesforce Integrations definitions](docs/salesforce-integrations-definitions.png)


Swagger Online Documentation
--------
This module provides documentation in two formats: Django REST api "schema", and Swagger. Swagger is overwhelmingly the better option, especially is you're new to this api.

![Swagger api documentation home screen](docs/swagger-screen-1.png)
![Swagger api documentation example resource](docs/swagger-screen-2.png)


manage.py command-line utilities
--------
```
sudo -H -u edxapp bash << EOF
cd ~
source /edx/app/edxapp/edxapp_env
python /edx/app/edxapp/edx-platform/manage.py cms sfconfigtest --settings=aws   # test your Django admin Salesforce configuration parameters
EOF
```
![open edx django migrations](docs/sfconfigtest.png)


```
sudo -H -u edxapp bash << EOF
cd ~
source /edx/app/edxapp/edxapp_env
python /edx/app/edxapp/edx-platform/manage.py cms sfpull --settings=aws         # download & synch salesforce contactID values
EOF
```
![open edx django migrations](docs/sfpull.png)


```
sudo -H -u edxapp bash << EOF
cd ~
source /edx/app/edxapp/edxapp_env
python /edx/app/edxapp/edx-platform/manage.py cms sfpush --settings=aws         # upload/update instructor "contacts" to salesforce.com
EOF
```


Django Admin console
--------
The salesforce integrations are fully maintainable from within the AM Django admin console.
![django admin console](docs/django_admin_screenshot.png)

Staff and/or Super Users can perform CRUD operations on contacts (aka Instructors).
![django admin contacts](docs/django_admin_contact.png)

Staff and/or Super Users can manage salesforce.com connectivity data. Modifications to the salesforce.com configuration parameters take effect immediately. You can test your salesforce.com connection parameters by using the Django command line utility ```python manage.py verifyconnectivity```
![django admin configuration](docs/django_admin_configuration.png)
