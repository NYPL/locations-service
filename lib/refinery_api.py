import requests
from requests.exceptions import JSONDecodeError, RequestException
from datetime import datetime


class RefineryApi:
    locations = ['schwarzman', 'lpa', 'schomburg']
    BASE_URL = "https://refinery.nypl.org/api/nypl/locations/v1.0/locations/"
    locations_cache = {}
    # this order is based on python's datetime.weekday() which returns 0 for 
    #   Monday and 6 for Sunday:
    days_of_the_week = ['Monday' ,'Tuesday' ,'Wednesday' ,'Thursday' 'Friday' ,'Saturday', 'Sunday']

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
        self.locations_cache['updated_at'] = datetime.today()

    def parse_address(self, data):
        parsed_data = {}
        parsed_data['line1'] = data.get('street_address')
        parsed_data['city'] = data.get('locality')
        parsed_data['state'] = data.get('region')
        parsed_data['postal_code'] = data.get('postal_code')
        return parsed_data

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

    @staticmethod
    def determine_location(code):
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

    # expects time - a string representing a 24hr clock time, and day - a 
    # datetime object. Returns a new datetime object with the same date and
    # a new time attached
    @staticmethod
    def build_timestamp(time, day):
        # extract 12 from '12:00'
        hour = int(time.split(':')[0])
        return day.replace(hour=hour)

    # start_time and end_time are strings representing 24 hour times: '10:00'
    # day is a datetime object
    # index is an integer
    @staticmethod
    def build_hours_hash(self, start_time, end_time, day, index):
        hours = {
            'day': self.days_of_the_week[day.weekday()],
            'startTime': RefineryApi.build_timestamp(start_time, day),
            'endTime': RefineryApi.build_timestamp(end_time, day)
        }
        hours['today'] = index == 0
        hours['nextBusinessDay'] = index == 1

    @staticmethod
    def build_hours_array(days_array, current_day):
        today_weekday = current_day.weekday()


class RefineryApiError(Exception):
    def __init__(self, message=None):
        self.message = message
