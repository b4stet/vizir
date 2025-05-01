CREATE TABLE transfers (
    date text,
    block_id int,
    asn_id int,
    transfer_type text,
    src_org_id int,
    dst_org_id int,
    source_filepath text,
    UNIQUE(block_id, transfer_type, asn_id, src_org_id, dst_org_id, date)
);

CREATE TABLE asns (
    id integer primary key,
    asn int,
    UNIQUE(asn)
);

CREATE TABLE orgs (
    id integer primary key,
    org text,
    UNIQUE(org)
);
