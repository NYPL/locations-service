import re
import os
import time

from functools import cache
from nypl_py_utils.classes.s3_client import S3Client

import lib.nypl_core
from lib.logger import GlobalLogger
from lib.errors import MissingEnvVar
from lib.refinery_api import get_refinery_data


@cache
def fetch_s3():
    bucket = os.environ.get('S3_BUCKET')
    resource = os.environ.get('S3_LOCATIONS_FILE')
    if bucket is None:
        raise MissingEnvVar('S3_BUCKET')
    if resource is None:
        raise MissingEnvVar('S3_LOCATIONS_FILE')
    s3_client = S3Client(bucket, resource)
    return {'data': s3_client.fetch_cache(), 'updated_at': time.time()}


def check_cache_or_fetch_s3():
    s3_data = fetch_s3()
    updated_at = s3_data.get('updated_at')
    s3_cache_invalidated = time.time() - updated_at > 3600
    if s3_data.get('data') is None or s3_cache_invalidated:
        fetch_s3.cache_clear()
        s3_data = fetch_s3()
    return s3_data.get('data')


def fetch_locations(location_codes, fields):
    location_dict = {}
    for code in location_codes:
        location_dict[code] = build_location_info(code, fields)
    return location_dict


# returns s3 location code, location url, and location label for a
# given sierra location code
def build_location_info(location_code, fields):
    GlobalLogger.logger.info(
        f'Accessing NYPL-core for location code: {location_code}')
    if location_code != 'rc':
        nypl_core_location_data = (lib.nypl_core
                                      .sierra_location_by_code(location_code))
    else:
        nypl_core_location_data = { 'label': 'ReCAP' }

    if nypl_core_location_data is None:
        GlobalLogger.logger.error(
            f'No nypl core data returned for location code: {location_code}')
        return []
    label = nypl_core_location_data.get('label')
    url = None
    code = None
    for s3_code, s3_url in check_cache_or_fetch_s3().items():
        # turn xxx* into ^(xxx)+
        regex = r'^(' + s3_code[0:-1] + ')+'
        if re.match(regex, location_code) is not None:
            # TODO: remove dependency on code property in DFE
            code = location_code
            url = s3_url
    refinery_data = get_refinery_data(location_code, fields)
    # original implementation of this code returned an array of multiple codes
    # which the front end would then filter through. We now only return one,
    # correct location, but it has to be in an array due to original contract.
    location_info = {'code': code, 'label': label}
    if 'url' in fields:
        location_info['url'] = url
    if 'location' in fields and refinery_data is not None:
        location_info['location'] = refinery_data.get('location')
    if 'hours' in fields and refinery_data is not None:
        location_info['hours'] = refinery_data.get('hours')
    return [location_info]
