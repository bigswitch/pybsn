import pybcf
import argparse

parser = argparse.ArgumentParser(description='Add a static endpoint')

parser.add_argument('path', type=str, default='controller', nargs='?')
parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

parser.add_argument("--max-depth", "-d", type=int, help="Maximum recursion depth")

args = parser.parse_args()

bcf = pybcf.BCF("http://%s:8080" % args.host, args.user, args.password)

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
        if True:
            output(name, ":", node['leafType'].lower())
    elif node['nodeType'] == 'LEAF_LIST':
        output(name, ":", "list of", node['leafSchemaNode']['leafType'].lower())
    else:
        assert False, "unknown node type %s" % node['nodeType']

path = args.path.replace('.', '/').replace('_', '-')
traverse(bcf.schema(path), name=path)
