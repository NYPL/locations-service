import os
from lib.logger import GlobalLogger


class TestHelpers:
    ENV_VARS = {
        'AWS_REGION': 'test_aws_region',
        'AWS_ACCESS_KEY_ID': 'test_aws_key_id',
        'AWS_SECRET_ACCESS_KEY': 'test_aws_secret_key',
        'NYPL_CORE_OBJECTS_BASE_URL': 'https://example.com/',
        'S3_BUCKET': 'bucket',
        'S3_LOCATIONS_FILE': 'file',
        'REFINERY_API_BASE_URL': 'https://refineryapi.net/',
        'DRUPAL_API_BASE_URL': 'https://drupalapi.net/',
        'RC_ALERTS_URL': 'https://www.fake_rc_alerts.com'
    }

    @classmethod
    def set_env_vars(cls):
        for key, value in cls.ENV_VARS.items():
            os.environ[key] = value

    @classmethod
    def clear_env_vars(cls):
        for key in cls.ENV_VARS.keys():
            if key in os.environ:
                del os.environ[key]

    @classmethod
    def set_up(cls):
        GlobalLogger.initialize_logger(__name__)

    @classmethod
    def tear_down(cls):
        GlobalLogger.logger = None
