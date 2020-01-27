# LTI Integration for Willo Labs

Canvas via Willo Integration:
===================
https://willowlabs.instructure.com/
un: rover_teach
pw: WilloTest1

https://willowlabs.instructure.com/
un: rover_learner
pw: WilloTest1

Provides enhanced integration capabilities to WilloLab-connected external systems like Canvas, Blackboard, Moodle. Facilitates grade exports to the external system by building a map between LTI tpa_lti_params data passed to Rover during LTI authentication. This module infers and caches relationships between the tpa_lti_params data and Rover course_id, username, subsection.

Makes copious use of Opaque keys. Read more here: https://github.com/edx/edx-platform/wiki/Opaque-Keys-(Locators)

**Provides efficient bidirectional integration capability between Rover and the external system for real-time student grade syncronization.**

## cache.py
Provides lazy-reader caching objects for course, course enrollment, assignments, and grades

## provisioners.py
Provides automated course provisioning capability so that, when/if necesary, students are automatically enrolled in the correct Rover course based on the LTI data passed to Rover during their LTI authentication.

## tasks.py
Real-time Willo Labs Grade Sync. Called asynchronously via Celery when Rover students click the submit button
on a Rover assignment problem. Calculates the grade and posts to Willo Labs api.

## utils.py
Willo Labs api methods.

## management.commands.gradesync.py
Command-line tool to bulk grade sync all students / all assignments for a course_id.