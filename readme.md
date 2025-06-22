# VIZIR: VIsualize Internet Registries

The Regional Internet Registries compiles every day files related to IP networks that build the Internet, in particular `stats` and `transfers`.  
The `transfers` indicates the source and destination organization when an ASN or IP block is transferred. 
The `stats` log any changes in the country, status or requestor of an IP block.   
This small project allows to download, store and visualize the last changes on a given day.  

To be effective, the data need to be downloaded and stored for several consecutive days using the script `vizir.py`.  
The date of a change is primarily the date the data was processed. 
Indeed, the date in `stats` and `transfers` files are not accurate, we can find changes between two consecutives days but the recorded date is by far earlier.  

Then the script `analyze.py` provides some insights:
- with `--coverage`, it shows the space of the IPv4 and IPv6 allocated
- with a date formatted as `%Y%m%d`, it shows IP blocks for which an attribute changed at that day (status, country or requestor ID)

The supernets are computed efficiently as a network tree using the sweep line algorithm.

# Example 1

```
$ python analyze.py --coverage --date 20250418

[+] IPv4 report coverage
Found 221 ipv4 networks allocated by IANA
Found 262185 ipv4 networks in DB (IANA allocation excluded)
Found 24 ipv4 networks in DB equal to IANA allocation
IANA allocated 3707764736 ipv4, 86.33% of the space
Found 6765 non-overlapping networks ipv4, accounting for 3321872938 ipv4, 89.59% of IANA allocation

[+] IPv6 report coverage
Found 34 ipv6 networks allocated by IANA
Found 369279 ipv6 networks in DB (IANA allocation excluded)
Found 0 ipv6 networks in DB equal to IANA allocation
IANA allocated 669116692824468607286019819925667840 ipv6, 0.20% of the space
Found 22 non-overlapping networks ipv6, accounting for 669116692825677533105634449100374016 ipv6, 100.00% of IANA allocation

[+] Changes seen on 20250418 (55 found)
└── 23.137.236.0/24 ({'cc': 'US', 'status': 'allocated', 'requestor': '5c811aaf62f2a2b277e1480ff6638610'})
└── 23.137.244.0/24 ({'cc': 'US', 'status': 'allocated', 'requestor': 'fae4e89c02f8f3de14daea814dd4800a'})
└── 23.138.4.0/24 ({'cc': 'US', 'status': 'allocated', 'requestor': 'f1393dadfccb4850d5990c8340c60cbc'})
└── 56.0.0.0/15 ({'type': 'parent info', 'cc': 'US', 'status': 'allocated', 'requestor': '7bfe7160b82a7801909804dfa050e3bb'})
    └── 56.1.0.0/16 ({'cc': 'US', 'status': 'allocated', 'requestor': '20c786e8edd815cc245070645e265298', 'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
└── 56.4.0.0/15 ({'cc': 'US', 'status': 'allocated', 'requestor': '20c786e8edd815cc245070645e265298'})
    ├── 56.4.0.0/16 ({'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
    └── 56.5.0.0/16 ({'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
└── 56.8.0.0/16 ({'cc': 'US', 'status': 'allocated', 'requestor': '20c786e8edd815cc245070645e265298', 'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
└── 56.12.0.0/16 ({'cc': 'US', 'status': 'allocated', 'requestor': '20c786e8edd815cc245070645e265298', 'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
└── 56.15.0.0/16 ({'cc': 'US', 'status': 'allocated', 'requestor': '20c786e8edd815cc245070645e265298', 'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
└── 56.18.0.0/16 ({'cc': 'US', 'status': 'allocated', 'requestor': '20c786e8edd815cc245070645e265298', 'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
└── 56.20.0.0/14 ({'cc': 'US', 'status': 'allocated', 'requestor': '20c786e8edd815cc245070645e265298'})
    ├── 56.20.0.0/16 ({'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
    ├── 56.21.0.0/16 ({'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
    ├── 56.22.0.0/16 ({'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})
    └── 56.23.0.0/16 ({'src_org': 'United States Postal Service', 'dst_org': 'Amazon.com, Inc.'})

[... truncated ...]
```

The output indicates that:
- 86.33% of the IPv4 space is allocated by IANA, and almost 90% of it is in use
- 0.2% of the IPv6 space is allocated by IANA, and the entirety is in use
- on April 18th, a bunch of /16 were transfered from US Postal to Amazon, but `allocated` means that not yet in use
- the ID `20c786e8edd815cc245070645e265298` in stats files is probably tight to Amazon
- the parent block `56.0.0.0/15` is probably not owned by Amazon (the requestor is different)
- the block `56.20.0.0/14` does not have any parent and is owned entirely by Amazon: it's a direct allocation by a RIR, there is no intermediary/reseller in between

# Example 2
```
$ python analyze.py --date 20250618

[+] Changes seen on 20250618 (2641 found)
└── 160.223.180.0/23 ({'status': 'allocated->assigned', 'requestor': 'cc429e8b49be2ee3e7c00f5fd3e11a41->49a468ab-35f7-461f-a4e6-a97eaaa79dd9', 'cc': 'CA->FR', 'org': 'bombardier inc.->alstom transport sa'})
└── 160.223.202.0/24 ({'status': 'allocated->assigned', 'requestor': 'cc429e8b49be2ee3e7c00f5fd3e11a41->af91326f-50d4-4e50-b00b-528900f858aa', 'cc': 'CA->FR', 'org': 'bombardier inc.->alstom transport sa'})

[ ... truncated ...]


```

The output indicates that 2 ranges were transfered from Bombardier to Alstom, probably some "cleaning" after they acquired Bombardier years ago.