# salesforce Django app

Scaffolded with Django REST Framework Cookie Cutter.

management/commands/
--------
Each of these python files is callable from Django manage.py. [Read more here.](https://simpleisbetterthancomplex.com/tutorial/2018/08/27/how-to-create-custom-django-management-commands.html)

admin.py
--------
To register models with [Django Admin Console app](https://docs.djangoproject.com/en/2.1/ref/contrib/admin/).


connector.py
--------
Subclass of [simple_salesforce.Salesforce](https://readthedocs.org/projects/simple-salesforce/). This provides the connectivity to salesforce.com as well as awareness of the Django Admin Salesforce Configuration data. OpenStax (Michael Harrison) [provided this code sample](https://github.com/openstax/openstax-cms/blob/master/salesforce/salesforce.py) which I used to create this module.


models.py
--------
All are Generic [Django Models](https://docs.djangoproject.com/en/2.1/topics/db/models/). Nothing noteworthy about any of these.
- Campaign
- Contact
- Configuration

serializers.py
--------
Subclasses from [Django REST Framework Serializers](https://www.django-rest-framework.org/api-guide/serializers/) to serialize Django ORM model data into JSON representations.

urls.py
--------
[rest_framework router](https://www.django-rest-framework.org/api-guide/routers/) configuration for the REST api end points as well as introspection-based documentation

views.py
--------
implemented using [rest_framework ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/). This is the simplest possible implementation, offering fully-functional list and detail views with default behavior.


# salesforce.com Destination
![salesforce object manager](docs/salesforce_db_mgr_screenshot.png)
