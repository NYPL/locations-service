import requests
import os
import datetime

from requests.exceptions import JSONDecodeError, RequestException
from functools import cache


@cache
def fetch_location_data(location):
    try:
        response = requests.get(
            os.environ['REFINERY_API_BASE_URL'] + location)
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


def parse_address(data):
    return {
        'line1': data.get('street_address'),
        'city': data.get('locality'),
        'state': data.get('region'),
        'postal_code': data.get('postal_code')
    }


# given an array of fields and a location
#  code, return an dict populated
# by those fields for that location code.
def get_refinery_data(code, fields):
    print('dataaa')
    data = {}
    location = determine_location(code)
    location_data = check_cache_and_or_fetch_data(location)\
        .get('location_data')
    if 'location' in fields:
        data['location'] = parse_address(location_data)
    if 'hours' in fields:
        data['hours'] = build_hours_array(
            location_data.get('hours').get('regular'),
            datetime.datetime.today())
    return data


def check_cache_and_or_fetch_data(location):
    location_data = fetch_location_data(location)
    delta = datetime.datetime.today() - location_data.get('updated_at')
    if delta.seconds > 3600:
        fetch_location_data.cache_clear()
        location_data = fetch_location_data(location)

    return location_data


def determine_location(code):
    location = ''
    if code.startswith('ma'):
        location = 'schwarzman'
    if code.startswith('sc'):
        location = 'schomburg'
    if code.startswith('pa'):
        location = 'lpa'
    if location == '':
        raise RefineryApiError('Unsupported location provided: ' + code)
    return location


# expects time - a string representing a 24hr clock time, and day - a
# datetime object. Returns a
#  string representing day updated to a new time
# in format YYYY-MM-DDTHH:MM
def build_timestamp(time, day):
    if time is None:
        return None
    # extract 12 from '12:00'
    hour = int(time.split(':')[0])
    return day.replace(hour=hour).strftime('%Y-%m-%dT%X')


# refinery day is one element of the hours array returned by Refinery API
# today is a datetime object
def build_hours_hash(refinery_day, offset, today):
    new_date = today + datetime.timedelta(days=offset)
    hours = {
        'day': new_date.strftime('%A'),
        'startTime': build_timestamp(
            refinery_day.get('open'), new_date),
        'endTime': build_timestamp(
            refinery_day.get('close'), new_date),
    }
    if offset == 0:
        hours['today'] = True
    if offset == 1:
        hours['nextBusinessDay'] = True

    return hours


def build_hours_array(days_array, today):
    # put sunday
    refinery_days_sunday_last = days_array[1:] + days_array[0:]
    # loop over that array, creating full timestamps for the start and
    # endhours using as the first date. today is incremented by i
    # (the current index) days for each iteration of the array.
    days_with_timestamp = []
    for i in range(7):
        offset = (7 + i - today.weekday()) % 7
        days_with_timestamp.append(build_hours_hash(
            refinery_days_sunday_last[i], offset, today))
    return days_with_timestamp


class RefineryApiError(Exception):
    def __init__(self, message=None):
        self.message = message
