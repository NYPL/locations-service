from lib.location_lookup import build_location_info,\
    fetch_locations, init, S3Client, _set_cache, _get_cache
from test.unit.test_helpers import TestHelpers

from unittest.mock import patch
import time

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

    def test_init_uses_cache(self):
        updated = time.time()
        _set_cache('s3_locations', {'code': 'cached data'})
        _set_cache('s3_locations_updated_at', updated)
        init()
        assert _get_cache().get('s3_locations') == {'code': 'cached data'}

    def test_init_resets_cache(self):
        with patch.object(S3Client, '__init__', lambda s, b, r: None):
            with patch.object(S3Client, 'fetch_cache', lambda p:
                              'refreshed data'):
                updated = 1
                _set_cache('s3_locations', {'code': 'cached data'})
                _set_cache('s3_locations_updated_at', updated)
                init()
                assert _get_cache().get('s3_locations') == 'refreshed data'

    def test_init_sets_s3_locations(self):
        with patch.object(S3Client, '__init__', lambda s, b, r: None):
            with patch.object(S3Client, 'fetch_cache', lambda p: s3_locations):
                _set_cache('s3_locations', None)
                assert _get_cache().get('s3_locations') is None
                init()
                assert _get_cache().get('s3_locations') == s3_locations

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label'})
    def test_build_location_info(self, MockNyplCore):
        _set_cache('s3_locations', s3_locations)
        assert build_location_info('lol99', ['url']) \
            == [{'code': 'lol99', 'label': 'label', 'url': 'url.com'}]
        assert build_location_info('lol99', ['hours']) \
            == [{'code': 'lol99', 'label': 'label'}]
        # ensure xma99 does not match ma
        assert build_location_info('xma99', ['hours']) \
            == [{'code': None, 'label': 'label'}]

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={})
    def test_fetch_locations_no_label(self, MockNyplCore):
        fields = ['location', 'hours', 'url']
        location_codes = ['mab', 'sco', 'myq']
        assert fetch_locations(location_codes, fields) == \
            {
                'mab': [{
                    'code': 'mab',
                    'url': 'sasb.com',
                    'label': None
                }],
                'sco': [{
                    'code': 'sco',
                    'url': 'schom.com',
                    'label': None
                }],
                'myq': [{
                    'code': 'myq',
                    'url': 'lpa.com',
                    'label': None
                }]
        }

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label'})
    def test_fetch_locations(self, MockNyplCore):
        fields = ['location', 'hours', 'url']
        location_codes = ['mab', 'sco', 'myq']
        assert fetch_locations(location_codes, fields) == \
            {
                'mab': [{
                    'code': 'mab',
                    'url': 'sasb.com',
                    'label': 'label'
                }],
                'sco': [{
                    'code': 'sco',
                    'url': 'schom.com',
                    'label': 'label'
                }],
                'myq': [{
                    'code': 'myq',
                    'url': 'lpa.com',
                    'label': 'label'
                }]
        }

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label anyway'})
    def test_fetch_locations_code_not_in_s3(self, MockNyplCore):
        fields = ['location', 'hours', 'url']
        location_codes = ['xxx']
        assert fetch_locations(location_codes, fields) == \
            {
                'xxx': [{
                    'code': None,
                    'url': None,
                    'label': 'label anyway'
                }]
        }
