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

The blocks are displayed efficiently as a network tree using the sweep line algorithm.

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
- the parent block `56.0.0.0/15` is not owned by Amazon (the requestor is different)
- the block `56.20.0.0/14` does not have any parent and is owned entirely by Amazon: it's a direct allocation by a RIR, there is no intermediary/reseller in between

# Example 2
```
$ python analyze.py --date 20250426

[+] Changes seen on 20250426 (2529 found)
└── 192.189.1.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': 'cca738c4-a27a-4e19-b732-7682d79c2438'})
└── 192.189.8.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': '5d046ab7-3e1b-4241-94cd-61b46840aafa'})
└── 192.189.9.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': '91d35573-7796-4a05-92b4-9bdfb3169ed1'})
└── 192.189.10.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': 'dd21ba8e-8a19-4187-8aba-7a58efbe32c0'})
└── 192.189.11.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': '928110ed-3e5a-459d-8b3c-423833e0a3b7'})
└── 192.189.23.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': '439defa7-a91f-49a1-8247-7000b8e5fb6e'})
└── 192.189.41.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': '802036cf-0474-41b5-a31b-4a8f2fd2aa32'})
└── 192.189.51.0/24 ({'cc': 'AT', 'status': 'assigned', 'requestor': '159b3f51-f0ba-4d84-a369-e330296359a4'})
└── 192.189.52.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': 'ffe78436-059f-4c44-86d0-ac151af76c31'})
└── 192.189.55.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': '7868a23a-d24e-4977-bb52-b6be47685256'})
└── 192.189.66.0/24 ({'cc': 'FR', 'status': 'assigned', 'requestor': '095d7670-987c-432c-8753-f6bbf0798b07'})
└── 192.189.69.0/24 ({'cc': 'GB', 'status': 'assigned', 'requestor': 'c4efff33-0763-4272-b523-b67f29f06470'})

[ ... truncated ...]

└── 185.8.116.0/22 ({'type': 'parent info', 'cc': 'DE', 'status': 'allocated', 'requestor': 'd6fa08ae-fb69-4083-9fdd-a6ecbd7545f2'})
    ├── 185.8.116.0/23 ({'cc': 'DE', 'status': 'allocated', 'requestor': 'd6fa08ae-fb69-4083-9fdd-a6ecbd7545f2'})
    └── 185.8.118.0/23 ({'cc': 'DE', 'status': 'allocated', 'requestor': '987a82ec-2877-4ba8-aa08-8d9acef01473'})
[ ... truncated ...]

└── 163.227.160.0/19 ({'type': 'parent info', 'cc': '', 'status': 'available', 'requestor': ''})
    ├── 163.227.160.0/23 ({'cc': 'VN', 'status': 'assigned', 'requestor': 'A92CDC65'})
    ├── 163.227.162.0/23 ({'cc': 'VN', 'status': 'assigned', 'requestor': 'A92A6EAD'})
    ├── 163.227.164.0/22 ({'cc': '', 'status': 'available', 'requestor': ''})
    ├── 163.227.168.0/21 ({'cc': '', 'status': 'available', 'requestor': ''})
    └── 163.227.176.0/20 ({'cc': '', 'status': 'available', 'requestor': ''})

```

The output indicates that:
- we don't have the information about orgs: the transfers are not consistent with the stats
- the block `185.8.116.0/22` was split: the requestor `d6fa08ae-fb69-4083-9fdd-a6ecbd7545f2` sold or leased the second `/23`
- the block `163.227.160.0/19` was entirely available, from which 2 `/23` were `assigned` to 2 different operators
- a bunch of small ranges got `allocated`: the requestor is the new owner
- a bunch of small ranges got `assigned` with many distinct requestors: the requestor is the new operator
- other got `reserved`: a local or regional registry blocked the availability of the IP block