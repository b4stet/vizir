import os
import argparse
import sqlite3
import ipaddress
import json
from datetime import datetime, date
from network_tree import NetworkNode, NetworksHierarchicalTree


def get_iana_allocation(iana_path: str):
    iana_allocated = {'ipv4': [], 'ipv6': []}
    for filename in os.listdir(iana_path):
        filepath = os.path.join(iana_path, filename)
        with open(filepath, mode='r', encoding='utf8') as fp:
            data = json.load(fp)
        for allocation in data['services']:
            for network in allocation[0]:
                net = ipaddress.ip_network(network, strict=False)
                if net.version == 4:
                    iana_allocated['ipv4'].append(net)
                else:
                    iana_allocated['ipv6'].append(net)
    return iana_allocated

def get_networks(db_path: str, ip_type: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    all_networks = cursor.execute('SELECT * FROM inetnum WHERE ip_type = ?', (ip_type,)).fetchall()
    conn.close()

    return all_networks

def print_internet_coverage(all_networks: list, ip_type: str, iana_allocated: list):
    networks = [ipaddress.ip_network(net['value']) for net in all_networks]
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


def get_asn_changes_for_date(db_path: str, day: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    asns = {}

    events = cursor.execute((
        'SELECT t.asn as asn, t.change_type as change_type, t.old_value as old_value_id, t.new_value as new_value_id '
        'FROM timeline_asn AS t '
        'WHERE date_download = ? '
    ), (day,)).fetchall()
    for event in events:
        print(event['asn'], event['change_type'], event['old_value_id'], event['new_value_id'])
        if event['asn'] not in asns:
            asns[event['asn']] = {
                'asn': event['asn'],
            }

        old_value = None
        if event['old_value_id'] == '':
            old_value = 'n/a'

        if event['change_type'] == 'aso':
            old_org = old_value
            if old_value is None:
                old_org = cursor.execute('SELECT value FROM aso WHERE id = ?', (event['old_value_id'],)).fetchone()['value']
            new_value = cursor.execute('SELECT value FROM aso WHERE id = ?', (event['new_value_id'],)).fetchone()
            asns[event['asn']]['aso'] = old_org + '->' + new_value['value']
        elif event['change_type'] == 'org':
            old_org = old_value
            if old_value is None:
                old_org = cursor.execute('SELECT value FROM org WHERE id = ?', (event['old_value_id'],)).fetchone()['value']
            new_value = cursor.execute('SELECT value FROM org WHERE id = ?', (event['new_value_id'],)).fetchone()
            asns[event['asn']]['org'] = old_org + '->' + new_value['value']
        elif event['change_type'] == 'requestor':
            old_requestor = old_value
            if old_value is None:
                old_requestor = cursor.execute('SELECT value FROM requestor WHERE id = ?', (event['old_value_id'],)).fetchone()['value']
            new_value = cursor.execute('SELECT value FROM requestor WHERE id = ?', (event['new_value_id'],)).fetchone()
            asns[event['asn']]['requestor'] = old_requestor + '->' + new_value['value']
        elif event['change_type'] == 'cc':
            old_cc = old_value
            if old_value is None:
                old_cc = cursor.execute('SELECT value FROM cc WHERE id = ?', (event['old_value_id'],)).fetchone()['value']
            new_value = cursor.execute('SELECT value FROM cc WHERE id = ?', (event['new_value_id'],)).fetchone()
            asns[event['asn']]['cc'] = old_cc + '->' + new_value['value']
        elif event['change_type'] == 'status':
            old_status = old_value
            if old_value is None:
                old_status = cursor.execute('SELECT value FROM status WHERE id = ?', (event['old_value_id'],)).fetchone()['value']
            new_value = cursor.execute('SELECT value FROM status WHERE id = ?', (event['new_value_id'],)).fetchone()
            asns[event['asn']]['status'] = old_status + '->' + new_value['value']        
    conn.close()
    return asns


def get_network_changes_for_date(db_path: str, day: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    networks = {}

    events = cursor.execute((
        'SELECT net.id as inetnum_id, net.value as inetnum, net.ip_type as ip_type, '
        't.change_type as change_type, t.old_value as old_value_id, t.new_value as new_value_id '
        'FROM timeline_inetnum AS t ' 
        'JOIN inetnum AS net ON t.inetnum_id = net.id '
        'WHERE date_download = ? '
    ), (day,)).fetchall()
    for event in events:
        if event['inetnum'] not in networks:
            net = ipaddress.ip_network(event['inetnum'])
            networks[event['inetnum']] = {
                'inetnum_id': event['inetnum_id'],
                'value': event['inetnum'],
                'ip_start': net[0].compressed,
                'ip_end': net[-1].compressed,
                'nb_ips': net.num_addresses, 
                'cidr': net.prefixlen,
                'ip_type': event['ip_type'],
            }

        old_value = None
        if event['old_value_id'] == '':
            old_value = 'n/a'

        if event['change_type'] == 'asn':
            old_asn = old_value
            if old_value is None:
                old_asn = event['old_value_id']
            networks[event['inetnum']]['asn'] = old_asn + '->' + event['new_value_id']        
        elif event['change_type'] == 'org':
            old_org = old_value
            if old_value is None:
                old_org = cursor.execute('SELECT value FROM org WHERE id = ?', (event['old_value_id'],)).fetchone()['value']
            new_value = cursor.execute('SELECT value FROM org WHERE id = ?', (event['new_value_id'],)).fetchone()
            networks[event['inetnum']]['org'] = old_org + '->' + new_value['value']
        elif event['change_type'] == 'requestor':
            old_requestor = old_value
            if old_value is None:
                old_requestor = cursor.execute('SELECT value FROM requestor WHERE id = ?', (event['old_value_id'],)).fetchone()['value']
            new_value = cursor.execute('SELECT value FROM requestor WHERE id = ?', (event['new_value_id'],)).fetchone()
            networks[event['inetnum']]['requestor'] = old_requestor + '->' + new_value['value']
        elif event['change_type'] == 'cc':
            old_cc = old_value
            if old_value is None:
                old_cc = cursor.execute('SELECT value FROM cc WHERE id = ?', (event['old_value_id'],)).fetchone()['value']
            new_value = cursor.execute('SELECT value FROM cc WHERE id = ?', (event['new_value_id'],)).fetchone()
            networks[event['inetnum']]['cc'] = old_cc + '->' + new_value['value']
        elif event['change_type'] == 'status':
            old_status = old_value
            if old_value is None:
                old_status = cursor.execute('SELECT value FROM status WHERE id = ?', (event['old_value_id'],)).fetchone()['value']
            new_value = cursor.execute('SELECT value FROM status WHERE id = ?', (event['new_value_id'],)).fetchone()
            networks[event['inetnum']]['status'] = old_status + '->' + new_value['value']

    conn.close()
    return networks

def get_parent(db_path: str, network_id: int, day: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    parent_id = cursor.execute((
        'SELECT supernet_inetnum_id, first_seen '
        'FROM inetnum2supernet WHERE inetnum_id = ? '
        'ORDER BY first_seen DESC LIMIT 1'
        ), (network_id,)).fetchone()

    if parent_id is None:
        return None
    
    parent_since = parent_id['first_seen']
    parent_id = parent_id['supernet_inetnum_id']
    parent = cursor.execute('SELECT value, ip_type FROM inetnum WHERE id = ?', (parent_id,)).fetchone()
    parent_network = ipaddress.ip_network(parent['value'], strict=False)
    desc = f'is parent since {parent_since}'
    parent_node = NetworkNode({
        'value': parent['value'],
        'ip_start': parent_network[0].compressed,
        'ip_end': parent_network[-1].compressed,
        'cidr': parent_network.prefixlen,
        'nb_ips': parent_network.num_addresses,
        'ip_type': parent['ip_type'],
        'desc': desc
    })

    last_event_parent = cursor.execute(
        (
            'SELECT change_type, date_download '
            'FROM timeline_inetnum ' 
            'WHERE inetnum_id = ? AND CAST(date_download AS integer) <= ? '
            'ORDER BY date_download DESC LIMIT 1'
        ), (parent_id, day)
    ).fetchone()
    if last_event_parent is not None:
        desc += f', and has last change on {last_event_parent["date_download"]} concerning {last_event_parent["change_type"]}'
    parent_node.desc = desc

    conn.close()
    return parent_node


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Date of the Internet picture. Default is today. Format is %%Y%%m%%d', default=None)
    parser.add_argument('--coverage', action='store_true', help='Print Internet coverage')
    parser.add_argument('--changes', action='store_true', help='Print networks changes')
    args = parser.parse_args()

    if args.date is None:
        args.date = datetime.strftime(datetime.today(), '%Y%m%d')

    project_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_path, 'db', 'vizir.sqlite3')

    if args.coverage is True:
        iana_path = os.path.join(project_path, 'data', 'iana', args.date)
        iana_allocated = get_iana_allocation(iana_path)

        print(f'\n[+] IPv4 report coverage')
        all_ipv4 = get_networks(db_path, 'ipv4')
        print_internet_coverage(all_ipv4, 'ipv4', iana_allocated['ipv4'])

        print(f'\n[+] IPv6 report coverage')
        all_ipv6 = get_networks(db_path, 'ipv6')
        print_internet_coverage(all_ipv6, 'ipv6', iana_allocated['ipv6'])

    if args.changes is True:
        # networks changes
        networks = get_network_changes_for_date(db_path, args.date)
        print(f'\n[+] Network changes seen on {args.date} ({len(networks)} found)')
        tree = NetworksHierarchicalTree(list(networks.values()))
        for network in networks.values():
            tree.nodes[network['value']].desc = {k: v for k, v in network.items() if k in ['asn','org', 'requestor', 'cc', 'status']}

        tree.build()
        for root in tree.roots:
            root_id = networks[root.block]['inetnum_id']
            parent = get_parent(db_path, root_id, args.date)
            if parent is not None:
                tree.nodes[parent.block] = parent
        tree.build()
        tree.print_tree()

        # asns changes
        asns = get_asn_changes_for_date(db_path, args.date)
        print(f'\n[+] ASN changes seen on {args.date} ({len(asns)} found)')
        for asn in asns.values():
            print(asn)
