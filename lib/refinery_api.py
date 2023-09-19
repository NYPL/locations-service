import requests
import os
import datetime

from functools import cache
from requests.exceptions import JSONDecodeError, RequestException

from lib.logger import GlobalLogger
from lib.errors import RefineryApiError


GlobalLogger.initialize_logger(__name__)
logger = GlobalLogger.logger


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
    data = {}
    location = determine_location(code)
    if location is None:
        return None
    logger.debug(f'Checking cache for {location}')
    location_data = check_cache_and_or_fetch_data(location)\
        .get('location_data')
    if 'location' in fields:
        data['location'] = parse_address(location_data)
    if 'hours' in fields:
        hours_array = build_hours_array(
            location_data.get('hours').get('regular'),
            datetime.datetime.now())
        alerts = location_data.get('_embedded', {}).get('alerts')
        # TODO: length of alerts with 'applies' is not 0
        if [len(alerts) != 0]:
            print('alerts length zero')
            hours_array = apply_alerts(hours_array, alerts)
    return data


def check_cache_and_or_fetch_data(location):
    location_data = fetch_location_data(location)
    delta = datetime.datetime.now() - location_data.get('updated_at')
    if delta.seconds > 3600:
        fetch_location_data.cache_clear()
        logger.info('Refreshing Refinery API data for location: ' + location)
        location_data = fetch_location_data(location)
    return location_data


def determine_location(code):
    location = None
    if code.startswith('ma'):
        location = 'schwarzman'
    elif code.startswith('sc'):
        location = 'schomburg'
    elif code.startswith('pa'):
        location = 'lpa'
    else:
        logger.warning('Unsupported location provided: ' + code)
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


def apply_alerts(days_array, alerts):
    for alert in alerts:
        alert_start_string = alert.get('applies', {}).get('start')
        alert_end_string = alert.get('applies', {}).get('end')
        if alert_start_string is None and alert_end_string is None:
            continue
        for day in days_array:
            if day['startTime'] is None and day['endTime'] is None:
                continue
            day_start, day_end, alert_start, alert_end = \
                [datetime.datetime.fromisoformat(iso_string)
                    for iso_string in
                 [day['startTime'], day['endTime'],
                 alert_start_string, alert_end_string]]
            # Closure starts during operating hours (Early closing):
            if alert_start > day_start and alert_start < day_end:
                day['endTime'] = alert_start_string
            # Closure ends during operating hours (Late opening):
            if alert_end > day_start and alert_end < day_end:
                day['startTime'] = alert_end_string
            # (Closure occludes operating hours entirely)
            if alert_start <= day_start and alert_end >= day_end:
                day['startTime'] = day['endTime'] = None
    return days_array
