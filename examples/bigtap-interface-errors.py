#!/usr/bin/env python
import pybsn
import argparse
import re

parser = argparse.ArgumentParser(description='Show interfaces with errors')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

args = parser.parse_args()

bt = pybsn.connect(args.host, args.user, args.password)
topology = bt.root.applications.bigtap.topology

interfaces = []
for interface_type in ['core', 'filter', 'delivery', 'service']:
    for interface in topology[interface_type + '-interface']():
        interface['type'] = interface_type
        interfaces.append(interface)

switches_by_dpid = {}
for switch in bt.root.core.switch():
    switches_by_dpid[switch['dpid']] = switch

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split('(\d+)', text) ]

def sort_key(interface):
    return (interface['switch'], natural_keys(interface['interface']))

for interface in sorted(interfaces, key=sort_key):
    if interface['count-rx-error'] > 0 or interface['count-xmit-error'] > 0:
        direction = interface['direction'] == "rx" and "<-" or "->"
        if interface['switch'] in switches_by_dpid:
            switch_name = switches_by_dpid[interface['switch']]['alias']
        else:
            switch_name = interface['switch']
        print switch_name, interface['interface'], interface['type'], direction, interface['peer']
        for k, v in interface.items():
            if re.match(r'count.*error', k) and v > 0:
                print "  %s: %u" % (k, v)
