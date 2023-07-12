import os
import json
import re

from nypl_py_utils.classes.s3_client import S3Client
from nypl_py_utils.functions.config_helper import load_env_file

from lib.logger import GlobalLogger
from lib.errors import MissingEnvVar, ParamError
from lib.location_lookup import fetch_locations, load_swagger_docs


GlobalLogger.initialize_logger(__name__)
logger = GlobalLogger.logger

CACHE = {}


def handler(event, context):
    load_env_file(os.environ['ENVIRONMENT'], 'config/{}.yaml')
    init()
    path = event.get('path')
    method = event.get('httpMethod')
    params = event.get('queryStringParameters')
    (location_codes, fields) = parse_params(params)
    if method != 'GET':
        return create_response(501, 'LocationsService only implements GET \
endpoints')
    if path == '/docs/locations':
        load_swagger_docs()
    elif re.match(r'\S+/locations', path) is not None:
        try:
            locations_data = fetch_locations(
                location_codes, fields, CACHE['s3_locations'])
            return create_response(200, locations_data)
        except ParamError:
            return create_response(400,
                                   'No location codes provided')
        except Exception as e:
            logger.warn(f'Received error in fetch_locations_and_respond. \
Message: {e.message}')
            return create_response(500,
                                   'Failed to fetch locations by code.')
    else:
        return create_response(404, "#{path} not found")


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


def create_response(status_code=200, body=None):
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'isBase64Encoded': False,
        'headers': {'Content-type': 'application/json'}
    }


def parse_params(params):
    fields = params.get('fields')
    if fields is None or len(fields) == 0:
        # default to return url if no fields specified
        fields = ['url']
    else:
        # otherwise, return provided fields
        fields = fields.split(',')
    location_codes = params.get('location_codes')
    if location_codes is None or location_codes == '':
        raise ParamError()
    else:
        location_codes = location_codes.split(',')
    return (location_codes, fields)
