import sqlite3
import ipaddress
from network_tree import NetworksHierarchicalTree

def get_networks(db_path: str, ip_type: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    all_networks = cursor.execute(f'SELECT id, block, ip_type, ip_start, ip_end, cidr, nb_ips FROM ip_blocks WHERE ip_type = "{ip_type}"').fetchall()
    conn.close()

    return all_networks

def store_subnet_supernet(db_path: str, tree: NetworksHierarchicalTree, network_ids: dict):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for node in tree.nodes.values():
        if node.parent is None:
            continue

        parent = tree.nodes[node.parent]

        # the parent is a supernet of the block
        cursor.execute(
            f'INSERT OR IGNORE INTO supernets (block_id, is_supernet_of_block_id) VALUES (?, ?)', 
            (network_ids[parent.block], network_ids[node.block])
        )

        # the block is a direct subnet of the parent
        cursor.execute(
            f'INSERT OR IGNORE INTO subnets (block_id, is_subnet_of_block_id) VALUES (?, ?)', 
            (network_ids[node.block], network_ids[parent.block])
        )
    conn.commit()
    conn.close()


if __name__ == '__main__':
    db_path = './db/vizir.sqlite3'

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