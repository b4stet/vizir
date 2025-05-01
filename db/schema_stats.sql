CREATE TABLE ip_blocks (
    id integer primary key,
    block text,
    cidr int,
    nb_ips text,
    ip_type text,
    ip_start text,
    ip_end text,
    UNIQUE(block)
);

CREATE TABLE subnets (
    block_id int,
    is_subnet_of_block_id int,
    UNIQUE(block_id, is_subnet_of_block_id)
);


CREATE TABLE supernets (
    block_id int,
    is_supernet_of_block_id int,
    UNIQUE(block_id, is_supernet_of_block_id)
);

CREATE TABLE timeline (
    date text,
    block_id int,
    rir_id int,
    requestor_id int,
    status_id int,
    cc_id int,
    record_date text,
    source_filepath text,
    UNIQUE(block_id, rir_id, requestor_id, status_id, cc_id, record_date)
);

CREATE index idx_timeline_blocks on timeline(block_id);
CREATE index idx_timeline_requestors on timeline(requestor_id);

CREATE TABLE rirs (
    id integer primary key,
    rir text,
    UNIQUE(rir)
);

INSERT INTO rirs (id, rir) VALUES (1, 'afrinic');
INSERT INTO rirs (id, rir) VALUES (2, 'apnic');
INSERT INTO rirs (id, rir) VALUES (3, 'arin');
INSERT INTO rirs (id, rir) VALUES (4, 'lacnic');
INSERT INTO rirs (id, rir) VALUES (5, 'ripencc');

CREATE TABLE country_codes (
    id integer primary key,
    cc text,
    UNIQUE(cc)
);

CREATE TABLE statuses (
    id integer primary key,
    status text,
    UNIQUE(status)
);

INSERT INTO statuses (id, status) VALUES (1, 'allocated');
INSERT INTO statuses (id, status) VALUES (2, 'assigned');
INSERT INTO statuses (id, status) VALUES (3, 'available');
INSERT INTO statuses (id, status) VALUES (4, 'reserved');

CREATE TABLE requestors (
    id integer primary key,
    requestor text,
    UNIQUE(requestor)
);

