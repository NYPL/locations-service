import json
import os
import pytest
from unittest.mock import patch

from main import parse_params, load_swagger_docs, handler
from test.unit.test_helpers import TestHelpers
from lib.errors import ParamError


class TestMain:
    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()
        TestHelpers.set_up()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()
        TestHelpers.tear_down()

    def test_parse_params(self):
        params = {'fields': 'url,hours,location', "location_codes": 'abc'}
        assert parse_params(params) == (['abc'], ['url', 'hours', 'location'])
        params = {'fields': 'hours,location', "location_codes": 'abc'}
        assert parse_params(params) == (['abc'], ['hours', 'location'])
        params = {"location_codes": 'abc'}
        assert parse_params(params) == (['abc'], ['url'])

    def test_parse_param_error(self):
        with pytest.raises(ParamError):
            parse_params(None)
        with pytest.raises(ParamError):
            parse_params({'fields': 'abc'})
        with pytest.raises(ParamError):
            parse_params({'fields': 'abc', 'location_codes': None})

    def test_load_swagger_docs(self):
        swagger_response = load_swagger_docs()
        assert swagger_response['statusCode'] == 200
        assert json.loads(swagger_response['body'])['swagger'] == \
            '2.0'

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label'})
    def test_handler(self, MockNyplCore):
        TestHelpers.clear_env_vars()
        os.environ['ENVIRONMENT'] = 'qa'
        assert handler({
            'path': 'spaghetti',
            'httpMethod': 'GET',
            'queryStringParameters': None}, {}).get('statusCode') == 404
        assert handler({
            'path': 'api/locations',
            'httpMethod': 'GET',
            'queryStringParameters': {'location_codes': None}}, {}) \
            .get('statusCode') == 400
