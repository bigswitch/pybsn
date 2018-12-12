#!/usr/bin/env python
import pybsn
import argparse

parser = argparse.ArgumentParser(description='Generate and download a support bundle')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

parser.add_argument('--output', '-o', help="Output filename")

args = parser.parse_args()

bcf = pybsn.connect(args.host, args.user, args.password)

print "Generating..."
reply = root.support.generate_bundle.rpc()
print "Downloading..."
name = args.output or reply['name']
with open(name, "w") as f:
    r = bcf.session.get(bcf.url + reply['url-path'], stream=True)
    r.raise_for_status()
    for chunk in r.iter_content(4096):
        f.write(chunk)
print "Support bundle left in", name
