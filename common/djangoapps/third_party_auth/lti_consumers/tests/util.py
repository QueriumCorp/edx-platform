"""
Misc utility functions for the test modules
"""
# python stuff
import logging
import json
import traceback

# AWS stuff
import boto3
from botocore.exceptions import ClientError

# django stuff
from django.conf import settings

THIS_SUBDOMAIN = settings.SITE_NAME.split('.')[0].lower()
log = logging.getLogger(__name__)

def s3_list_contents(bucket_name, path="/"):
    """Return a list of the qualified files in the S3 Bucket.

    Files are named using dot notation and are identifiable by the subdomain of the edxapp
    server on which they are intended to run.

    Example file:  my.mayville.json
    This would be the test file for Mayville College on MY


    """
    client = boto3.client('s3')

    try:
        retval = client.list_objects(Bucket=bucket_name, Prefix=path)
    except ClientError as e:
        log.info(__name__, 'lti_consumers.tests.util.s3_list_contents() - {err}'.format(err=e))
        return None

    files = []
    try:
        for dicts in retval['Contents']:
            key = str(dicts.get('Key'))
            if key != path:
                filename = key.replace(path, '')
                extension = filename.split('.')[-1].lower()
                domain = filename.split('.')[0].lower()
                if (domain == THIS_SUBDOMAIN) and (extension == 'json'):
                    files.append(filename)

        return files
    except Exception:
        return None


def lti_params_from_s3(bucket, file_name):
    """Download and return a tpa_lti_params object from
    an S3 bucket.

    Args:
        bucket (string): 'tests.roverbyopenstax.org'
        file_name (string): 'common/djangoapps/third_party_auth/lti_consumers/tests/data/tpa_lti_params/ku.json'

    Returns:
        [json]: parsed tpa_lti_params object
    """

    s3 = boto3.client('s3')
    with open(file_name, 'wb') as json_file:
        s3.download_fileobj(bucket, file_name, json_file)
        tpa_lti_params = json.load(json_file)

    return tpa_lti_params


def lti_params_from_fs(file_name):
    """
    file_name (string): 'generic.json'

    Returns:
        [json]: parsed tpa_lti_params object
    """
    with open('./data/tpa_lti_params/' + file_name) as json_file:
        data = json.load(json_file)
    return data[LTI_PARAMS_KEY]
