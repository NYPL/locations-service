from lib.location_lookup import build_location_info, fetch_locations
from test.unit.test_helpers import TestHelpers

from unittest.mock import patch

s3_locations = {'lo*': 'url.com',
                'xo*': 'url.com',
                'ma*': 'sasb.com',
                'sc*': 'schom.com',
                'my*': 'lpa.com'}

refinery_data = {
    'hours': 'some hours',
    'location': 'a location'
}


class TestLocationLogic:
    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()
        TestHelpers.set_up()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()
        TestHelpers.tear_down()

    @patch('lib.location_lookup.get_refinery_data', return_value=refinery_data)
    @patch('lib.location_lookup.check_cache_or_fetch_s3',
           return_value=s3_locations)
    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label'})
    def test_build_location_info(self, MockNyplCore, MockS3, MockRefinery):
        assert build_location_info('lol99', ['url']) \
            == [{'code': 'lol99', 'label': 'label', 'url': 'url.com'}]
        assert build_location_info('lol99', ['hours']) \
            == [{'code': 'lol99', 'label': 'label', 'hours': 'some hours'}]
        # ensure xma99 does not match ma
        assert build_location_info('xma99', ['location']) \
            == [{'code': None, 'label': 'label', 'location': 'a location'}]

    @patch('lib.location_lookup.get_refinery_data', return_value=refinery_data)
    @patch('lib.location_lookup.check_cache_or_fetch_s3',
           return_value=s3_locations)
    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={})
    def test_fetch_locations_no_label(self, MockNyplCore, MockS3,
                                      MockRefinery):
        fields = ['location', 'hours', 'url']
        location_codes = ['mab', 'sco', 'myq']
        assert fetch_locations(location_codes, fields) == \
            {
                'mab': [{
                    'hours': 'some hours',
                    'location': 'a location',
                    'code': 'mab',
                    'url': 'sasb.com',
                    'label': None
                }],
                'sco': [{
                    'hours': 'some hours',
                    'location': 'a location',
                    'code': 'sco',
                    'url': 'schom.com',
                    'label': None
                }],
                'myq': [{
                    'hours': 'some hours',
                    'location': 'a location',
                    'code': 'myq',
                    'url': 'lpa.com',
                    'label': None
                }]
        }

    @patch('lib.location_lookup.get_refinery_data', return_value=refinery_data)
    @patch('lib.location_lookup.check_cache_or_fetch_s3',
           return_value=s3_locations)
    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label'})
    def test_fetch_locations(self, MockNyplCore, MockS3, MockRefinery):
        fields = ['location', 'hours', 'url']
        location_codes = ['mab', 'sco', 'myq']
        assert fetch_locations(location_codes, fields) == \
            {
                'mab': [{
                    'hours': 'some hours',
                    'location': 'a location',
                    'code': 'mab',
                    'url': 'sasb.com',
                    'label': 'label'
                }],
                'sco': [{
                    'hours': 'some hours',
                    'location': 'a location',
                    'code': 'sco',
                    'url': 'schom.com',
                    'label': 'label'
                }],
                'myq': [{
                    'hours': 'some hours',
                    'location': 'a location',
                    'code': 'myq',
                    'url': 'lpa.com',
                    'label': 'label'
                }]
        }

    @patch('lib.location_lookup.get_refinery_data', return_value=refinery_data)
    @patch('lib.location_lookup.check_cache_or_fetch_s3',
           return_value=s3_locations)
    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label anyway'})
    def test_fetch_locations_code_not_in_s3(self, MockNyplCore, MockS3,
                                            MockRefinery):
        fields = ['url']
        location_codes = ['xxx']
        assert fetch_locations(location_codes, fields) == \
            {
                'xxx': [{
                    'code': None,
                    'url': None,
                    'label': 'label anyway'
                }]
        }
