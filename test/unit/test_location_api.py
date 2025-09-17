from datetime import datetime, timedelta
import json
import os
from freezegun import freeze_time

from lib.location_api import parse_hours, parse_address, get_location_data
from test.unit.test_helpers import TestHelpers


class TestLocationApi:

    def timedelta_side_effect(day_offset):
        return timedelta(days=day_offset)

    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()
        TestHelpers.set_up()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()
        TestHelpers.tear_down()

    def fetch_data_success(code):
        with open(f'test/data/drupal_responses/{code}.json',
                  'r') as file:
            return json.load(file)

    def test_parse_hours(self):
        monday = {
            "day": "Monday",
            "hours": "10 AM–6 PM"
        }
        current_date = datetime(2000, 1, 1).astimezone()  # this is a saturday
        parsed = parse_hours(current_date, monday)
        assert parsed['day'] == 'Monday'
        assert parsed['startTime'] == '2000-01-03T10:00:00-05:00'
        assert parsed['endTime'] == '2000-01-03T18:00:00-05:00'

    def test_parse_hours_with_minutes(self):
        monday = {
            "day": "Monday",
            "hours": "10:23 AM–6:17 PM"
        }
        current_date = datetime(2000, 1, 1).astimezone()  # this is a saturday
        parsed = parse_hours(current_date, monday)
        assert parsed['day'] == 'Monday'
        assert parsed['startTime'] == '2000-01-03T10:23:00-05:00'
        assert parsed['endTime'] == '2000-01-03T18:17:00-05:00'


    def test_parse_hours_today(self):
        day = {
            "day": "Saturday",
            "hours": "10 AM–6 PM"
        }
        current_date = datetime(2000, 1, 1).astimezone()  # this is a saturday
        parsed = parse_hours(current_date, day)
        assert parsed['day'] == 'Saturday'
        assert parsed['startTime'] == '2000-01-01T10:00:00-05:00'
        assert parsed['endTime'] == '2000-01-01T18:00:00-05:00'
        assert parsed['today']

    def test_parse_hours_midnight(self):
        day = {
            "day": "Saturday",
            "hours": "12 AM–12 PM"
        }
        current_date = datetime(2000, 1, 1).astimezone()  # this is a saturday
        parsed = parse_hours(current_date, day)
        assert parsed['day'] == 'Saturday'
        assert parsed['startTime'] == '2000-01-01T00:00:00-05:00'
        assert parsed['endTime'] == '2000-01-01T12:00:00-05:00'
        assert parsed['today']

    def test_parse_hours_noon(self):
        day = {
            "day": "Saturday",
            "hours": "12 PM–8 PM"
        }
        current_date = datetime(2000, 1, 1).astimezone()  # this is a saturday
        parsed = parse_hours(current_date, day)
        assert parsed['day'] == 'Saturday'
        assert parsed['startTime'] == '2000-01-01T12:00:00-05:00'
        assert parsed['endTime'] == '2000-01-01T20:00:00-05:00'
        assert parsed['today']

    def test_parse_address(self):
        address_data = {
            "langcode": "en",
            "country_code": "US",
            "administrative_area": "NY",
            "locality": "New York",
            "postal_code": "10018",
            "address_line1": "Fifth Avenue and 42nd Street",
            "address_line3": ""
        }
        parsed = parse_address(address_data)
        assert parsed['line1'] == "Fifth Avenue and 42nd Street"
        assert parsed['city'] == 'New York'
        assert parsed['state'] == 'NY'
        assert parsed['postal_code'] == '10018'

    @freeze_time(datetime(2000, 1, 1))
    def test_get_location_data_special_hours(self, requests_mock):
        requests_mock.get(os.environ['DRUPAL_API_BASE_URL'] + '?filter[field_ts_location_code]=ma',
                          json=TestLocationApi.fetch_data_success('ma'))
        location_data = get_location_data('ma', ['hours', 'location'])
        correct_today = False
        correct_next_business_day = False
        for hours in location_data.get('hours'):
            if hours['day'] == 'Saturday' and hours['today']:
                correct_today = True
            if hours['day'] == 'Tuesday' and hours['nextBusinessDay']:
                # test day is closed on sunday and monday so it wraps to tuesday
                correct_next_business_day = True
        assert correct_today
        assert correct_next_business_day

    @freeze_time(datetime(2000, 1, 1))
    def test_get_location_data_regular_hours(self, requests_mock):
        requests_mock.get(os.environ['DRUPAL_API_BASE_URL'] + '?filter[field_ts_location_code]=ma',
                          json=TestLocationApi.fetch_data_success('ma_regular_hours'))
        location_data = get_location_data('ma', ['hours', 'location'])
        correct_today = False
        correct_next_business_day = False
        for hours in location_data.get('hours'):
            if hours['day'] == 'Saturday' and hours['today']:
                correct_today = True
            if hours['day'] == 'Monday' and hours['nextBusinessDay']:
                # test day is closed on sunday so it wraps to monday
                correct_next_business_day = True
        assert correct_today
        assert correct_next_business_day
