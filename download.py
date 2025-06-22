from fileinput import filename
import requests
import os
import sys
from datetime import datetime


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

ASN = 'https://ftp.ripe.net/ripe/asnames/asn.txt'

IP2ASN = 'https://ipinfo.io/data/ipinfo_lite.csv.gz?token={IPINFO_TOKEN}'

def _download_http(src, dest):
    with open(dest, "wb") as f:
        try:
            r = requests.get(src)
            r.raise_for_status()
        except requests.HTTPError as e:
            print(f'Failed to download {src} due to {e}')
        f.write(r.content)


def download_transfers(dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    for rir, url in TRANSFERS.items():
        print(f'Downloading Org transfers from {url}')
        dest = os.path.join(dest_dir, f'{rir}.json')
        _download_http(url, dest)

def download_stats(dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    for rir, url in STATS.items():
        print(f'Downloading RIR stats from {url}')
        filename = url.split('/')[-1]
        dest = os.path.join(dest_dir, f'{rir}_{filename}.txt')
        _download_http(url, dest)

def download_iana_allocations(dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    for ip_type, url in IANA_ALLOCATIONS.items():
        print(f'Downloading IANA allocations {url}')
        dest = os.path.join(dest_dir, f'{ip_type}.json')
        _download_http(url, dest)

def download_ip2asn(dest_dir: str, ipinfo_token=None):
    os.makedirs(dest_dir, exist_ok=True)
    url = IP2ASN.format(IPINFO_TOKEN=ipinfo_token)
    print(f'Downloading IP->ASN from {IP2ASN}')
    dest = os.path.join(dest_dir, 'ip2asn.csv.gz')
    _download_http(url, dest)

def download_asn(dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    print(f'Downloading ASNs from {ASN}')
    dest = os.path.join(dest_dir, 'asn.txt')
    _download_http(ASN, dest)

if __name__ == '__main__':
    dest_dir = './data'
    today = datetime.today().strftime('%Y%m%d')
    download_transfers(os.path.join(dest_dir, 'transfers', today))
    download_stats(os.path.join(dest_dir, 'stats', today))
    download_iana_allocations(os.path.join(dest_dir, 'iana', today))
    download_asn(os.path.join(dest_dir, 'asn', today))
    ipinfo_token = os.getenv('IPINFO_TOKEN', None)
    if ipinfo_token is None:
        print('IPINFO_TOKEN is not set. Skipping ip2asn download')
    else:
        download_ip2asn(os.path.join(dest_dir, 'ip2asn', today), ipinfo_token)