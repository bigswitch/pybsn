#!/usr/bin/env python
import pybsn
import argparse

parser = argparse.ArgumentParser(description='Add a switch')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

parser.add_argument('name', help='Switch name')
parser.add_argument('dpid', help='Switch DPID')
parser.add_argument('--fabric-role', help='Fabric role', choices=['leaf', 'spine'])
parser.add_argument('--leaf-group', help='Leaf group')

args = parser.parse_args()

bcf = pybsn.connect(args.host, args.user, args.password)
bcf.root.core.switch_config.put({
    'name': args.name,
    'dpid': args.dpid,
    'fabric-role': args.fabric_role,
    'leaf-group': args.leaf_group,
})
