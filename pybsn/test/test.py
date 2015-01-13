#!/usr/bin/env python
# coding: interpy
import unittest
from nose.tools import with_setup
import responses
import requests
import json
import random

PREFIX = "/api/v1/data/"

@responses.activate

#TODO: Find a sexier way to mock up response types in accordanance with validations
def mock_leaf_response(leaf_node, path):

    type_schema_node = leaf_node['typeSchemaNode']
    node_type = type_schema_node['leafType']

    body = "{\"#{leaf_node['name']}\":"
    if node_type == 'STRING':
        body += '"string"}'
    elif node_type == 'BOOLEAN':
        body += 'false}'
    elif node_type == 'INTEGER':
        body += '1}'
    elif node_type == 'ENUMERATION':
        # Will there ever be more than one type validator?
        enums = type_schema_node['typeValidator'][0]['names'].keys()
        enum = random.choice(enums)
        body += "\"#{enum}\"}"
    else:
        print "Missing node_type #{node_type}"

    print body
    responses.add(responses.GET, PREFIX + path,
              body=body, status=200,
              content_type='application/json')

def traverse(node, path="controller"):

    if type(node) is dict:
        if node['nodeType'] == 'CONTAINER' or node['nodeType'] == 'LIST_ELEMENT':
            for child in node['childNodes']:
                traverse(node['childNodes'][child])
        elif node['nodeType'] == 'LIST':
            traverse(node['listElementSchemaNode'])
        elif node['nodeType'] == 'LEAF':
            path += "/" + node['name']
            mock_leaf_response(node, path)
        elif node['nodeType'] == 'LEAF_LIST':
            pass
            # do stuff
        else:
            assert False, "unknown node type %s" % node['nodeType']
    else:
        print node

def load_schema():
    json_data=open('schema')
    root_node = json.load(json_data)
    json_data.close()

    traverse(root_node)


class BigDBClientTest(unittest.TestCase):

    def setUp(self):
        load_schema()

    def test_client(self):
        print "testing"