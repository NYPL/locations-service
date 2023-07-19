import re
import os

from nypl_py_utils.classes.s3_client import S3Client

import lib.nypl_core
from lib.logger import GlobalLogger
from lib.errors import MissingEnvVar

CACHE = {}


def init():
    if CACHE.get('s3_locations') is None:
        bucket = os.environ.get('S3_BUCKET')
        resource = os.environ.get('S3_LOCATIONS_FILE')
        if bucket is None:
            raise MissingEnvVar('S3_BUCKET')
        if resource is None:
            raise MissingEnvVar('S3_LOCATIONS_FILE')
        s3_client = S3Client(bucket, resource)
        CACHE['s3_locations'] = s3_client.fetch_cache()


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
    nypl_core_location_data = (lib.nypl_core
                                  .sierra_location_by_code(location_code))
    if nypl_core_location_data is None:
        GlobalLogger.logger.error(
            f'No nypl core data returned for location code: {location_code}')
        return []
    label = nypl_core_location_data.get('label')
    url = None
    code = None
    for s3_code, s3_url in CACHE.get('s3_locations').items():
        # turn xxx* into ^(xxx)+
        regex = r'^(' + s3_code[0:-1] + ')+'
        if re.match(regex, location_code) is not None:
            # TODO: remove dependency on code property in DFE
            code = location_code
            url = s3_url
    # original implementation of this code returned an array of multiple codes
    # which the front end would then filter through. We now only return one,
    # correct location, but it has to be in an array due to original contract.
    location_info = {'code': code, 'label': label}
    if 'url' in fields:
        location_info['url'] = url
    return [location_info]
