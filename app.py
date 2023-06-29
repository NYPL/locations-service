import json
import re

from lib.logger import GlobalLogger
import lib.nypl_core
from errors import ParamError

GlobalLogger.initialize_logger(__name__)
logger = GlobalLogger.logger

# def handler(event, context):
#     path = event.get('path')
#     method = event.get('method')
#     params = event.get('queryStringParameters')

#     if method != 'GET':
#         return create_response(501, 'LocationsService only implements GET \
#             endpoints')
#     if path == '/docs/locations':
#         load_swagger_docs()
#     elif re.match('\S+/locations/', path) is not None:
#         fetch_locations_and_respond(params)
#     else:
#         create_response(404, "#{path} not found")
