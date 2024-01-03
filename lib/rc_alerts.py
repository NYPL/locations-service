import requests
import os


class RCAlerts:

    @classmethod
    def get_alerts(cls):
        rc_alerts_url = os.environ['RC_ALERTS_URL']
        resp = requests.get(rc_alerts_url)
        return [cls.date_to_datetime(line.split(','))
                for line in resp.text.split('\n')[1:]]

    @classmethod
    def date_to_datetime(cls, date):
        if len(date) != 2:
            return {}
        (start, end) = date
        # TODO: this should really be either 4 or 5 depending on the date,
        # but in this case it doesn't matter
        # as long as ReCAP closures are full days
        offset = '-05:00'
        return {'applies':
                {
                    'start': f'{start}T00:00:00{offset}',
                    'end': f'{end}T23:59:58{offset}'}
                }
