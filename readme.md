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

[+] Changes seen on 20250420 (55 found)
└── 4.0.0.0/8 ({'org': 'level 3 communications, inc.->level 3 parent, llc'})
    ├── 4.128.0.0/12 ({'org': 'level 3 parent, llc->microsoft corporation'})
    ├── 4.144.0.0/12 ({'org': 'level 3 parent, llc->microsoft corporation'})
    ├── 4.160.0.0/12 ({'org': 'level 3 parent, llc->microsoft corporation'})
    ├── 4.176.0.0/12 ({'org': 'level 3 parent, llc->microsoft corporation'})
    ├── 4.192.0.0/12 ({'org': 'level 3 parent, llc->microsoft corporation'})
    ├── 4.208.0.0/12 ({'org': 'level 3 parent, llc->microsoft corporation'})
    ├── 4.224.0.0/12 ({'org': 'level 3 parent, llc->microsoft corporation'})
    └── 4.240.0.0/12 ({'org': 'level 3 parent, llc->microsoft corporation'})

└── 56.16.0.0/12 (is parent since 20250617)
    ├── 56.16.0.0/15 (is parent since 20250420, and has last change on 20250420 concerning cc)
    │   ├── 56.16.0.0/16 ({'org': 'united states postal service.->amazon.com, inc.'})
    │   └── 56.17.0.0/16 ({'org': 'united states postal service.->amazon.com, inc.'})
    ├── 56.18.0.0/16 ({'org': 'united states postal service->amazon.com, inc.'})
    ├── 56.19.0.0/16 ({'org': 'united states postal service.->amazon.com, inc.'})
    ├── 56.20.0.0/14 (is parent since 20250420, and has last change on 20250420 concerning cc)
    │   ├── 56.20.0.0/16 ({'org': 'united states postal service->amazon.com, inc.'})
    │   ├── 56.21.0.0/16 ({'org': 'united states postal service->amazon.com, inc.'})
    │   ├── 56.22.0.0/16 ({'org': 'united states postal service->amazon.com, inc.'})
    │   └── 56.23.0.0/16 ({'org': 'united states postal service->amazon.com, inc.'})

[... truncated ...]

{'asn': 14730, 'org': 'cavalier telephone->windstream communications llc'}
{'asn': 16810, 'org': 'cavalier telephone->windstream communications llc'}

[... truncated ...]

```

The output indicates that:
- 86.33% of the IPv4 space is allocated by IANA, and almost 90% of it is in use
- 0.2% of the IPv6 space is allocated by IANA, and the entirety is in use
- LEVEL 3 sold a bunch of `/12` to Microsoft
- a bunch of /16 were transfered from US Postal to Amazon
- Windstream did some cleaning and renamed the AS they used for "Cavalier Telephone"

# Example 2
```
$ python analyze.py --date 20250623

[+] Changes seen on 20250623 (2641 found)
└── 160.223.180.0/23 ({'status': 'allocated->assigned', 'requestor': 'cc429e8b49be2ee3e7c00f5fd3e11a41->49a468ab-35f7-461f-a4e6-a97eaaa79dd9', 'cc': 'CA->FR', 'org': 'bombardier inc.->alstom transport sa'})
└── 160.223.202.0/24 ({'status': 'allocated->assigned', 'requestor': 'cc429e8b49be2ee3e7c00f5fd3e11a41->af91326f-50d4-4e50-b00b-528900f858aa', 'cc': 'CA->FR', 'org': 'bombardier inc.->alstom transport sa'})

[ ... truncated ...]

└── 2.92.0.0/14 (is parent since 20250623, and has last change on 20250621 concerning requestor)
    ├── 2.94.216.0/21 ({'asn': 'n/a->8402'})
    └── 2.94.224.0/23 (is parent since 20250623, and has last change on 20250617 concerning asn)
        ├── 2.94.224.0/24 ({'asn': 'n/a->8402'})
        └── 2.94.225.0/24 ({'asn': 'n/a->3216'})


```

The output indicates that 
- 2 ranges were transfered from Bombardier to Alstom, probably some "cleaning" after they acquired Bombardier years ago.
- The AS 8402 (Univerisity of North Florida) sold/leased/released a /24 to a third party which is now announced by AS3216 (TEXTRON)