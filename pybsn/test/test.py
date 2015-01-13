#!/usr/bin/env python
import unittest
from nose.tools import with_setup
import responses
import requests
import json

PREFIX = "/api/v1/data/"

@responses.activate

def mock_leaf_response(leaf_node, path):

    type_schema_node = leaf_node['typeSchemaNode']
    node_type = type_schema_node['leafType']

    if node_type == 'STRING':
        body = "string"

    responses.add(responses.GET, PREFIX + path,
              body=body, status=200,
              content_type='application/json')

def traverse(node, path="controller"):
    if node['nodeType'] == 'CONTAINER' or node['nodeType'] == 'LIST_ELEMENT':
        for child in node['childNodes']:
            traverse(child)
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

def load_schema():
    json_data=open('schema')
    node = json.load(json_data)
    json_data.close()

    traverse(node)


class BigDBClientTest(unittest.TestCase):

    def setUp(self):
        load_schema()

    def test_client(self):
        print "testing"