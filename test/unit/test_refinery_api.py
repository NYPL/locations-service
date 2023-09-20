import datetime
import json
import os
from unittest.mock import patch

from lib.refinery_api import build_timestamp, get_refinery_data,\
    fetch_location_data, build_hours_array, apply_alerts
from test.unit.test_helpers import TestHelpers
from test.data.refinery_responses.closures import \
    extended_closure_long, early_closure, delayed_opening, extended_closure_into_late_opening, extended_closure_short, temp_closure_overlapping


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
     "startTime": '2000-01-03T10:00:00-05:00',
     "endTime": '2000-01-03T18:00:00-05:00'},
    {"day": 'Tuesday',
     "startTime": '2000-01-04T10:00:00-05:00',
     "endTime": '2000-01-04T20:00:00-05:00'},
    {"day": 'Wednesday',
     "startTime": '2000-01-05T13:00:00-05:00',
     "endTime": '2000-01-05T17:00:00-05:00'},
    {"day": 'Thursday',
     "startTime": '2000-01-06T10:00:00-05:00',
     "endTime": '2000-01-06T18:00:00-05:00'},
    {"day": 'Friday',
     "startTime": '2000-01-07T10:00:00-05:00',
     "endTime": '2000-01-07T20:00:00-05:00'},
    {"day": 'Saturday',
     "startTime": '2000-01-01T10:00:00-05:00',
     "endTime": '2000-01-01T20:00:00-05:00',
     "today": True},
    {"day": 'Sunday',
     "startTime": '2000-01-02T13:00:00-05:00',
     "endTime": '2000-01-02T17:00:00-05:00',
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
        with open(f'test/data/refinery_responses/{location}.json',
                  'r') as file:
            return json.load(file)

    def test_build_timestamp(self):
        assert (build_timestamp(
            '10:00', datetime.datetime(2000, 1, 1, 7).astimezone())) == \
            '2000-01-01T10:00:00-05:00'
        assert (build_timestamp(
            '7:00', datetime.datetime(2000, 1, 1, 1).astimezone())) == \
            '2000-01-01T07:00:00-05:00'

    def test_build_hours_array(self):
        assert build_hours_array(
            DAYS, datetime.datetime(2000, 1, 1).astimezone()) == \
            PARSED_HOURS_ARRAY

    def test_fetch_location_data(self, requests_mock):
        requests_mock.get(os.environ['REFINERY_API_BASE_URL'] + 'schomburg',
                          json=TestRefineryApi.fetch_data_success('schomburg'))
        data = fetch_location_data('schomburg')
        data = fetch_location_data('schomburg')
        assert type(data['updated_at']) is datetime.datetime
        assert type(data['location_data']) is dict
        # RefineryApi client returns cached values upon second request
        assert requests_mock.call_count == 1

    def test_get_refinery_data_address_and_hours(self, requests_mock):
        with patch('lib.refinery_api.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = \
                datetime.datetime(2000, 1, 1)
            mock_datetime.timedelta.side_effect = \
                lambda days: datetime.timedelta(days=days)
            mock_datetime.datetime.astimezone.return_value = \
                datetime.datetime(2000, 1, 1).astimezone()
            requests_mock.get(os.environ['REFINERY_API_BASE_URL'] +
                              'schwarzman',
                              json=TestRefineryApi
                              .fetch_data_success('schwarzman'))
            data = get_refinery_data(
                'mal82', ['location', 'hours'])
            assert data.get('hours') == \
                [{'day': 'Monday', 'startTime': '2000-01-03T10:00:00-05:00',
                    'endTime': '2000-01-03T18:00:00-05:00'},
                 {'day': 'Tuesday', 'startTime': '2000-01-04T10:00:00-05:00',
                    'endTime': '2000-01-04T20:00:00-05:00'},
                 {'day': 'Wednesday', 'startTime': '2000-01-05T10:00:00-05:00',
                    'endTime': '2000-01-05T20:00:00-05:00'},
                 {'day': 'Thursday', 'startTime': '2000-01-06T10:00:00-05:00',
                    'endTime': '2000-01-06T18:00:00-05:00'},
                 {'day': 'Friday', 'startTime': '2000-01-07T10:00:00-05:00',
                    'endTime': '2000-01-07T18:00:00-05:00'},
                 {'day': 'Saturday', 'startTime': '2000-01-01T10:00:00-05:00',
                    'endTime': '2000-01-01T18:00:00-05:00', 'today': True},
                 {'day': 'Sunday', 'startTime': None, 'endTime': None,
                 'nextBusinessDay': True}]

            assert data.get('location') == \
                {'city': 'New York',
                 'line1': 'Fifth Avenue and 42nd Street',
                 'postal_code': '10018',
                 'state': 'NY'}

            get_refinery_data('mal82', ['location', 'hours'])
            # cached data was accessed so only 1 api call
            assert requests_mock.call_count == 1

    def test_get_refinery_data_invalidate_cache(self, requests_mock):
        requests_mock.get(
            os.environ['REFINERY_API_BASE_URL'] + 'lpa',
            json=TestRefineryApi.fetch_data_success('lpa'))
        with patch('lib.refinery_api.datetime') as mock_datetime:
            mock_datetime.datetime.now.side_effect = \
                [datetime.datetime(2000, 1, 1, 10),
                 datetime.datetime(2000, 1, 1, 10),
                 # two hours later so we can check cache invalidation
                 datetime.datetime(2000, 1, 1, 12),
                 datetime.datetime(2000, 1, 1, 12)]
            mock_datetime.timedelta.side_effect = \
                lambda days: datetime.timedelta(days=days)
            get_refinery_data('pal82', ['location'])
            data = get_refinery_data('pal82', ['location'])
            assert data.get('location') == \
                {'city': 'New York',
                 'line1': '40 Lincoln Center Plaza (entrance at 111 Amsterdam \
between 64th and 65th)',
                 'postal_code': '10023',
                 'state': 'NY'}
            # cache was invalidated so two api calls should be made
            assert requests_mock.call_count == 2

    def test_refinery_data_invalid_location(self):
        assert get_refinery_data('xxx', ['location']) is None

    def test_apply_alerts_extended_closure_one_day(self):
        alerts_added_days = apply_alerts(
            PARSED_HOURS_ARRAY, extended_closure_short)
        for day in alerts_added_days:
            # Thursday should be entirely closed
            if day['day'] == 'Thursday':
                assert day['startTime'] is day['endTime'] is None
            else:
                parsed_day = [pday for pday in PARSED_HOURS_ARRAY
                              if pday['day'] == day['day']][0]
                # The rest of the days should be unchanged
                assert day['startTime'] == parsed_day['startTime']
    # def test_apply_alerts_extended_closure_whole_week(self):

    # def test_apply_alerts_early_closing(self):

    # def test_apply_alerts_late_opening(self):
