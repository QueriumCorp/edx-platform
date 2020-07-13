"""Manager for cache_config.ini cache field mapping configuration file."""

from configparser import ConfigParser
import os
from .constants import WORKING_PATH

CONFIG_FILENAME = 'cache_config.ini'

"""these are fallback field mapping settings
in case config.ini is missing or corrupted.
"""
default_values = {
    "context_id": "context_id",
    "course_id": "course_id",
    "context_title": "context_title",
    "context_label": "context_label",

    "ext_roles": "ext_roles",

    "ext_wl_launch_key": "ext_wl_launch_key",
    "ext_wl_launch_url": "ext_wl_launch_url",
    "ext_wl_version": "ext_wl_version",
    "ext_wl_outcome_service_url": "ext_wl_outcome_service_url",
    "ext_wl_privacy_mode": "ext_wl_privacy_mode",

    "tool_consumer_info_product_family_code": "tool_consumer_info_product_family_code",
    "tool_consumer_info_version": "tool_consumer_info_version",
    "tool_consumer_instance_contact_email": "tool_consumer_instance_contact_email",
    "tool_consumer_instance_guid": "tool_consumer_instance_guid",
    "tool_consumer_instance_name": "tool_consumer_instance_name",

    "lis_person_contact_email_primary": "lis_person_contact_email_primary",
    "lis_person_name_family": "lis_person_name_family",
    "lis_person_name_full": "lis_person_name_full",
    "lis_person_name_given": "lis_person_name_given",

    "custom_api_domain": "NO_DEFAULT_PARAMETER",
    "custom_course_id": "NO_DEFAULT_PARAMETER",
    "custom_course_startat": "NO_DEFAULT_PARAMETER",
    "custom_user_id": "NO_DEFAULT_PARAMETER",
    "custom_user_login_id": "NO_DEFAULT_PARAMETER",
    "custom_person_timezone": "NO_DEFAULT_PARAMETER"
}

parser = ConfigParser(default_values)

# mcdaniel: feb-2020
# Fix DeprecationWarning: You passed a bytestring as `filenames`. This will not work on Python 3. Use `cp.read_file()` or switch to using Unicode strings across the board.
filename = os.path.join(WORKING_PATH, CONFIG_FILENAME)

# mcdaniel: may-2020
# CONFIRMED! this breaks in python3
#filename = filename.decode()
parser.read(filename)
