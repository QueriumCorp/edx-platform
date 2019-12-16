# LTI Integration for Willo Labs

Provides enhanced integration capabilities to WilloLab-connected external systems like Canvas, Blackboard, Moodle. Facilitates grade exports to the external system by building a map between LTI tpa_lti_params data passed to Rover during LTI authentication. This module infers and caches relationships between the tpa_lti_params data and Rover course_id, username, subsection.

**Provides efficient bidirectional integration capability between Rover and the external system for real-time student grade syncronization.**

## cache.py
Provides lazy-reader caching objects for course, course enrollment, and grades

## provisioners.py
Provides automated course provisioning capability so that, when/if necesary, students are automatically enrolled in the correct Rover course based on the LTI data passed to Rover during their LTI authentication.