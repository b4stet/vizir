import requests
import os
from datetime import datetime
import sys


STATS = {
    'ripe': 'https://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-extended-latest',
    'lacnic': 'https://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-extended-latest',
    'arin': 'https://ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest',
    'apnic': 'https://ftp.apnic.net/stats/apnic/delegated-apnic-extended-latest',
    'afrinic': 'https://ftp.afrinic.net/stats/afrinic/delegated-afrinic-extended-latest',
}

TRANSFERS = {
    'ripe': 'https://ftp.ripe.net/pub/stats/ripencc/transfers/transfers_latest.json',
    'lacnic': 'https://ftp.lacnic.net/pub/stats/lacnic/transfers/transfers_latest.json',
    'arin': 'https://ftp.arin.net/pub/stats/arin/transfers/transfers_latest.json',
    'apnic': 'https://ftp.apnic.net/stats/apnic/transfers/transfers_latest.json',
    'afrinic': 'https://ftp.afrinic.net/stats/afrinic/transfers/transfers_latest.json',
}

IANA_ALLOCATIONS = {
    'ipv4': 'https://data.iana.org/rdap/ipv4.json',
    'ipv6': 'https://data.iana.org/rdap/ipv6.json',
}

def _download_http(src, dest):
    with open(dest, "wb") as f:
        try:
            r = requests.get(src)
            r.raise_for_status()
        except requests.HTTPError() as e:
            print(f'Failed to download {src} due to {e}')
        f.write(r.content)


def download_transfers(dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    for rir, url in TRANSFERS.items():
        print(f'Downloading transfers {url}')
        dest = os.path.join(dest_dir, f'{rir}.json')
        _download_http(url, dest)

def download_stats(dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    for rir, url in STATS.items():
        print(f'Downloading stats {url}')
        filename = url.split('/')[-1]
        dest = os.path.join(dest_dir, f'{rir}_{filename}.txt')
        _download_http(url, dest)

def download_allocations(dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    for ip_type, url in IANA_ALLOCATIONS.items():
        print(f'Downloading allocations {url}')
        dest = os.path.join(dest_dir, f'{ip_type}.json')
        _download_http(url, dest)

if __name__ == '__main__':
    dest_dir = './data'
    today = datetime.today().strftime('%Y%m%d')
    download_transfers(os.path.join(dest_dir, 'transfers', today))
    download_stats(os.path.join(dest_dir, 'stats', today))
    download_allocations(dest_dir)