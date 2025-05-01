import sys
import os
import sqlite3
import ipaddress


def create_schema_stats(db_path: str, db_schema: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    table_exists = cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="ip_blocks"').fetchone()
    if table_exists:
        print('Table ip_blocks already exists')
        return

    print(f'Creating ip_blocks table according to {db_schema}')
    with open(db_schema, mode='r', encoding='utf8') as fp:
        cursor.executescript(fp.read())
    conn.close()

def store_stats(db_path: str, files_path: str, date: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    blocks = {}
    for filename in os.listdir(files_path):
        print(f'Parsing {filename}')
        filepath = os.path.join(files_path, filename)
        with open(filepath, mode='r', encoding='utf8') as fp:
            nb = 0
            for line in fp:
                line = line.strip('\n')
                if nb > 0 and nb % 10000 == 0:
                    conn.commit()
                    print(f'Processed {nb} records')

                # filter on IP records
                if '|ipv' not in line or '|summary' in line:
                    continue

                # parse record
                record = line.split('|')
                rir = record[0]
                country = record[1]
                ip_type = record[2]
                ip_start = ipaddress.ip_address(record[3])

                if ip_type == 'ipv4':
                    ip_end = ip_start + int(record[4]) - 1
                    net_block = list(ipaddress.summarize_address_range(ip_start, ip_end))[0]
                elif ip_type == 'ipv6':
                    net_block = ipaddress.ip_network(ip_start.compressed + '/' + record[4], strict=False)

                blocks[net_block.compressed] = {'ip_start_int': int(net_block[0]), 'ip_end_int': int(net_block[-1])}
                nb_ips = net_block.num_addresses
                cidr = net_block.prefixlen
                record_date = record[5]
                status = record[6]
                requestor = record[7] if len(record) > 7 else ''

                # store attributes
                rir_id = cursor.execute('SELECT id FROM rirs WHERE rir = ?', (rir,)).fetchone()['id']
                status_id = cursor.execute('SELECT id FROM statuses WHERE status = ?', (status,)).fetchone()['id']

                cursor.execute('INSERT OR IGNORE INTO country_codes (cc) VALUES (?)', (country,))
                country_id = cursor.execute('SELECT id FROM country_codes WHERE cc = ?', (country,)).fetchone()['id']

                cursor.execute('INSERT OR IGNORE INTO requestors (requestor) VALUES (?)', (requestor,))
                requestor_id = cursor.execute('SELECT id FROM requestors WHERE requestor = ?', (requestor,)).fetchone()['id']

                cursor.execute((
                    'INSERT OR IGNORE INTO ip_blocks (block, cidr, nb_ips, ip_type, ip_start, ip_end) '
                    'VALUES (?, ?, ?, ?, ?, ?)'
                ), (net_block.compressed, cidr, str(nb_ips), ip_type, net_block[0].compressed, net_block[-1].compressed))
                block_id = cursor.execute('SELECT id FROM ip_blocks WHERE block = ?', (net_block.compressed,)).fetchone()['id']

                # store timeline
                cursor.execute((
                    'INSERT OR IGNORE INTO timeline (date, block_id, rir_id, requestor_id, status_id, cc_id, record_date, source_filepath) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
                ), (date, block_id, rir_id, requestor_id, status_id, country_id, record_date, filepath))
                                
                nb += 1

            conn.commit()
            print(f'Processed {nb} records')

    conn.close()

if __name__ == '__main__':
    date = sys.argv[1]
    data_path = os.path.join('.', 'data', 'stats', date)
    db_path = os.path.join('.', 'db', 'vizir.sqlite3')
    db_schema = os.path.join('.', 'db', 'schema_stats.sql')

    create_schema_stats(db_path, db_schema)
    store_stats(db_path, data_path, date)

