#!/usr/bin/env python
"""
Add static endpoints from a CSV file

CSV columns:
    tenant
    segment
    name
    mac
    switch
    interface
    vlan

This example is simplistic in that it only supports specifying the attachment
point with switch+interface+vlan.
"""
import pybsn
import argparse
import csv
from collections import defaultdict

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('path', type=file, help="CSV file")
parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

args = parser.parse_args()

bcf = pybsn.connect(args.host, args.user, args.password)

# (tenant, segment) -> [endpoint]
endpoints_by_segment = defaultdict(list)

for row in csv.reader(args.path):
    tenant, segment, name, mac, switch, interface, vlan = row
    endpoints_by_segment[(tenant, segment)].append({
        'name': name,
        'mac': mac,
        'attachment-point': {
            'switch': switch,
            'interface': interface,
            'vlan': vlan,
        }
    })

for ((tenant, segment), endpoints) in sorted(endpoints_by_segment.items()):
    print "Adding %d static endpoints to tenant %s segment %s" % (len(endpoints), tenant, segment)
    bcf.root.applications.bcf.tenant.match(name=tenant).segment.match(name=segment).endpoint.put(endpoints)
