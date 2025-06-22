CREATE TABLE inetnum (
    id integer primary key,
    value text,
    ip_type text,
    cidr int,
    UNIQUE(value)
);

CREATE TABLE aso (
    id integer primary key,
    value text,
    UNIQUE(value)
);

CREATE TABLE org (
    id integer primary key,
    value text,
    UNIQUE(value)
);

CREATE TABLE requestor (
    id integer primary key,
    value text,
    UNIQUE(value)
);

CREATE TABLE status (
    id integer primary key,
    value text,
    UNIQUE(value)
);

INSERT INTO status (id, value) VALUES (1, 'allocated');
INSERT INTO status (id, value) VALUES (2, 'assigned');
INSERT INTO status (id, value) VALUES (3, 'available');
INSERT INTO status (id, value) VALUES (4, 'reserved');

CREATE TABLE cc (
    id integer primary key,
    value text,
    UNIQUE(value)
);

CREATE TABLE inetnum2supernet (
    inetnum_id int,
    supernet_inetnum_id int,
    first_seen text,
    UNIQUE(inetnum_id, supernet_inetnum_id)
);

CREATE TABLE requestor2org (
    requestor_id int,
    org_id int,
    UNIQUE(requestor_id, org_id)
);

CREATE TABLE timeline_inetnum (
    id integer primary key,
    date_download text,
    date_registry text,
    change_type text,
    inetnum_id int,
    old_value text,
    new_value text,
    source text,
    UNIQUE(date_registry, change_type, inetnum_id, old_value, new_value)
);
CREATE index idx_timeline_inetnum_id_change_type on timeline_inetnum(inetnum_id, change_type);


CREATE TABLE timeline_asn (
    id integer primary key,
    date_download text,
    date_registry text,
    change_type text,
    asn int,
    old_value text,
    new_value text,
    source text,
    UNIQUE(date_registry, change_type, asn, old_value, new_value)
);
CREATE index idx_timeline_asn_change_type on timeline_asn(asn, change_type);
