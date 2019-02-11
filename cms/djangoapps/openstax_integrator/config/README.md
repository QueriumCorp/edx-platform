# Environment-specific Django Configurations


common.py
--------
These parameters should be limited to name spaces that only exist in this project. any configuration parameters that MIGHT exist in Open edX pose a risk of breaking the production platform at run-time.

local.py
--------
Intended to be executed daily as a cron job. Creates new salesforce contact master records for Open edX Course Creators added since the last time sfpull was executed.

production.py
--------
For this project "production" means the Open edX platform, which is a beastly, inherently complex configuration. It's therefore recommended that you avoid adding any configuration parameters to this module.
