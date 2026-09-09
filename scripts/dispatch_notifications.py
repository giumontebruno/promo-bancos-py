"""Send the daily opt-in favorite digest through the protected notification service."""
import os
import requests
from urllib.parse import urlparse


def main():
    service = os.environ.get('PAYBACK_NOTIFICATIONS_URL', '').rstrip('/')
    token = os.environ.get('PAYBACK_NOTIFICATIONS_CRON_TOKEN', '')
    if urlparse(service).scheme != 'https' or not token:
        raise RuntimeError('Notification service secrets are not configured')
    cursor, sent, failed = '', 0, 0
    for _ in range(500):
        response = requests.post(service + '/api/push/dispatch', params={'cursor': cursor},
                                 headers={'Authorization': 'Bearer ' + token}, timeout=240)
        if response.status_code != 200:
            raise RuntimeError(f'Notification service returned HTTP {response.status_code}')
        payload = response.json()
        sent += payload['sent']
        failed += payload['failed']
        cursor = payload.get('cursor')
        if not cursor:
            break
    else:
        raise RuntimeError('Daily notification pagination limit reached')
    print(f'Daily digest: {sent} sent; {failed} failed.')
    if failed:
        raise RuntimeError('Some push deliveries failed; inspect notification service')


if __name__ == '__main__':
    main()
