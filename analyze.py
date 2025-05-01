import argparse
import sqlite3
import ipaddress
import json
from network_tree import NetworkNode, NetworksHierarchicalTree


def get_iana_allocation(iana_path: dict):
    iana_allocated = {'ipv4': [], 'ipv6': []}
    for ip_type, source in iana_path.items():
        with open(source, 'r') as fp:
            data = json.load(fp)

            for allocation in data['services']:
                iana_allocated[ip_type].extend([ipaddress.ip_network(b) for b in allocation[0]])
    return iana_allocated

def get_networks(db_path: str, ip_type: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    all_networks = cursor.execute('SELECT * FROM ip_blocks WHERE ip_type = ?', (ip_type,)).fetchall()
    conn.close()

    return all_networks

def print_internet_coverage(all_networks: list, ip_type: str, iana_allocated: list):
    networks = [ipaddress.ip_network(b['block']) for b in all_networks]
    networks_not_iana = [b for b in networks if b not in iana_allocated]
    print(f'Found {len(iana_allocated)} {ip_type} networks allocated by IANA')
    print(f'Found {len(networks_not_iana)} {ip_type} networks in DB (IANA allocation excluded)')
    print(f'Found {len(networks) - len(networks_not_iana)} {ip_type} networks in DB equal to IANA allocation')

    collapsed = list(ipaddress.collapse_addresses(networks_not_iana))
    nb_ip_not_iana = sum([b.num_addresses for b in collapsed])
    nb_ip_iana = sum([b.num_addresses for b in iana_allocated])
    nb_ip_max = 2**32 if ip_type == 'ipv4' else 2**128
    print(f'IANA allocated {nb_ip_iana} {ip_type}, {nb_ip_iana/nb_ip_max*100:.2f}% of the space')
    print(f'Found {len(collapsed)} non-overlapping networks {ip_type}, accounting for {nb_ip_not_iana} {ip_type}, {nb_ip_not_iana/nb_ip_iana*100:.2f}% of IANA allocation')


def get_changes_for_date(db_path: str, date: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    networks = {}

    stats = cursor.execute((
        'SELECT b.id as block_id, b.block as block, b.ip_type as ip_type, c.cc as cc, s.status as status, r.requestor as requestor '
        'FROM timeline AS t ' 
        'JOIN ip_blocks AS b ON t.block_id = b.id '
        'JOIN country_codes AS c ON t.cc_id = c.id '
        'JOIN statuses AS s ON t.status_id = s.id '
        'JOIN requestors AS r ON t.requestor_id = r.id '
        'WHERE date = ? OR record_date = ?'
    ), (date, date)).fetchall()
    for network in stats:
        if network['block'] not in networks:
            net = ipaddress.ip_network(network['block'])
            networks[network['block']] = {
                'block_id': network['block_id'],
                'block': network['block'],
                'ip_start': net[0].compressed,
                'ip_end': net[-1].compressed,
                'nb_ips': net.num_addresses, 
                'cidr': net.prefixlen,
                'ip_type': network['ip_type'],
            }

        networks[network['block']]['cc'] = network['cc']
        networks[network['block']]['status'] = network['status']
        networks[network['block']]['requestor'] = network['requestor']

    transfers = cursor.execute((
        'SELECT b.id as block_id, b.block as block, b.ip_type as ip_type, src.org as src_org, dst.org as dst_org '
        'FROM transfers AS t ' 
        'JOIN ip_blocks AS b ON t.block_id = b.id '
        'JOIN orgs AS src ON t.src_org_id = src.id '
        'JOIN orgs AS dst ON t.dst_org_id = dst.id '
        'WHERE date = ?'
    ), (date,)).fetchall()
    for network in transfers:
        if network['block'] not in networks:
            net = ipaddress.ip_network(network['block'])
            networks[network['block']] = {
                'block_id': network['block_id'],
                'block': network['block'],
                'ip_start': net[0].compressed,
                'ip_end': net[-1].compressed,
                'nb_ips': net.num_addresses, 
                'cidr': net.prefixlen,
                'ip_type': network['ip_type'],
            }

        networks[network['block']]['src_org'] = network['src_org']
        networks[network['block']]['dst_org'] = network['dst_org']
    conn.close()

    return networks

def get_parent(db_path: str, network_id: int, day: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    parent_id = cursor.execute('SELECT block_id FROM supernets WHERE is_supernet_of_block_id = ?', (network_id,)).fetchone()

    if parent_id is None:
        return None
    
    parent = cursor.execute('SELECT block, ip_type, ip_start, ip_end, cidr, nb_ips FROM ip_blocks WHERE id = ?', (parent_id['block_id'],)).fetchone()
    last_stat = cursor.execute(
        (
            'SELECT c.cc as cc, s.status as status, r.requestor as requestor '
            'FROM timeline AS t ' 
            'JOIN country_codes AS c ON t.cc_id = c.id '
            'JOIN statuses AS s ON t.status_id = s.id '
            'JOIN requestors AS r ON t.requestor_id = r.id '
            'WHERE block_id = ? AND CAST(date AS integer) <= ? '
            'ORDER BY date DESC LIMIT 1'
        ), (parent_id['block_id'], day)
    ).fetchone()
    last_transfer = cursor.execute(
        (
            'SELECT src.org as src_org, dst.org as dst_org '
            'FROM transfers AS t ' 
            'JOIN orgs AS src ON t.src_org_id = src.id '
            'JOIN orgs AS dst ON t.dst_org_id = dst.id '
            'WHERE block_id = ? AND CAST(date AS integer) <= ? '
            'ORDER BY date DESC LIMIT 1'
        ), (parent_id['block_id'], day)
    ).fetchone()

    parent_node = NetworkNode({
        'block': parent['block'],
        'ip_start': parent['ip_start'],
        'ip_end': parent['ip_end'],
        'cidr': parent['cidr'],
        'nb_ips': parent['nb_ips'],
        'ip_type': parent['ip_type'],
    })

    desc = {'type': 'parent info'}
    if last_stat is not None:
        desc['cc'] = last_stat['cc']
        desc['status'] = last_stat['status']
        desc['requestor'] = last_stat['requestor']
    if last_transfer is not None:
        desc['src_org'] = last_transfer['src_org']
        desc['dst_org'] = last_transfer['dst_org']
    parent_node.desc = desc

    return parent_node


if __name__ == '__main__':
    db_path = './db/vizir.sqlite3'
    iana_path = {
        'ipv4': './data/ipv4.json',
        'ipv6': './data/ipv6.json',
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('--coverage', action='store_true', help='Print Internet coverage')
    parser.add_argument('--date', type=str, help='See changes at that date, format is %Y%m%d', default=None)
    args = parser.parse_args()

    if args.coverage is True:
        iana_allocated = get_iana_allocation(iana_path)

        print(f'\n[+] IPv4 report coverage')
        all_ipv4 = get_networks(db_path, 'ipv4')
        print_internet_coverage(all_ipv4, 'ipv4', iana_allocated['ipv4'])

        print(f'\n[+] IPv6 report coverage')
        all_ipv6 = get_networks(db_path, 'ipv6')
        print_internet_coverage(all_ipv6, 'ipv6', iana_allocated['ipv6'])

    if args.date is not None:
        networks = get_changes_for_date(db_path, args.date)
        print(f'\n[+] Changes seen on {args.date} ({len(networks)} found)')
        tree = NetworksHierarchicalTree(list(networks.values()))
        for network in networks.values():
            tree.nodes[network['block']].desc = {k: v for k, v in network.items() if k in ['status', 'cc', 'requestor', 'src_org', 'dst_org']}

        tree.build()
        for root in tree.roots:
            root_id = networks[root.block]['block_id']
            parent = get_parent(db_path, root_id, args.date)
            if parent is not None:
                tree.nodes[parent.block] = parent

        tree.build()
        tree.print_tree()
