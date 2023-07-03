import os
import json
import re

from nypl_py_utils.classes.s3_client import S3Client
from nypl_py_utils.functions.config_helper import load_env_file

from lib.logger import GlobalLogger
from errors import MissingEnvVar, ParamError
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
    if method != 'GET':
        return create_response(501, 'LocationsService only implements GET \
endpoints')
    if path == '/docs/locations':
        load_swagger_docs()
    elif re.match(r'\S+/locations', path) is not None:
        try:
            locations_data = fetch_locations(params, CACHE['s3_locations'])
            return create_response(200, locations_data)
        except ParamError:
            return create_response(500,
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

