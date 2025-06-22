import sys
import sqlite3
import ipaddress
from network_tree import NetworksHierarchicalTree

def get_networks(db_path: str, ip_type: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    all_networks = cursor.execute(f'SELECT id, value, ip_type, cidr FROM inetnum WHERE ip_type = "{ip_type}"').fetchall()
    conn.close()

    return all_networks

def store_supernet(db_path: str, all_networks: list, supernet_date: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    network_ids = {network['value']: network['id'] for network in all_networks}
    tree = NetworksHierarchicalTree(all_networks)
    tree.build()

    nb = 0
    for node in tree.nodes.values():
        if node.parent is None:
            continue

        if nb > 0 and nb % 50000 == 0:
            conn.commit()
            print(f'Processed {nb} records')

        parent = tree.nodes[node.parent]
        cursor.execute(
            f'INSERT OR IGNORE INTO inetnum2supernet (inetnum_id, supernet_inetnum_id, first_seen) VALUES (?, ?, ?)', 
            (network_ids[node.block], network_ids[parent.block], supernet_date)
        )
        nb += 1
    conn.commit()
    print(f'Processed {nb} records')
    conn.close()


if __name__ == '__main__':
    db_path = './db/vizir.sqlite3'
    data_date = sys.argv[1]

    print(f'Storing supernets of IPv4 networks')
    all_networks = get_networks(db_path, 'ipv4')
    store_supernet(db_path, all_networks, data_date)

    print(f'Storing supernets of IPv6 networks')
    all_networks = get_networks(db_path, 'ipv6')
    store_supernet(db_path, all_networks, data_date)
