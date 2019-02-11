# Django Command-Line Interface

Custom Django manage.py functions
See: https://simpleisbetterthancomplex.com/tutorial/2018/08/27/how-to-create-custom-django-management-commands.html


sfconfigtest.py
--------
Validates configuration parameters stored in Django Admin Salesforce/Configurations. Returns a confirmation message if successful, an error stack trace otherwise.

sfpull.py
--------
Intended to be executed daily as a cron job. Creates new local salesforce contact master records for Open edX Course Creators added since the last time sfpull was executed. The local (ie Open edX db) Contact object stores the salesforce.com contactID value which we use for record updates in sfpush.py.

sfpush.py
--------
Intended to be executed daily as a cron job. Inserts/Updates salesforce contact records to salesforce.com using the connection parameters stored in Django Admin Console - Salesforce/Configuration. sfpush.py adds data to the salesforce.com table CampaignMember, which contains all of the custom fields that OpenStax uses for tracking the Instructor marketing process.

- Insert: Add new salesforce.com Contact (and CampaignManager????) record(s). This method handles an exception: In a "normal" work flow an Instructor first creates an account on OpenStax and then later creates an account on Rover; ideally using our single-sign feature to "Login with OpenStax". OpenStax creates a new salesforce.com Contact record in their new Instructor on-boarding process. Thus, when running sfpush.py we expect to encounter zero AM Contacts who are missing a corresponding salesforce.com Contact record. OpenStax marketing

- Update: Iterates the entire saleforce.com CampaignManager rowset, copying the corresponding field values of the local Contacts master record to the CampaignManager.

**The marketing team at OpenStax has emphasized multiple times that it is important to commit these operations by batch rather than on a record-by-record basis due to salesforce.com rate-limits.**

django.core.management.base.BaseCommand.style
--------
error - A major error.
notice - A minor error.
success - A success.
warning - A warning.
sql_field - The name of a model field in SQL.
sql_coltype - The type of a model field in SQL.
sql_keyword - An SQL keyword.
sql_table - The name of a model in SQL.
http_info - A 1XX HTTP Informational server response.
http_success - A 2XX HTTP Success server response.
http_not_modified - A 304 HTTP Not Modified server response.
http_redirect - A 3XX HTTP Redirect server response other than 304.
http_not_found - A 404 HTTP Not Found server response.
http_bad_request - A 4XX HTTP Bad Request server response other than 404.
http_server_error - A 5XX HTTP Server Error response.
migrate_heading - A heading in a migrations management command.
migrate_label - A migration name.
