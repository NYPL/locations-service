import logic_module as logic_module
from unittest.mock import patch


class TestLogic:

    @patch('lib.nypl_core.sierra_location_by_code',
           return_value={'label': 'label'})
    def test_build_location_info(self, MockNyplCore):
        assert logic_module \
            .build_location_info(True,
                                 'lol99',
                                 {'lo*': 'url.com', 'xo*': 'url.com'}) \
            == {'code': 'lo*', 'url': 'url.com', 'label': 'label'}
        assert logic_module \
            .build_location_info(False,
                                 'lol99',
                                 {'lo*': 'url.com', 'xo*': 'url.com'}) \
            == {'code': 'lo*', 'label': 'label'}

    def test_parse_params(self):
        assert logic_module \
            .parse_params({'fields': 'location,hours,url',
                           'location_codes': 'ma,sc,my'}) == \
            {'location': True,
             'hours': True,
             'url': True,
             'location_codes': 'ma,sc,my'}
        assert logic_module \
            .parse_params({'fields': 'location,url',
                           'location_codes': 'ma,sc,my'}) == \
            {'location': True,
             'hours': False,
             'url': True,
             'location_codes': 'ma,sc,my'}
        assert logic_module \
            .parse_params({'fields': 'location',
                           'location_codes': 'ma,sc,my'}) == \
            {'location': True,
             'hours': False,
             'url': False,
             'location_codes': 'ma,sc,my'}
        assert logic_module \
            .parse_params({'location_codes': 'ma,sc,my'}) == \
            {'location': False,
             'hours': False,
             'url': False,
             'location_codes': 'ma,sc,my'}
