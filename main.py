import os
import json
import re

from nypl_py_utils.functions.config_helper import load_env_file

from lib.logger import GlobalLogger
from lib.errors import ParamError
from lib.location_lookup import fetch_locations


GlobalLogger.initialize_logger(__name__)
logger = GlobalLogger.logger


def handler(event, context):
    load_env_file(os.environ['ENVIRONMENT'], 'config/{}.yaml')
    method = event.get('httpMethod')
    if method != 'GET':
        return create_response(501, 'LocationsService only implements GET \
            endpoints')
    path = event.get('path')
    if path == '/docs/locations':
        return load_swagger_docs()
    elif re.match(r'\S+/locations', path) is None:
        return create_response(404, f"Path {path} not found")
    else:
        try:
            params = event.get('queryStringParameters')
            (location_codes, fields) = parse_params(params)
            locations_data = fetch_locations(
                location_codes, fields)
            return create_response(200, locations_data)
        except ParamError:
            return create_response(400,
                                   'No location codes provided')
        except Exception as e:
            logger.warn(f'Received error in fetch_locations_and_respond. \
                            Message: {e.message}')
            return create_response(500,
                                   'Failed to fetch locations by code.')


def create_response(status_code=200, body=None):
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'isBase64Encoded': False,
        'headers': {'Content-type': 'application/json'}
    }


def parse_params(params):
    try:
        fields = params.get('fields')
        if fields is None or len(fields) == 0:
            # default to return url if no fields specified
            fields = ['url']
        else:
            # otherwise, return provided fields
            fields = fields.split(',')
        location_codes = params.get('location_codes')
        location_codes = location_codes.split(',')
        return (location_codes, fields)
    except Exception:
        raise ParamError


def load_swagger_docs():
    try:
        with open('./swagger.json') as swagger_file:
            swagger_json = json.load(swagger_file)
            return create_response(200, swagger_json)
    except json.JSONDecodeError as e:
        logger.error('Failed to parse Swagger documentation')
        logger.debug(e.message)
        create_response(500, 'Unable to load Swagger docs from JSON')
    except IOError as e:
        logger.error('Unable to load swagger documentation from file')
        logger.debug(e.message)
        create_response(500, 'Unable to load Swagger docs from JSON')
