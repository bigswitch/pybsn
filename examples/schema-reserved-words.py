# Check for words or syntax in schema names that collide with names used by pybcf
import pybsn
import argparse
import sys

parser = argparse.ArgumentParser(description='Check for use of reserved names in the schema')

parser.add_argument('path', type=str, default='controller', nargs='?')
parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

args = parser.parse_args()

bcf = pybsn.connect(args.host, args.user, args.password)

blacklist = set(dir(bcf.root))
seen = set()
failed = False

def traverse(node):
    name = 'name' in node and node.name or None
    if name and name not in seen:
        seen.add(name)
        if name in blacklist or '_' in name:
            print name
            failed = True

    if node.nodeType == 'CONTAINER' or node.nodeType == 'LIST_ELEMENT':
        for child_name in node.childNodes:
            traverse(getattr(node.childNodes, child_name))
    elif node.nodeType == 'LIST':
        traverse(node.listElementSchemaNode)

traverse(bcf.schema('controller'))

if failed:
    sys.exit(1)
