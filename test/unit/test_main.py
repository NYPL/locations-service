import json

from main import parse_params, load_swagger_docs
from test.unit.test_helpers import TestHelpers


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
        params = {'fields': 'url,hours,address', "location_codes": 'abc'}
        assert parse_params(params) == (['abc'], ['url', 'hours', 'address'])
        params = {'fields': 'hours,address', "location_codes": 'abc'}
        assert parse_params(params) == (['abc'], ['hours', 'address'])
        params = {"location_codes": 'abc'}
        assert parse_params(params) == (['abc'], ['url'])

    def test_load_swagger_docs(self):
        swagger_response = load_swagger_docs()
        assert swagger_response['statusCode'] == 200
        assert json.loads(swagger_response['body'])['swagger'] == \
            '2.0'
