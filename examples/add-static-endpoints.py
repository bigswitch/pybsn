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
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import pybsn

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("path", type=Path, help="CSV file")
parser.add_argument("--host", "-H", type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument("--user", "-u", type=str, default="admin", help="Username")
parser.add_argument("--password", "-p", type=str, default="adminadmin", help="Password")

args = parser.parse_args()

bcf = pybsn.connect(args.host, args.user, args.password)

# (tenant, segment) -> [endpoint]
endpoints_by_segment = defaultdict(list)

with open(args.path) as f:
    for row in csv.reader(f):
        tenant, segment, name, mac, switch, interface, vlan = row
        endpoints_by_segment[(tenant, segment)].append(
            {
                "name": name,
                "mac": mac,
                "attachment-point": {
                    "switch": switch,
                    "interface": interface,
                    "vlan": vlan,
                },
            }
        )

for (tenant, segment), endpoints in sorted(endpoints_by_segment.items()):
    print(f"Adding {len(endpoints)} static endpoints to tenant {tenant} segment {segment}")
    bcf.root.applications.bcf.tenant.match(name=tenant).segment.match(name=segment).endpoint.put(endpoints)
