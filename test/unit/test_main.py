from unittest.mock import patch

from main import init, CACHE, S3Client
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

    def test_init_sets_s3_locations(self):
        with patch.object(S3Client, '__init__', lambda s, b, r: None):
            with patch.object(S3Client, 'fetch_cache', lambda p: 'locations'):
                assert CACHE.get('s3_locations') is None
                init()
                assert CACHE.get('s3_locations') == 'locations'
