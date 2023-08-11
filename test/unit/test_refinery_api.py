from lib.refinery_api import RefineryApi, requests
from test.unit.test_helpers import TestHelpers

import datetime
import json
from unittest.mock import patch


DAYS = [
    {
        "day": "Sun.",
        "open": "13:00",
                "close": "17:00"
    },
    {
        "day": "Mon.",
        "open": "10:00",
                "close": "18:00"
    },
    {
        "day": "Tue.",
        "open": "10:00",
                "close": "20:00"
    },
    {
        "day": "Wed.",
        "open": "13:00",
                "close": "17:00"
    },
    {
        "day": "Thu.",
        "open": "10:00",
                "close": "18:00"
    },
    {
        "day": "Fri.",
        "open": "10:00",
                "close": "20:00"
    },
    {
        "day": "Sat.",
        "open": "10:00",
                "close": "20:00"
    }]

PARSED_HOURS_ARRAY = [
    {"day": 'Monday',
     "startTime": '2000-01-03T10:00:00',
     "endTime": '2000-01-03T18:00:00'},
    {"day": 'Tuesday',
     "startTime": '2000-01-04T10:00:00',
     "endTime": '2000-01-04T20:00:00'},
    {"day": 'Wednesday',
     "startTime": '2000-01-05T13:00:00',
     "endTime": '2000-01-05T17:00:00'},
    {"day": 'Thursday',
     "startTime": '2000-01-06T10:00:00',
     "endTime": '2000-01-06T18:00:00'},
    {"day": 'Friday',
     "startTime": '2000-01-07T10:00:00',
     "endTime": '2000-01-07T20:00:00'},
    {"day": 'Saturday',
     "startTime": '2000-01-01T10:00:00',
     "endTime": '2000-01-01T20:00:00',
     "today": True},
    {"day": 'Sunday',
     "startTime": '2000-01-02T13:00:00',
     "endTime": '2000-01-02T17:00:00',
     "nextBusinessDay": True},
]


class TestRefineryApi:

    def timedelta_side_effect(day_offset):
        return datetime.timedelta(days=day_offset)

    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()
        TestHelpers.set_up()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()
        TestHelpers.tear_down()

    def fetch_data_success(location):
        with open(f'test/unit/refinery_responses_regular/{location}.json',
                  'r') as file:
            return json.load(file)

    def test_build_timestamp(self):
        assert (RefineryApi.build_timestamp(
            '10:00', datetime.datetime(2000, 1, 1, 7))) == \
            '2000-01-01T10:00:00'
        assert (RefineryApi.build_timestamp(
            '7:00', datetime.datetime(2000, 1, 1, 1))) == \
            '2000-01-01T07:00:00'

    def test_build_hours_array(self):
        assert RefineryApi.build_hours_array(
            DAYS, datetime.datetime(2000, 1, 1)) == \
            PARSED_HOURS_ARRAY

    def test_fetch_location_data(self, requests_mock):
        requests_mock.get(RefineryApi.BASE_URL + 'schomburg',
                          json=TestRefineryApi.fetch_data_success('schomburg'))
        data = RefineryApi.fetch_location_data('schomburg')
        data = RefineryApi.fetch_location_data('schomburg')
        assert type(data['updated_at']) is datetime.datetime
        assert type(data['location_data']) is dict
        # RefineryApi client returns cached values upon second request
        assert requests_mock.call_count == 1

    def test_get_refinery_data_address_and_hours(self, requests_mock):
        with patch('lib.refinery_api.datetime') as mock_datetime:
            mock_datetime.datetime.today.return_value = \
                datetime.datetime(2000, 1, 1)
            mock_datetime.timedelta.side_effect = \
                lambda days: datetime.timedelta(days=days)
            requests_mock.get(RefineryApi.BASE_URL + 'schwarzman',
                              json=TestRefineryApi.fetch_data_success('schwarzman'))
            data = RefineryApi.get_refinery_data(
                'mal82', ['address', 'hours'])
            assert data.get('hours') == \
                [{'day': 'Monday', 'startTime': '2000-01-03T10:00:00',
                    'endTime': '2000-01-03T18:00:00'},
                 {'day': 'Tuesday', 'startTime': '2000-01-04T10:00:00',
                    'endTime': '2000-01-04T20:00:00'},
                 {'day': 'Wednesday', 'startTime': '2000-01-05T10:00:00',
                    'endTime': '2000-01-05T20:00:00'},
                 {'day': 'Thursday', 'startTime': '2000-01-06T10:00:00',
                    'endTime': '2000-01-06T18:00:00'},
                 {'day': 'Friday', 'startTime': '2000-01-07T10:00:00',
                    'endTime': '2000-01-07T18:00:00'},
                 {'day': 'Saturday', 'startTime': '2000-01-01T10:00:00',
                    'endTime': '2000-01-01T18:00:00', 'today': True},
                 {'day': 'Sunday', 'startTime': None, 'endTime': None,
                 'nextBusinessDay': True}]

            assert data.get('address') == \
                {'city': 'New York',
                 'line1': 'Fifth Avenue and 42nd Street',
                 'postal_code': '10018',
                 'state': 'NY'}

            RefineryApi.get_refinery_data('mal82', ['address', 'hours'])
            # cached data was accessed so only 1 api call
            assert requests_mock.call_count == 1

    def test_get_refinery_data_invalidate_cache(self, requests_mock):
        requests_mock.get(
            RefineryApi.BASE_URL + 'lpa',
            json=TestRefineryApi.fetch_data_success('lpa'))
        with patch('lib.refinery_api.datetime') as mock_datetime:
            mock_datetime.datetime.today.side_effect = \
                [datetime.datetime(2000, 1, 1, 10),
                 datetime.datetime(2000, 1, 1, 10),
                 # two hours later so we can check cache invalidation
                 datetime.datetime(2000, 1, 1, 12),
                 datetime.datetime(2000, 1, 1, 12)]
            mock_datetime.timedelta.side_effect = \
                lambda days: datetime.timedelta(days=days)
            RefineryApi.get_refinery_data('pal82', ['address'])
            data = RefineryApi.get_refinery_data('pal82', ['address'])
            assert data.get('address') == \
                {'city': 'New York',
                 'line1': '40 Lincoln Center Plaza (entrance at 111 Amsterdam \
between 64th and 65th)',
                 'postal_code': '10023',
                 'state': 'NY'}
            # cache was invalidated so two api calls should be made
            assert requests_mock.call_count == 2
