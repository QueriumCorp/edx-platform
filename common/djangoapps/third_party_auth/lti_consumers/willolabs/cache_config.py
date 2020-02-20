"""
  McDaniel Jul-2019
  lpm0073@gmail.com
  https://lawrencemcdaniel.com
"""
from configparser import SafeConfigParser
import json

"""
  The provisioner.config file should be in the same folder as this Python module.
  Build a full absolute path to this file, then strip off the file name, leaving just the path.
"""

# these are fallback field mapping settings in case config.ini is missing or corrupted.
default_values = {
    "context_id": "context_id",
    "course_id": "course_id",
    "context_title": "context_title",
    "context_label": "context_label",
    "ext_wl_launch_key": "ext_wl_launch_key",
    "ext_wl_launch_url": "ext_wl_launch_url",
    "ext_wl_version": "ext_wl_version",
    "ext_wl_outcome_service_url": "ext_wl_outcome_service_url",
    "custom_api_domain": "custom_canvas_api_domain",
    "custom_course_id": "custom_canvas_course_id",
    "custom_course_startat": "custom_canvas_course_startat",
    "tool_consumer_info_product_family_code": "tool_consumer_info_product_family_code",
    "tool_consumer_info_version": "tool_consumer_info_version",
    "tool_consumer_instance_contact_email": "tool_consumer_instance_contact_email",
    "tool_consumer_instance_guid": "tool_consumer_instance_guid",
    "tool_consumer_instance_name": "tool_consumer_instance_name",
    "custom_user_id": "custom_canvas_user_id",
    "custom_user_login_id": "custom_canvas_user_login_id",
    "custom_person_timezone": "custom_canvas_person_timezone",
    "ext_roles": "ext_roles",
    "ext_wl_privacy_mode": "ext_wl_privacy_mode",
    "lis_person_contact_email_primary": "lis_person_contact_email_primary",
    "lis_person_name_family": "lis_person_name_family",
    "lis_person_name_full": "lis_person_name_full",
    "lis_person_name_given": "lis_person_name_given"
}

parser = SafeConfigParser(json.load(default_values))
parser.read('./cache_config.ini')
