# Stepwise Django app

Scaffolded with Django REST Framework Cookie Cutter.

admin.py
--------
To register models with [Django Admin Console app](https://docs.djangoproject.com/en/2.1/ref/contrib/admin/).


models.py
--------
All are Generic [Django Models](https://docs.djangoproject.com/en/2.1/topics/db/models/). Nothing noteworthy about any of these.
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
