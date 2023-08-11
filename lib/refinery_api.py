import requests
from requests.exceptions import JSONDecodeError, RequestException
import datetime
from functools import cache


class RefineryApi:
    BASE_URL = "https://refinery.nypl.org/api/nypl/locations/v1.0/locations/"
    # this order is based on python's datetime.weekday() which returns 0 for
    #   Monday and 6 for Sunday:

    @cache
    @staticmethod
    def fetch_location_data(location):
        try:
            response = requests.get(RefineryApi.BASE_URL + location)
            response.raise_for_status()
            response = response.json()
            return {
                'location_data': response.get('location'),
                'updated_at': datetime.datetime.today()
            }
        except RequestException as e:
            raise RefineryApiError(
                f'Failed to retrieve Refinery API location data \
                for {location}: {e}')
        except (JSONDecodeError, KeyError) as e:
            raise RefineryApiError(
                f'Failed to parse Refinery API response: \
                    {type(e)} {e}')

    @staticmethod
    def parse_address(data):
        parsed_data = {}
        parsed_data['line1'] = data.get('street_address')
        parsed_data['city'] = data.get('locality')
        parsed_data['state'] = data.get('region')
        parsed_data['postal_code'] = data.get('postal_code')
        return parsed_data

    # given an array of fields and a location code, return an dict populated
    # by those fields for that location code.
    @staticmethod
    def get_refinery_data(code, fields):
        data = {}
        location = RefineryApi.determine_location(code)
        location_data = RefineryApi.check_cache_and_or_fetch_data(location)\
            .get('location_data')
        if 'address' in fields:
            data['address'] = RefineryApi.parse_address(location_data)
        if 'hours' in fields:
            data['hours'] = RefineryApi.build_hours_array(
                location_data.get('hours').get('regular'),
                datetime.datetime.today())
        return data

    @staticmethod
    def check_cache_and_or_fetch_data(location):
        location_data = RefineryApi.fetch_location_data(location)
        delta = datetime.datetime.today() - location_data.get('updated_at')
        if delta.seconds > 3600:
            RefineryApi.fetch_location_data.cache_clear()
            location_data = RefineryApi.fetch_location_data(location)
        return location_data

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

    # expects time - a string representing a 24hr clock time, and day - a
    # datetime object. Returns a string representing day updated to a new time
    # in format YYYY-MM-DDTHH:MM
    @staticmethod
    def build_timestamp(time, day):
        if time is None:
            return None
        # extract 12 from '12:00'
        hour = int(time.split(':')[0])
        return day.replace(hour=hour).strftime('%Y-%m-%dT%X')

    # refinery day is one element of the hours array returned by Refinery API
    # today is a datetime object
    # i is an integer
    @staticmethod
    def build_hours_hash(refinery_day, offset, today):
        new_date = today + datetime.timedelta(days=offset)
        hours = {
            'day': new_date.strftime('%A'),
            'startTime': RefineryApi.build_timestamp(
                refinery_day.get('open'), new_date),
            'endTime': RefineryApi.build_timestamp(
                refinery_day.get('close'), new_date),
        }
        if offset == 0:
            hours['today'] = True
        if offset == 1:
            hours['nextBusinessDay'] = True
        return hours

    @staticmethod
    def build_hours_array(days_array, today):
        # put sunday
        refinery_days_sunday_last = days_array[1:] + days_array[0:]
        # loop over that array, creating full timestamps for the start and
        # endhours using as the first date. today is incremented by i
        # (the current index) days for each iteration of the array.
        days_with_timestamp = []
        for i in range(7):
            offset = (7 + i - today.weekday()) % 7
            days_with_timestamp.append(RefineryApi.build_hours_hash(
                refinery_days_sunday_last[i], offset, today))
        return days_with_timestamp


class RefineryApiError(Exception):
    def __init__(self, message=None):
        self.message = message
