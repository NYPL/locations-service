from lib.refinery_api import RefineryApi
from test.unit.test_helpers import TestHelpers

import datetime

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


class TestMain:
    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()
        TestHelpers.set_up()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()
        TestHelpers.tear_down()

    def test_arrange_data_today_first(self):
        today = datetime.datetime(2000, 1, 1, 7)
        assert RefineryApi.arrange_days(DAYS, today) == DAYS

    def test_arrange_data_today_is_wednesday(self):
        today = 'Wed'
        arranged = RefineryApi.arrange_days(DAYS, today)
        assert [day.get('day') for day in arranged] == [
            "Wed.",
            "Thu.",
            "Fri.",
            "Sat.",
            "Sun.",
            "Mon.",
            "Tue."]

    def test_build_timestamp(self):
        assert (RefineryApi.build_timestamp(
            '10:00', datetime.datetime(2000, 1, 1, 7))) == \
            datetime.datetime(2000, 1, 1, 10)
        assert (RefineryApi.build_timestamp(
            '7:00', datetime.datetime(2000, 1, 1, 1))) == \
            datetime.datetime(2000, 1, 1, 7)

    def test_build_hours_array(self):
        assert RefineryApi.build_hours_array(
            DAYS, datetime.datetime(2000, 1, 1)) == \
            [
            {"day": 'Thursday', "startTime": '2023-06-01T10:00:00+00:00',
             "endTime": '2023-06-01T18:00:00+00:00', "today": True},
            {"day": 'Friday', "startTime": '2023-06-02T10:00:00+00:00',
             "endTime": '2023-06-02T18:00:00+00:00', "nextBusinessDay": True},
            {"day": 'Saturday', "startTime": '2023-06-03T10:00:00+00:00',
             "endTime": '2023-06-03T18:00:00+00:00'},
            {"day": 'Sunday', "startTime": '2023-06-04T13:00:00+00:00',
             "endTime": '2023-06-04T17:00:00+00:00'},
            {"day": 'Monday', "startTime": '2023-06-05T10:00:00+00:00',
             "endTime": '2023-06-05T18:00:00+00:00'},
            {"day": 'Tuesday', "startTime": '2023-06-06T10:00:00+00:00',
             "endTime": '2023-06-06T20:00:00+00:00'},
            {"day": 'Wednesday', "startTime": '2023-06-07T10:00:00+00:00',
             "endTime": '2023-06-07T20:00:00+00:00'}
        ]
