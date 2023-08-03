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
        return day.slice(0 ,-1) + 'day'

    def attach_data(self, code, fields):
        data = {}
        location = self.determine_location(code)
        if 'address' in fields:
            data['address'] = self.locations_cache[location]['address']
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


class RefineryApiError(Exception):
    def __init__(self, message=None):
        self.message = message


refinery = RefineryApi()
refinery.refresh_refinery_data()
print(refinery.attach_data('sc', ['address']))
