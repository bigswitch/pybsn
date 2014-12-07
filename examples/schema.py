import pybcf
import argparse
import json

parser = argparse.ArgumentParser(description='Add a static endpoint')

parser.add_argument('path', type=str, default='controller', nargs='?')
parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

parser.add_argument("--max-depth", "-d", type=int, help="Maximum recursion depth")
parser.add_argument("--raw", action="store_true", help="Print raw JSON")

args = parser.parse_args()

bcf = pybcf.BCF("http://%s:8080" % args.host, args.user, args.password)

def pretty_type(node):
    if not 'typeSchemaNode' in node:
        return node['leafType'].lower()

    t = node['typeSchemaNode']

    if t['leafType'] == 'ENUMERATION':
        names = [x for x in t['typeValidator'] if x['type'] == 'ENUMERATION_VALIDATOR'][0]['names']
        return "enum { %s }" % ', '.join(names)
    elif t['leafType'] == 'UNION':
        names = [x['name'] for x in t['typeSchemaNodes']]
        return "union { %s }" % ', '.join(names)
    else:
        return t['leafType'].lower()

def traverse(node, depth=0, name="root"):
    def output(*s):
        print " " * (depth * 2) + ' '.join(s)
    if args.max_depth is not None and depth > args.max_depth:
        return
    if node['nodeType'] == 'CONTAINER' or node['nodeType'] == 'LIST_ELEMENT':
        if node['nodeType'] == 'LIST_ELEMENT':
            output(name, "(list)")
        else:
            output(name)
        for child_name in node['childNodes']:
            child = node['childNodes'][child_name]
            traverse(child, depth+1, child_name)
    elif node['nodeType'] == 'LIST':
        traverse(node['listElementSchemaNode'], depth, name)
    elif node['nodeType'] == 'LEAF':
        output(name, ":", pretty_type(node))
    elif node['nodeType'] == 'LEAF_LIST':
        output(name, ":", "list of", pretty_type(node['leafSchemaNode']))
    else:
        assert False, "unknown node type %s" % node['nodeType']

path = args.path.replace('.', '/').replace('_', '-')

if args.raw:
    print json.dumps(bcf.schema(path), indent=4, cls=pybcf.BCFJSONEncoder)
else:
    traverse(bcf.schema(path), name=path)
