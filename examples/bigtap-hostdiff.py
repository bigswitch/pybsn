#!/usr/bin/env python
import pybsn
import argparse
import os
import pickle
import socket
from collections import namedtuple

Host = namedtuple("Host", ["ip", "mac", "hostname"])

FILENAME = "/tmp/bigtap-hostdiff.data"
TMP_FILENAME = FILENAME + ".tmp"

parser = argparse.ArgumentParser(description='Show difference between previous and current set of tracked hosts')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

args = parser.parse_args()

bt = pybsn.connect(args.host, args.user, args.password)
hosts = bt.root.applications.bigtap.tracked_host()

new_data = []
import random
for host in hosts:
    new_data.append(Host(
        ip=host['ip-addr'],
        mac=host['mac-addr'],
        hostname=host['host-name']))
new_data.sort()

if os.path.exists(FILENAME):
    with open(FILENAME) as f:
        old_data = pickle.load(f)
else:
    old_data = []

old_set = set(old_data)
new_set = set(new_data)

deleted_hosts = []
for host in old_data:
    if not host in new_set:
        deleted_hosts.append(host)

added_hosts = []
for host in new_data:
    if not host in old_set:
        added_hosts.append(host)

def ip_sort_key(host):
    return socket.inet_aton(host.ip)

diff_hosts = sorted(deleted_hosts + added_hosts, key=ip_sort_key)
for host in diff_hosts:
    mark = host in new_set and '+' or '-'
    print "%s %-15s %s %s" % (mark, host.ip, host.mac, host.hostname)

with open(TMP_FILENAME, "w") as f:
    pickle.dump(new_data, f)

os.rename(TMP_FILENAME, FILENAME)
