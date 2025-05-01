from re import I
import sys
import os
import sqlite3
import json
import ipaddress

def create_schema_transfers(db_path: str, db_schema: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    table_exists = cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="transfers"').fetchone()
    if table_exists:
        print('Table transfers already exists')
        return

    print(f'Creating transfers table according to {db_schema}')
    with open(db_schema, mode='r', encoding='utf8') as fp:
        cursor.executescript(fp.read())
    conn.close()

def _store_network_transfers(cursor: sqlite3.Cursor, filename: str, transfer_date: str, transfer_type: str, src_org_id: int, dst_org_id: int, networks):
    for network in networks:
        ip_start = network['start_address']
        if '.' in ip_start:
            ip_start = '.'.join([str(int(i)) for i in network['start_address'].split('.')])
        ip_start = ipaddress.ip_address(ip_start)
        ip_end = network['end_address']
        if '.' in ip_end:
            ip_end = '.'.join([str(int(i)) for i in network['end_address'].split('.')])
        ip_end = ipaddress.ip_address(ip_end)
        network = list(ipaddress.summarize_address_range(ip_start, ip_end))[0]
        ip_type = 'ipv4' if network.version == 4 else 'ipv6'

        # store block
        cursor.execute((
            'INSERT OR IGNORE INTO ip_blocks (block, cidr, nb_ips, ip_type, ip_start, ip_end) '
            'VALUES (?, ?, ?, ?, ?, ?)'
        ), (
            network.compressed, network.prefixlen, str(network.num_addresses), 
            ip_type, network[0].compressed, network[-1].compressed
        ))
        block_id = cursor.execute('SELECT id FROM ip_blocks WHERE block = ?', (network.compressed,)).fetchone()['id']

        # store transfer
        cursor.execute((
            'INSERT OR IGNORE INTO transfers (date, block_id, asn_id, transfer_type, src_org_id, dst_org_id, source_filepath) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)'
        ), (
            transfer_date, block_id, '', transfer_type, src_org_id, dst_org_id, filename
        ))

def _store_asn_transfers(cursor: sqlite3.Cursor, filename: str, transfer_date: str, transfer_type: str, src_org_id: int, dst_org_id: int, asns):
    for asn_block in asns:
        asn_start = int(asn_block['start'])
        asn_end = int(asn_block['end'])

        for asn in range(asn_start, asn_end + 1):
            # store asn
            cursor.execute('INSERT OR IGNORE INTO asns (asn) VALUES (?)', (asn,))
            asn_id = cursor.execute('SELECT id FROM asns WHERE asn = ?', (asn,)).fetchone()['id']

            # store transfer
            cursor.execute((
                'INSERT OR IGNORE INTO transfers (date, block_id, asn_id, transfer_type, src_org_id, dst_org_id, source_filepath) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)'
            ), (
                transfer_date, '', asn_id, transfer_type, src_org_id, dst_org_id, filename
            ))

def store_transfers(db_path: str, files_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    for filename in os.listdir(files_path):
        print(f'Parsing {filename}')
        filepath = os.path.join(files_path, filename)
        with open(filepath, mode='r', encoding='utf8') as fp:
            transfers = json.load(fp)

        nb = 0
        for transfer in transfers['transfers']:
            # it's just a RIR transfer
            if 'recipient_organization' not in transfer or 'source_organization' not in transfer:
                continue

            if nb > 0 and nb % 10000 == 0:
                conn.commit()
                print(f'Processed {nb} transfers')

            transfer_date = transfer['transfer_date'].replace('-', '').replace('T', ' ').split(' ')[0]
            transfer_type = transfer['type']
            src_org = transfer['source_organization']['name']
            if src_org is None:
                src_org = ''
            src_org = ''.join([c for c in src_org if c.isprintable()])
            cursor.execute('INSERT OR IGNORE INTO orgs (org) VALUES (?)', (src_org,))
            src_org_id = cursor.execute('SELECT id FROM orgs WHERE org = ?', (src_org,)).fetchone()['id']

            dst_org = transfer['recipient_organization']['name']
            dst_org_id = None
            if dst_org is None:
                dst_org = ''
            dst_org = ''.join([c for c in dst_org if c.isprintable()])
            cursor.execute('INSERT OR IGNORE INTO orgs (org) VALUES (?)', (dst_org,))
            dst_org_id = cursor.execute('SELECT id FROM orgs WHERE org = ?', (dst_org,)).fetchone()['id']

            if 'ip4nets' in transfer:
                networks = transfer['ip4nets']
                if isinstance(networks, list) and len(networks) > 0: 
                    networks = networks[0]
                if isinstance(networks, dict):
                    networks = networks['transfer_set']
                _store_network_transfers(cursor, filepath, transfer_date, transfer_type, src_org_id, dst_org_id, networks)
                nb += len(networks)

            if 'ip6nets' in transfer:
                networks = transfer['ip6nets']
                if isinstance(networks, list) and len(networks) > 0:
                    networks = networks[0]
                if isinstance(networks, dict):
                    networks = networks['transfer_set']
                _store_network_transfers(cursor, filepath, transfer_date, transfer_type, src_org_id, dst_org_id, networks)
                nb += len(networks)
            
            if 'asns' in transfer:
                asns = transfer['asns']
                if isinstance(asns, list) and len(asns) > 0:
                    asns = asns[0]
                if isinstance(asns, dict):
                    asns = asns['transfer_set']
                _store_asn_transfers(cursor, filepath, transfer_date, transfer_type, src_org_id, dst_org_id, asns)
                nb += len(asns)
        conn.commit()
        print(f'Processed {nb} transfers')
    conn.close()

if __name__ == '__main__':
    date = sys.argv[1]
    data_path = os.path.join('.', 'data', 'transfers', date)
    db_path = os.path.join('.', 'db', 'vizir.sqlite3')
    db_schema = os.path.join('.', 'db', 'schema_transfers.sql')

    create_schema_transfers(db_path, db_schema)
    store_transfers(db_path, data_path)

