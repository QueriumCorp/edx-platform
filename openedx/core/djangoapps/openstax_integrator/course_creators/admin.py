from __future__ import absolute_import
from django.contrib import admin

# Register your models here.


from django.contrib import admin
from .models import CourseCreator

admin.site.register(CourseCreator)
