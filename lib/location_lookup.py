import re

import lib.nypl_core
from lib.logger import GlobalLogger
from lib.errors import ParamError


def parse_params(params):
    location_codes = params.get('location_codes')
    if location_codes is None or location_codes == '':
        raise ParamError()
    fields = params.get('fields', '').split(',')
    return {
        'location_codes': location_codes.split(','),
        'hours': 'hours' in fields,
        'location': 'location' in fields,
        # default with no fields provided is url = True
        'url': 'url' in fields or len(fields) == 0,
    }


def load_swagger_docs():
    return 'swag'


def fetch_locations(params, s3_locations):
    params = parse_params(params)
    get_url = True
    location_codes = params.get('location_codes')
    location_dict = {}
    for code in location_codes:
        location_dict[code] = build_location_info(get_url, code, s3_locations)
    return location_dict


# returns s3 location code, location url, and location label for a
# given sierra location code
def build_location_info(get_url, location_code, s3_locations):
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
    for s3_code, s3_url in s3_locations.items():
        # turn xxx* into ^(xxx)+
        regex = r'^(' + s3_code[0:-1] + ')+'
        if re.match(regex, location_code) is not None:
            # TODO: remove dependency on code property in DFE
            code = s3_code
            url = s3_url
    # original implementation of this code returned an array of multiple
    # which the front end would then filter through. We now only return one,
    # correct location, but it has to be in an array due to original contract.
    location_info = {'code': code, 'label': label}
    if get_url:
        location_info['url'] = url
    return [location_info]
