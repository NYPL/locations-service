from lib.location_lookup import build_location_info,\
    fetch_locations
from test.unit.test_helpers import TestHelpers

from unittest.mock import patch

s3_locations = {'lo*': 'url.com',
                'xo*': 'url.com',
                'ma*': 'sasb.com',
                'sc*': 'schom.com',
                'my*': 'lpa.com'}


class TestLogic:
    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()
        TestHelpers.set_up()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()
        TestHelpers.tear_down()

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label'})
    def test_build_location_info(self, MockNyplCore):
        assert build_location_info('lol99', ['url'], s3_locations) \
            == [{'code': 'lo*', 'url': 'url.com', 'label': 'label'}]
        assert build_location_info('lol99', ['hours'], s3_locations) \
            == [{'code': 'lo*', 'label': 'label'}]
        # ensure xma99 does not match ma
        assert build_location_info('xma99', ['hours'], s3_locations) \
            == [{'code': None, 'label': 'label'}]

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={})
    def test_fetch_locations_no_label(self, MockNyplCore):
        fields = ['address', 'hours', 'url']
        location_codes = ['mab', 'sco', 'myq']
        assert fetch_locations(location_codes, fields, s3_locations) == \
            {
                'mab': [{
                    'code': 'ma*',
                    'url': 'sasb.com',
                    'label': None
                }],
                'sco': [{
                    'code': 'sc*',
                    'url': 'schom.com',
                    'label': None
                }],
                'myq': [{
                    'code': 'my*',
                    'url': 'lpa.com',
                    'label': None
                }]
        }

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label'})
    def test_fetch_locations(self, MockNyplCore):
        fields = ['address', 'hours', 'url']
        location_codes = ['mab', 'sco', 'myq']
        assert fetch_locations(location_codes, fields, s3_locations) == \
            {
                'mab': [{
                    'code': 'ma*',
                    'url': 'sasb.com',
                    'label': 'label'
                }],
                'sco': [{
                    'code': 'sc*',
                    'url': 'schom.com',
                    'label': 'label'
                }],
                'myq': [{
                    'code': 'my*',
                    'url': 'lpa.com',
                    'label': 'label'
                }]
        }

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label anyway'})
    def test_fetch_locations_code_not_in_s3(self, MockNyplCore):
        fields = ['address', 'hours', 'url']
        location_codes = ['xxx']
        assert fetch_locations(location_codes, fields, s3_locations) == \
            {
                'xxx': [{
                    'code': None,
                    'url': None,
                    'label': 'label anyway'
                }]
        }
