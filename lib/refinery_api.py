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
            'updated_at': datetime.datetime.now()
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
        alerts = location_data.get('_embedded', {}).get('alerts')
        closure_alerts = [alert for alert in alerts
                          if alert.get('applies') is not None]
        data['hours'] = build_hours_array(
            location_data.get('hours').get('regular'),
            datetime.datetime.now().astimezone(), closure_alerts)
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
    return day.replace(hour=hour).isoformat()


# refinery day is one element of the hours array returned by Refinery API
# today is a datetime object
def build_hours_hash(refinery_day, offset, today, alerts=[]):
    new_date = today + datetime.timedelta(days=offset)
    start_time = build_timestamp(
        refinery_day.get('open'), new_date)
    end_time = build_timestamp(
        refinery_day.get('close'), new_date)
    for alert in alerts:
        alert_start = alert.get('applies', {}).get('start')
        alert_end = alert.get('applies', {}).get('end')
        if alert_start is None and alert_end is None:
            continue
        start_time, end_time = update_times(
            start_time, end_time, alert_start, alert_end)
    hours = {
        'day': new_date.strftime('%A'),
        'startTime': start_time,
        'endTime': end_time
    }
    if offset == 0:
        hours['today'] = True
    if offset == 1:
        hours['nextBusinessDay'] = True
    return hours


def build_hours_array(days_array, today, alerts=[]):
    refinery_days_sunday_last = days_array[1:] + days_array[0:]
    # loop over that array, creating full timestamps for the start and
    # endhours using as the first date. today is incremented by i
    # (the current index) days for each iteration of the array.
    days_with_timestamp = []
    for i in range(7):
        offset = (7 + i - today.weekday()) % 7
        days_with_timestamp.append(build_hours_hash(
            refinery_days_sunday_last[i], offset, today, alerts))
    return days_with_timestamp


def update_times(day_start_string, day_end_string, alert_start_string, alert_end_string):
    """
    Given iso-formatted strings representing regular scheduled opening and 
    closing times ('day_start' and 'day_end' strings), and the end and start 
    times of a closure alert, update the day start and end strings to account
    for any overlapping/relevant closure alerts.
    """
    if day_start_string is None and day_end_string is None:
        return (day_start_string, day_end_string)
    # Convert to object so we can math!
    day_start, day_end, alert_start, alert_end = \
        [datetime.datetime.fromisoformat(iso_string)
            for iso_string in
            [day_start_string, day_end_string,
             alert_start_string, alert_end_string]]
    # Closure starts during operating hours (Early closing):
    if alert_start > day_start and alert_start < day_end:
        day_end_string = alert_start_string
    # Closure ends during operating hours (Late opening):
    elif alert_end > day_start and alert_end < day_end:
        day_start_string = alert_end_string
    # (Closure occludes operating hours entirely)
    elif alert_start <= day_start and alert_end >= day_end:
        return (None, None)
    return (day_start_string, day_end_string)
