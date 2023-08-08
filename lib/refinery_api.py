import requests
from requests.exceptions import JSONDecodeError, RequestException
import time


class RefineryApi:
    locations = ['schwarzman', 'lpa', 'schomburg']
    BASE_URL = "https://refinery.nypl.org/api/nypl/locations/v1.0/locations/"
    locations_cache = {}

    def refresh_refinery_data(self):
        for location in self.locations:
            self.locations_cache[location] = {}
        for location in self.locations:
            response = None
            try:
                response = requests.get(self.BASE_URL + location)
                response.raise_for_status()
            except RequestException as e:
                raise RefineryApiError(
                    f'Failed to retrieve Refinery API location data \
                    for {location}: {e}')
            try:
                response = response.json()
                self.locations_cache[location]['address'] = self.parse_address(response.get('location'))
                # self.locations_cache[location]['hours'] = self.parse_hours(response.get('location').get(''))
            except (JSONDecodeError, KeyError) as e:
                raise RefineryApiError(
                    f'Failed to parse Refinery API response: \
                        {type(e)} {e}')
        self.locations_cache['updated_at'] = time.time()

    def parse_address(self, data):
        parsed_data = {}
        parsed_data['line1'] = data.get('street_address')
        parsed_data['city'] = data.get('locality')
        parsed_data['state'] = data.get('region')
        parsed_data['postal_code'] = data.get('postal_code')
        return parsed_data

    def expand_day(self, day):
        return day.slice(0, -1) + 'day'

    # given an array of fields and a location code, return an dict populated
    # by those fields for that location code.
    def attach_data(self, code, fields):
        data = {}
        location = self.determine_location(code)
        if 'address' in fields:
            data['address'] = self.locations_cache.get(location).get('address')
        if 'hours' in fields:
            data['hours'] = self.locations_cache.get(location).get('hours').get('regular')
        return data

    def determine_location(self, code):
        location = ''
        if code.startswith('ma'):
            location = 'schwarzman'
        if code.startswith('sc'):
            location = 'schomburg'
        if code.startswith('pa'):
            location = 'lpa'
        return location

    # Expects an array of hashes representing open days of the branch. And a
    # 3 letter day string trimmed from a time.asctime return value.
    # Returns an array of those days in order, rearranged to start with today
    @staticmethod
    def arrange_days(days_array, today):
        # day is returned from refinery api as 'Mon.', eg
        
        index_of_today = [day.get('day')[:-1] for day in days_array].index(today)

        if index_of_today == 0:
            return days_array
        else:
            # reorder day objects so today is first in the array
            return days_array[index_of_today:] + days_array[0:index_of_today]


class RefineryApiError(Exception):
    def __init__(self, message=None):
        self.message = message


RefineryApi.arrange_days([
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
    }], "Wed")
