#!/usr/bin/env python
import pybsn
import argparse
import textwrap
import re
from IPython.config.loader import Config
from IPython.terminal.ipapp import TerminalIPythonApp
from IPython.core.inputtransformer import StatelessInputTransformer

parser = argparse.ArgumentParser(description='Start an IPython shell to interact with the REST API')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

args = parser.parse_args()

ctrl = pybsn.connect(args.host, args.user, args.password)

@StatelessInputTransformer.wrap
def LineTransformer(line):
    if line.endswith('#'):
        return "show_schema(%s)" % line[:-1]
    else:
        return line

def show_schema(root, max_depth=1, verbose=True):
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

        if max_depth is not None and depth > max_depth:
            return

        if verbose and 'description' in node:
            description = re.sub(r"\s+", " ", node['description'])
            indent = " "*(depth*2) + "  # "
            description = "\n" + textwrap.fill(
                description,
                initial_indent=indent,
                subsequent_indent=indent,
                width=70 - depth*2)
        else:
            description = ''

        if verbose:
            config = "config" in node['dataSources'] and "(config)" or ""
        else:
            config = ""

        if node['nodeType'] == 'CONTAINER' or node['nodeType'] == 'LIST_ELEMENT':
            if node['nodeType'] == 'CONTAINER':
                output(name, description)
            for child_name, child in node['childNodes'].items():
                traverse(child, depth+1, child_name)
        elif node['nodeType'] == 'LIST':
            output(name, "(list)", description)
            traverse(node['listElementSchemaNode'], depth, name)
        elif node['nodeType'] == 'LEAF':
            output(name, ":", pretty_type(node), config, description)
        elif node['nodeType'] == 'LEAF_LIST':
            output(name, ":", "list of", pretty_type(node['leafSchemaNode']), config, description)
        else:
            assert False, "unknown node type %s" % node['nodeType']

    traverse(root.schema(), name=root._path)

config = Config()
config.TerminalInteractiveShell.banner1 = """\
Available variables:
  - ctrl: BigDbClient instance
  - root: ctrl.root

Add '#' at the end of a line to show the schema for a pybsn Node.
"""
config.TerminalInteractiveShell.confirm_exit = False

user_ns = dict(ctrl=ctrl, root=ctrl.root, show_schema=show_schema)

app = TerminalIPythonApp(config=config)
app.initialize(argv=[])
app.shell.push(user_ns, interactive=False)
app.shell.input_transformer_manager.python_line_transforms.append(LineTransformer())
app.start()
