#!/usr/bin/env python
import pybsn
import argparse
from enchant.checker import SpellChecker

parser = argparse.ArgumentParser(description='Check spelling of schema descriptions')

parser.add_argument('path', type=str, default='controller', nargs='?')
parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

args = parser.parse_args()

bcf = pybsn.connect(args.host, args.user, args.password)

names = []
descriptions = []

def traverse(node):
    if 'name' in node:
        names.append(node['name'])

    if 'description' in node:
        descriptions.append(node['description'])

    if node['nodeType'] == 'CONTAINER' or node['nodeType'] == 'LIST_ELEMENT':
        for child_name, child in node['childNodes'].items():
            traverse(child)
    elif node['nodeType'] == 'LIST':
        traverse(node['listElementSchemaNode'])

traverse(bcf.root.schema())

chkr = SpellChecker("en_US")
chkr.set_text(' '.join(names).lower())
name_errors = set()
for err in chkr:
    name_errors.add(chkr.word)

description_errors = set()
chkr.set_text(' '.join(descriptions).lower())
for err in chkr:
    if chkr.word not in name_errors:
        description_errors.add(chkr.word)

for word in sorted(description_errors):
    print word
