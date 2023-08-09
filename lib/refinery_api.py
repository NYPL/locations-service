import requests
from requests.exceptions import JSONDecodeError, RequestException
import datetime
from functools import cache


class RefineryApi:
    locations = ['schwarzman', 'lpa', 'schomburg']
    BASE_URL = "https://refinery.nypl.org/api/nypl/locations/v1.0/locations/"
    locations_cache = {}
    # this order is based on python's datetime.weekday() which returns 0 for
    #   Monday and 6 for Sunday:
    days_of_the_week = ['Monday', 'Tuesday', 'Wednesday',
                        'Thursday', 'Friday', ' Saturday', 'Sunday']

    def get_refinery_data(self):
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
                self.locations_cache[location]['address'] = self.parse_address(
                    response.get('location'))
                # self.locations_cache[location]['hours'] = self.parse_hours(response.get('location').get(''))
            except (JSONDecodeError, KeyError) as e:
                raise RefineryApiError(
                    f'Failed to parse Refinery API response: \
                        {type(e)} {e}')
        return {
            'address': self.parse_address(response.get('location')),
            'hours': self.parse_hours(response.get('hours')),
            'updated_at': datetime.datetime.today()
        }

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
            data['hours'] = self.locations_cache.get(
                location).get('hours').get('regular')
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

    # Expects an array of hashes representing open days of the branch and a
    # datetime object returned by datetime.datetime.today()
    # Returns an array of those days in order, rearranged to start with today
    @staticmethod
    def arrange_days(days_array, today):
        days_array_sunday_last = days_array[1:] + days_array[0]
        # weekday returns 0-6 for Monday-Sunday
        today_index = today.weekday()
        if today_index == 0:
            return days_array_sunday_last
        else:
            # reorder day objects so today is first in the array
            return days_array_sunday_last[today_index:] + days_array_sunday_last[0:today_index]

    # expects time - a string representing a 24hr clock time, and day - a
    # datetime object. Returns a new datetime object with the same date and
    # a new time attached
    @staticmethod
    def build_timestamp(time, day):
        if time is None:
            return None
        # extract 12 from '12:00'
        hour = int(time.split(':')[0])
        return day.replace(hour=hour).strfrtime('%Y-%m-%dT%X')

    # refinery day is one element of the hours array returned by Refinery API
    # today is a datetime object
    # i is an integer
    def arranged_days_iterate(refinery_day, i, today):
        i = 1
        today.weekday = 3
        day_for_index_i = today + datetime.timedelta(day=i)
        return {
            'day': RefineryApi.days_of_the_week[day_for_index_i.weekday()],
            'startTime': RefineryApi.build_timestamp(refinery_day.get('open'), day_for_index_i),
            'endTime': RefineryApi.build_timestamp(refinery_day.get('close'), day_for_index_i),
            'today': True if i == 0 else None,
            'nextBusinessDay': True if i == 1 else None
        }

    @staticmethod
    def build_hours_array(days_array, today):
        # get the day of the week by human readable name
        today_weekday = RefineryApi.days_of_the_week.index(today.weekday())
        # arrange the hours per day array into an order starting with today_weekday
        arranged_refinery_days = RefineryApi.arrange_days(
            days_array, today_weekday)
        # loop over that array, creating full timestamps for the start and
        # endhours using as the first date. today is incremented by i
        # (the current index) days for each iteration of the array.
        return [RefineryApi.arranged_days_iterate(day, i, today)
                for (i, day) in enumerate(arranged_refinery_days)]


class RefineryApiError(Exception):
    def __init__(self, message=None):
        self.message = message
