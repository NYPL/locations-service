import requests
import os
import datetime

from dateutil.parser import parse
from functools import cache
from requests.exceptions import JSONDecodeError, RequestException

from lib.logger import GlobalLogger
from lib.errors import RefineryApiError


GlobalLogger.initialize_logger(__name__)
logger = GlobalLogger.logger

INTEGER_DAYS = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6
}


@cache
def get_location_by_code(code):
    try:
        response = requests.get(
            f"{os.environ['DRUPAL_API_BASE_URL']}?filter[field_ts_location_code]={code}"
        )
        response.raise_for_status()
        response = response.json()
        if not response.get('data') or not isinstance(response.get('data'), list):
            return None
        return response.get('data')[0].get('attributes', None)
    except RequestException as e:
        raise RefineryApiError(
            f'Failed to retrieve Drupal API location data \
            for {code}: {e}')
    except (JSONDecodeError, KeyError) as e:
        raise RefineryApiError(
            f'Failed to parse Drupal API response: \
                {type(e)} {e}')


def parse_address(address_data):
    return {
        'line1': address_data.get('address_line1', ''),
        'city': address_data.get('locality', ''),
        'state': address_data.get('administrative_area', ''),
        'postal_code': address_data.get('postal_code', '')
    }


def datetime_from_hours_string(base_date: datetime, hours_string: str):
    # given a base date, turn a string like 10 AM into a datetime
    hour_and_time_of_day = hours_string.split(' ')
    hour = int(hour_and_time_of_day[0])
    time_of_day = hour_and_time_of_day[1]
    if time_of_day.lower() == 'pm' and hour != 12:
        hour += 12
    if time_of_day.lower() == 'am' and hour == 12:
        hour = 0
    return base_date.replace(hour=hour).isoformat()


def parse_hours(current_date: datetime, date):
    # parse hours in the form
    # {
    #  "day": "Tuesday",
    #  "date": "8/26",
    #  "hours": "10 AM–8 PM"
    # },
    # to the expected return format
    # {
    #   "day": "Tuesday",
    #   "startTime": "2025-08-26T10:00:00+00:00",
    #   "endTime": "2025-08-26T20:00:00+00:00",
    #   "today": true
    # },

    # get a datetime for this weekday based off today's weekday
    weekday = date.get('day')
    current_weekday = current_date.weekday()
    weekday_index = INTEGER_DAYS.get(weekday.upper())
    if weekday_index >= current_weekday:
        weekday_offset = weekday_index - current_date.weekday()
    else:
        weekday_offset = 7 - current_weekday + weekday_index

    base_date = current_date + datetime.timedelta(days=weekday_offset)

    hours = {
        'day': weekday
    }

    # get start and close times from the "10 AM-8 PM" hours string
    if date.get('hours').lower() == 'closed':
        hours['startTime'] = None
        hours['endTime'] = None
    else:
        start_and_end = date.get('hours').split('–')
        hours['startTime'] = datetime_from_hours_string(base_date, start_and_end[0])
        hours['endTime'] = datetime_from_hours_string(base_date, start_and_end[1])
    if weekday_offset == 0:
        hours['today'] = True
    return hours


# given an array of fields and a location
#  code, return an dict populated
# by those fields for that location code.
def get_location_data(code, fields):
    data = {}
    location_data = check_cache_and_or_fetch_data(code)
    if location_data is None:
        return None
    if 'location' in fields:
        data['location'] = parse_address(location_data.get('field_as_address', {}))
    if 'hours' in fields:
        # If upcoming_hours exists, use that, otherwise use regular_hours
        location_hours = location_data.get('location_hours')
        upcoming_hours = (
                location_hours.get('upcoming_hours')
                if location_hours.get('upcoming_hours')
                else location_hours.get('regular_hours')
        )
        data['hours'] = []
        current_date = datetime.datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
        today_index = 0
        for index in range(len(upcoming_hours)):
            date = upcoming_hours[index]
            parsed_hours = parse_hours(current_date, date)
            data['hours'].append(parsed_hours)
            if parsed_hours.get('today'):
                today_index = index
        # determine the next business day
        for offset in range(1, 7):
            relative_offset = (today_index + offset) % 7
            if data['hours'][relative_offset].get('startTime'):
                data['hours'][relative_offset]['nextBusinessDay'] = True
                break

    return data


def check_cache_and_or_fetch_data(code):
    location_data = get_location_by_code(code)
    if not location_data:
        return None
    delta = datetime.datetime.now(tz=datetime.timezone.utc) - parse(location_data.get('changed'))
    if delta.seconds > 3600:
        get_location_by_code.cache_clear()
        logger.info('Refreshing Drupal API data for location: ' + code)
        location_data = get_location_by_code(code)
    return location_data
