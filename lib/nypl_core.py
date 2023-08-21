import requests
from requests.exceptions import JSONDecodeError, RequestException
import os


CACHE = {}


def sierra_location_by_code(location_code):
    """
    Return hash of Sierra location by location code
    """
    return nypl_core_objects('by_sierra_location.json').get(location_code)


def nypl_core_objects(name):
    if not CACHE.get(name) is None:
        return CACHE[name]

    base_url = os.environ.get('NYPL_CORE_OBJECTS_BASE_URL')
    url = f'{base_url}{name}'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except RequestException as e:
        raise NyplCoreObjectsError(
            'Failed to retrieve nypl-core-objects file from {url}: \
{errorType} {errorMessage}'
            .format(url=url, errorType=type(e), errorMessage=e)) from None

    try:
        CACHE[name] = response.json()
        return CACHE[name]
    except (JSONDecodeError, KeyError) as e:
        raise NyplCoreObjectsError(
            'Failed to parse nypl-core-objects file: \
{errorType} {errorMessage}'
            .format(errorType=type(e), errorMessage=e)) from None


class NyplCoreObjectsError(Exception):
    def __init__(self, message=None):
        self.message = message
