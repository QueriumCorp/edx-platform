# course_creators Django app

This is used for local development only. This is a minimal representation of the Open edX course_creators app.


Usage:
```
if os.environ["DJANGO_CONFIGURATION"] != "Local":
    # if our run-time environment is something other than Local
    # then use the Open edX CourseCreator model
    from ../some/other/path/course_creators.models import CourseCreator
else:
    # otherwise use our local simplified representation
    from ..course_creators.models import CourseCreator
```
