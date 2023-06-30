from lib.location_lookup import parse_params, build_location_info,\
                                fetch_locations_and_respond
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
        assert build_location_info(True,
                                   'lol99',
                                   s3_locations) \
            == [{'code': 'lo*', 'url': 'url.com', 'label': 'label'}]
        assert build_location_info(False,
                                   'lol99',
                                   s3_locations) \
            == [{'code': 'lo*', 'label': 'label'}]

    def test_parse_params(self):
        assert parse_params({'fields': 'location,hours,url',
                           'location_codes': 'ma,sc,my'}) == \
            {'location': True,
             'hours': True,
             'url': True,
             'location_codes': ['ma', 'sc', 'my']}
        assert parse_params({'fields': 'location,url',
                           'location_codes': 'ma,sc,my'}) == \
            {'location': True,
             'hours': False,
             'url': True,
             'location_codes': ['ma', 'sc', 'my']}
        assert parse_params({'fields': 'location',
                           'location_codes': 'ma,sc,my'}) == \
            {'location': True,
             'hours': False,
             'url': False,
             'location_codes': ['ma', 'sc', 'my']}
        assert parse_params({'location_codes': 'ma,sc,my'}) == \
            {'location': False,
             'hours': False,
             'url': False,
             'location_codes': ['ma', 'sc', 'my']}

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={})
    def test_fetch_locations_and_respond_no_label(self, MockNyplCore):
        params = {'fields': 'location,hours,url',
                            'location_codes': 'mab,sco,myq'}
        assert fetch_locations_and_respond(params, s3_locations) == \
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

