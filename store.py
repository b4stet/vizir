import sys
import os
import json
import sqlite3
import ipaddress
import time
import gzip
import csv


def create_schema(db_path: str, db_schema: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    table_exists = cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="inetnum"').fetchone()
    if table_exists:
        print('Schema already created. Skipping')
        return

    print(f'Creating schema according to {db_schema}')
    with open(db_schema, mode='r', encoding='utf8') as fp:
        cursor.executescript(fp.read())
    conn.close()

def timeline_stat_inetnum(
        cursor: sqlite3.Cursor, filepath: str, data_date: str, date_registry: str,  
        value : str, cidr_or_nb_ips: int, record_type: str, status_id: int, requestor_id: int, cc_id: int
):
    ip_start = ipaddress.ip_address(value)
    
    if record_type == 'ipv4':
        ip_end = ip_start + cidr_or_nb_ips - 1
        inetnum = list(ipaddress.summarize_address_range(ip_start, ip_end))[0]
    elif record_type == 'ipv6':
        inetnum = ipaddress.ip_network(ip_start.compressed + '/' + str(cidr_or_nb_ips), strict=False)

    # store inetnum
    cursor.execute('INSERT OR IGNORE INTO inetnum (value, ip_type, cidr) VALUES (?, ?, ?)', (inetnum.compressed, record_type, inetnum.prefixlen))
    inetnum_id = cursor.execute('SELECT id FROM inetnum WHERE value = ?', (inetnum.compressed,)).fetchone()['id']

    # update the timeline
    for change_type, new_value in zip(['status', 'requestor', 'cc'], [status_id, requestor_id, cc_id]):
        last_event = cursor.execute('SELECT * FROM timeline_inetnum WHERE inetnum_id = ? AND change_type = ? ORDER BY id DESC LIMIT 1', (inetnum_id, change_type)).fetchone()
        if last_event is None or last_event['new_value'] != str(new_value):
            old_value = last_event['new_value'] if last_event is not None else ''
            cursor.execute((
                'INSERT OR IGNORE INTO timeline_inetnum (date_download, date_registry, change_type, inetnum_id, old_value, new_value, source) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)'
            ), (data_date, date_registry, change_type, inetnum_id, old_value, str(new_value), filepath))

def timeline_stat_asn(
    cursor: sqlite3.Cursor, filepath: str, data_date: str, date_registry: str,  
    asn : int, status_id: int, requestor_id: int, cc_id: int
):
    # update the timeline
    for change_type, new_value in zip(['status', 'requestor', 'cc'], [status_id, requestor_id, cc_id]):
        last_event = cursor.execute('SELECT * FROM timeline_asn WHERE asn = ? AND change_type = ? ORDER BY id DESC LIMIT 1', (asn, change_type)).fetchone()
        if last_event is None or last_event['new_value'] != str(new_value):
            old_value = last_event['new_value'] if last_event is not None else ''
            cursor.execute((
                'INSERT OR IGNORE INTO timeline_asn (date_download, date_registry, change_type, asn, old_value, new_value, source) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)'
            ), (data_date, date_registry, change_type, asn, old_value, str(new_value), filepath))


def _process_stat_files(db_path: str, data_path: str, data_date: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    for filename in os.listdir(data_path):
        filepath = os.path.join(data_path, filename)
        print(f'Parsing {filepath}')
        with open(filepath, mode='r', encoding='utf8') as fp:
            nb = 0
            for line in fp:
                line = line.strip('\n')
                if nb > 0 and nb % 10000 == 0:
                    conn.commit()
                    print(f'Processed {nb} records')

                # filter on IP records
                if '|summary' in line:
                    continue

                if '|ipv' not in line and '|asn' not in line:
                    continue

                # parse record
                record = line.split('|')
                cc = record[1]
                record_type = record[2]
                value = record[3]
                date_registry = record[5]
                status = record[6]
                requestor = record[7] if len(record) > 7 else ''

                # store attributes
                status_id = cursor.execute('SELECT id FROM status WHERE value = ?', (status,)).fetchone()['id']
                cursor.execute('INSERT OR IGNORE INTO cc (value) VALUES (?)', (cc,))
                cc_id = cursor.execute('SELECT id FROM cc WHERE value = ?', (cc,)).fetchone()['id']
                cursor.execute('INSERT OR IGNORE INTO requestor (value) VALUES (?)', (requestor,))
                requestor_id = cursor.execute('SELECT id FROM requestor WHERE value = ?', (requestor,)).fetchone()['id']

                # store timelines
                if record_type in ['ipv4', 'ipv6']:
                    timeline_stat_inetnum(cursor, filepath, data_date, date_registry, value, int(record[4]), record_type, status_id, requestor_id, cc_id)
                elif record_type == 'asn':
                    timeline_stat_asn(cursor, filepath, data_date, date_registry, int(value), status_id, requestor_id, cc_id)
                nb += 1

        conn.commit()
        print(f'Processed {nb} records')

    conn.close()

def _timeline_transfer_inetnum(cursor: sqlite3.Cursor, filepath: str, data_date: str, date_registry: str, old_value_id: int, new_value_id: int, inetnums: list):
    for inetnum in inetnums:
        
        ip_start = inetnum['start_address']
        ip_end = inetnum['end_address']
        if ip_start is None or ip_end is None:
            continue
        if '.' in ip_start:
            ip_start = '.'.join([str(int(i)) for i in inetnum['start_address'].split('.')])
        ip_start = ipaddress.ip_address(ip_start)
        if '.' in ip_end:
            ip_end = '.'.join([str(int(i)) for i in inetnum['end_address'].split('.')])
        ip_end = ipaddress.ip_address(ip_end)
        network = list(ipaddress.summarize_address_range(ip_start, ip_end))[0]
        ip_type = 'ipv4' if network.version == 4 else 'ipv6'

        # store inetnum
        cursor.execute('INSERT OR IGNORE INTO inetnum (value, ip_type, cidr) VALUES (?, ?, ?)', (network.compressed, ip_type, network.prefixlen))
        inetnum_id = cursor.execute('SELECT id FROM inetnum WHERE value = ?', (network.compressed,)).fetchone()['id']

        # update timeline
        cursor.execute((
            'INSERT OR IGNORE INTO timeline_inetnum (date_download, date_registry, change_type, inetnum_id, old_value, new_value, source) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)'
        ), (data_date, date_registry, 'org', inetnum_id, str(old_value_id), str(new_value_id), filepath))

def _timeline_transfer_asn(cursor: sqlite3.Cursor, filepath: str, data_date: str, date_registry: str, old_value_id: int, new_value_id: int, asns: list):
    for asn_block in asns:
        asn_start = int(asn_block['start'])
        asn_end = int(asn_block['end'])

        for asn in range(asn_start, asn_end + 1):
            # update timeline
            cursor.execute((
                'INSERT OR IGNORE INTO timeline_asn (date_download, date_registry, change_type, asn, old_value, new_value, source) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)'
            ), (data_date, date_registry, 'org', asn, str(old_value_id), str(new_value_id), filepath))

def _store_transfer_org(cursor: sqlite3.Cursor, org: str):
    if org is None:
        org = ''
    org = ''.join([c for c in org.lower() if c.isprintable()])
    cursor.execute('INSERT OR IGNORE INTO org (value) VALUES (?)', (org,))
    org_id = cursor.execute('SELECT id FROM org WHERE value = ?', (org,)).fetchone()['id']

    return org_id

def _process_transfer_files(db_path: str, data_path: str, data_date: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    for filename in os.listdir(data_path):
        filepath = os.path.join(data_path, filename)
        print(f'Parsing {filepath}')
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
 
            registry_date = transfer['transfer_date'].replace('-', '').replace('T', ' ').split(' ')[0]
            src_org_id = _store_transfer_org(cursor, transfer['source_organization']['name'])
            dst_org_id = _store_transfer_org(cursor, transfer['recipient_organization']['name'])

            # src org = dest org is not a transfer
            if src_org_id == dst_org_id:
                continue

            for inet in ['ip4nets', 'ip6nets']:
                if inet in transfer:
                    inetnums = transfer[inet]
                    if isinstance(inetnums, list) and len(inetnums) > 0: 
                        inetnums = inetnums[0]['transfer_set']
                    if isinstance(inetnums, dict):
                        inetnums = inetnums['transfer_set']
                    _timeline_transfer_inetnum(cursor, filepath, data_date, registry_date, src_org_id, dst_org_id, inetnums)
                    nb += len(inetnums)
            
            if 'asns' in transfer:
                asns = transfer['asns']
                if isinstance(asns, list) and len(asns) > 0:
                    asns = asns[0]
                if isinstance(asns, dict):
                    asns = asns['transfer_set']
                _timeline_transfer_asn(cursor, filepath, data_date, registry_date, src_org_id, dst_org_id, asns)
                nb += len(asns)
        conn.commit()
        print(f'Processed {nb} transfers')
    conn.close()

def _process_ip2asn_files(db_path: str, data_path: str, data_date: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    for filename in os.listdir(data_path):
        filepath = os.path.join(data_path, filename)
        print(f'Parsing {filepath}')

        nb = 0
        with gzip.open(filepath, mode='rt', encoding='utf8') as fp:
            reader = csv.DictReader(fp, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                if row['asn'] == '':
                    continue

                if nb > 0 and nb % 500000 == 0:
                    conn.commit()
                    print(f'Processed {nb} records')

                inetnum = ipaddress.ip_network(row['network'], strict=False)
                # cc = row['country_code']
                asn = str(row['asn'][2:])

                # store attributes
                cursor.execute('INSERT OR IGNORE INTO inetnum (value, ip_type, cidr) VALUES (?, ?, ?)', (inetnum.compressed, f'ipv{inetnum.version}', inetnum.prefixlen))
                inetnum_id = cursor.execute('SELECT id FROM inetnum WHERE value = ?', (inetnum.compressed,)).fetchone()['id']

                # timeline_inetnum
                last_event = cursor.execute("SELECT * FROM timeline_inetnum WHERE inetnum_id=? AND change_type='asn' ORDER BY id DESC LIMIT 1", (inetnum_id,)).fetchone()
                if last_event is None or last_event['new_value'] != asn:
                    old_value = last_event['new_value'] if last_event is not None else ''
                    cursor.execute((
                        'INSERT OR IGNORE INTO timeline_inetnum (date_download, date_registry, change_type, inetnum_id, old_value, new_value, source) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?)'
                    ), (data_date, data_date, 'asn', inetnum_id, old_value, asn, filepath))

                nb += 1
        conn.commit()
        print(f'Processed {nb} records')
    conn.close()

def _process_asn_files(db_path: str, data_path: str, data_date: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    for filename in os.listdir(data_path):
        filepath = os.path.join(data_path, filename)
        print(f'Parsing {filepath}')

        nb = 0
        with open(filepath, mode='r', encoding='utf8') as fp:
            lines = fp.read().splitlines()
        for line in lines:
            if nb > 0 and nb % 10000 == 0:
                conn.commit()
                print(f'Processed {nb} records')

            # parse record
            record = line.split(' ')
            asn = int(record[0])
            aso_cc = ' '.join(record[1:]).split(',')
            aso = ','.join(aso_cc[:-1]).strip()
            cc = aso_cc[-1].strip()

            # store attributes
            cursor.execute('INSERT OR IGNORE INTO aso (value) VALUES (?)', (aso,))
            aso_id = cursor.execute('SELECT id FROM aso WHERE value = ?', (aso,)).fetchone()['id']
            cursor.execute('INSERT OR IGNORE INTO cc (value) VALUES (?)', (cc,))
            cc_id = cursor.execute('SELECT id FROM cc WHERE value = ?', (cc,)).fetchone()['id']

            # timeline_asn
            for change_type, new_value in zip(['cc', 'aso'], [cc_id, aso_id]):
                last_event = cursor.execute("SELECT * FROM timeline_asn WHERE asn=? AND change_type=? ORDER BY id DESC LIMIT 1", (asn, change_type)).fetchone()

                if last_event is None or last_event['new_value'] != str(new_value):
                    old_value = last_event['new_value'] if last_event is not None else ''
                    cursor.execute((
                        'INSERT OR IGNORE INTO timeline_asn (date_download, date_registry, change_type, asn, old_value, new_value, source) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?)'
                    ), (data_date, data_date, change_type, asn, old_value, new_value, filepath))
            nb += 1
        conn.commit()
        print(f'Processed {nb} records')
    conn.close()


def store_timelines(db_path: str, data_path: str, data_date: str):
    _process_stat_files(db_path, os.path.join(data_path, 'stats', data_date), data_date)
    _process_transfer_files(db_path, os.path.join(data_path, 'transfers', data_date), data_date)
    _process_ip2asn_files(db_path, os.path.join(data_path, 'ip2asn', data_date), data_date)
    _process_asn_files(db_path, os.path.join(data_path, 'asn', data_date), data_date)

if __name__ == '__main__':
    data_date = sys.argv[1]
    db_path = os.path.join('.', 'db', 'vizir.sqlite3')
    db_schema = os.path.join('.', 'db', 'schema.sql')
    data_path = os.path.join('.', 'data')

    create_schema(db_path, db_schema)
    store_timelines(db_path, data_path, data_date)
