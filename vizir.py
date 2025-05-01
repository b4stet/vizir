#!/usr/bin/env python

import os
from datetime import datetime
from download import download_transfers, download_stats, download_allocations
from store_stats import create_schema_stats, store_stats
from store_transfers import create_schema_transfers, store_transfers
from connect import get_networks, store_subnet_supernet
from network_tree import NetworksHierarchicalTree

if __name__ == '__main__':
    today = datetime.today().strftime('%Y%m%d')
    print(f'ETL for {today}')

    project_path = os.path.dirname(os.path.abspath(__file__))
    dest_dir = os.path.join(project_path, 'data')
    download_transfers(os.path.join(dest_dir, 'transfers', today))
    download_stats(os.path.join(dest_dir, 'stats', today))
    download_allocations(dest_dir)

    data_path = os.path.join(project_path, 'data', 'stats', today)
    db_path = os.path.join(project_path, 'db', 'vizir.sqlite3')
    db_schema = os.path.join(project_path, 'db', 'schema_stats.sql')
    create_schema_stats(db_path, db_schema)
    store_stats(db_path, data_path, today)

    data_path = os.path.join(project_path, 'data', 'transfers', today)
    db_path = os.path.join(project_path, 'db', 'vizir.sqlite3')
    db_schema = os.path.join(project_path, 'db', 'schema_transfers.sql')
    create_schema_transfers(db_path, db_schema)
    store_transfers(db_path, data_path)

    print(f'Storing subnets and supernets of IPv4 networks')
    all_networks = get_networks(db_path, 'ipv4')
    network_ids = {network['block']: network['id'] for network in all_networks}
    tree = NetworksHierarchicalTree(all_networks)
    tree.build()
    store_subnet_supernet(db_path, tree, network_ids)

    print(f'Storing subnets and supernets of IPv6 networks')
    all_networks = get_networks(db_path, 'ipv6')
    network_ids = {network['block']: network['id'] for network in all_networks}
    tree = NetworksHierarchicalTree(all_networks)
    tree.build()
    store_subnet_supernet(db_path, tree, network_ids)