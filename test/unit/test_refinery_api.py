from lib.refinery_api import RefineryApi
from test.unit.test_helpers import TestHelpers

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
        today = 'Sun'
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
