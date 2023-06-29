import json
import re


import lib.nypl_core
from errors import ParamError


s3_locations = None
initialized = False
s3_client = None


def parse_params(params):
    location_codes = params.get('location_codes')
    if location_codes is None:
        raise ParamError()
    fields = params.get('fields', '').split(',')
    return {
        'location_codes': location_codes,
        'hours': 'hours' in fields,
        'location': 'location' in fields,
        # default with no fields provided is url = True
        'url': 'url' in fields or len(fields) == 0,
    }


def load_swagger_docs():
    return 'swag'


def fetch_locations_and_respond(params):
    return 'locations'


# returns s3 location code, location url, and location label for a 
# given sierra location code
def build_location_info(url_query, location_code, s3_locations):
    nypl_core_location_data = (lib.nypl_core
                                  .sierra_location_by_code(location_code))
    label = nypl_core_location_data.get('label')
    url = None
    code = None
    for s3_code, s3_url in s3_locations.items():
        if re.match(r'^'+s3_code, location_code) is not None:
            # TODO: remove dependency on code property in DFE
            code = s3_code
            url = s3_url
    location_info = {'code': code, 'label': label}
    if url_query:
        location_info['url'] = url
    return location_info


def create_response(status_code=200, body=None):
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'isBase64Encoded': False,
        'headers': {'Content-type': 'application/json'}
    }
