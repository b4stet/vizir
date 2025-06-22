#!/usr/bin/env python

import os
from datetime import datetime
from download import download_transfers, download_stats, download_iana_allocations, download_ip2asn, download_asn
from store import create_schema, store_timelines
from connect_data import get_networks, store_supernet

if __name__ == '__main__':
    today = datetime.today().strftime('%Y%m%d')
    print(f'### ETL for {today} ###')

    # download
    project_path = os.path.dirname(os.path.abspath(__file__))
    dest_dir = os.path.join(project_path, 'data')
    download_transfers(os.path.join(dest_dir, 'transfers', today))
    download_stats(os.path.join(dest_dir, 'stats', today))
    download_iana_allocations(os.path.join(dest_dir, 'iana', today))
    download_asn(os.path.join(dest_dir, 'asn', today))
    ipinfo_token = os.getenv('IPINFO_TOKEN', None)
    if ipinfo_token is None:
        print('IPINFO_TOKEN is not set. Skipping ip2asn download')
    else:
        download_ip2asn(os.path.join(dest_dir, 'ip2asn', today), ipinfo_token)

    # store data
    db_path = os.path.join(project_path, 'db', 'vizir.sqlite3')
    db_schema = os.path.join(project_path, 'db', 'schema.sql')
    data_path = os.path.join(project_path, 'data')
    create_schema(db_path, db_schema)
    store_timelines(db_path, data_path, today)

    # store network relationship
    print(f'Storing supernets of IPv4 networks')
    all_networks = get_networks(db_path, 'ipv4')
    store_supernet(db_path, all_networks, today)

    print(f'Storing supernets of IPv6 networks')
    all_networks = get_networks(db_path, 'ipv6')
    store_supernet(db_path, all_networks, today)

