import json
import os
import logging
import re
import unittest
from unittest.mock import Mock

import requests

import pybsn
import responses

my_dir = os.path.dirname(__file__)

PARAMS = {'state-type': 'global-config'}

class TestNode(unittest.TestCase):
    def setUp(self):
        self.client = Mock(spec_set=pybsn.BigDbClient)
        self.root = pybsn.Node("controller", self.client)

    def test_getattr(self):
        node = self.root.core.switch_config
        self.assertEqual(node._path, "controller/core/switch-config")

    def test_getitem(self):
        node = self.root["core"]["switch-config"]
        self.assertEqual(node._path, "controller/core/switch-config")

    def test_root_get(self):
        self.client.get.return_value = dict(foo="bar")
        self.assertEqual(self.root.get(), dict(foo="bar"))
        self.client.get.assert_called_with("controller", None)

    def test_root_get_with_params(self):
        self.client.get.return_value = dict(foo="bar")
        self.assertEqual(self.root.get(params=PARAMS), dict(foo="bar"))
        self.client.get.assert_called_with("controller", PARAMS)

    def test_root_post(self):
        self.root.post(data=dict(foo="bar"))
        self.client.post.assert_called_with("controller", dict(foo="bar"), None)

    def test_root_post_with_params(self):
        self.root.post(data=dict(foo="bar"), params=PARAMS)
        self.client.post.assert_called_with("controller", dict(foo="bar"), PARAMS)

    def test_root_put(self):
        self.root.put(data=dict(foo="bar"))
        self.client.put.assert_called_with("controller", dict(foo="bar"), None)

    def test_root_put_with_params(self):
        self.root.put(data=dict(foo="bar"), params=PARAMS)
        self.client.put.assert_called_with("controller", dict(foo="bar"), PARAMS)

    def test_root_patch(self):
        self.root.patch(data=dict(foo="bar"))
        self.client.patch.assert_called_with("controller", dict(foo="bar"), None)

    def test_root_patch_with_params(self):
        self.root.patch(data=dict(foo="bar"), params=PARAMS)
        self.client.patch.assert_called_with("controller", dict(foo="bar"), PARAMS)

    def test_root_delete(self):
        self.root.delete()
        self.client.delete.assert_called_with("controller", params=None)

    def test_root_delete_with_params(self):
        self.root.delete(params=PARAMS)
        self.client.delete.assert_called_with("controller", params=PARAMS)

    def test_root_schema(self):
        self.client.schema.return_value = dict(foo="bar")
        ret = self.root.schema()
        self.assertEqual(ret, dict(foo="bar"))
        self.client.schema.assert_called_with("controller")

    def test_rpc(self):
        self.client.rpc.return_value = dict(foo="bar")
        ret = self.root.core.aaa.test.rpc(dict(input="foo"))

        self.assertEqual(ret, dict(foo="bar"))
        self.client.rpc.assert_called_with("controller/core/aaa/test",
            dict(input="foo"), None)

    def test_rpc_params(self):
        self.client.rpc.return_value = dict(foo="bar")
        ret = self.root.core.aaa.test.rpc(dict(input="foo"), params={'initiate-async-id': 'asyncId'})

        self.assertEqual(ret, dict(foo="bar"))
        self.client.rpc.assert_called_with("controller/core/aaa/test",
            dict(input="foo"), {'initiate-async-id': 'asyncId'})

    def test_match(self):
        self.client.rpc.return_value = dict(foo="bar")
        node = self.root.node
        self.assertEqual(node.match()._path, "controller/node")
        self.assertEqual(node.match(a="foo")._path, "controller/node[a='foo']")
        self.assertIn(
            node.match(a="foo", b=2)._path,
             ("controller/node[a='foo'][b=2]",
              # in py<3.7 dictionaries are not yet ordered; can remove when requiring py3.7
              "controller/node[b=2][a='foo']" )
        )

    def test_filter(self):
        self.client.rpc.return_value = dict(foo="bar")
        node = self.root.node
        self.assertEqual(node.filter("a='foo'")._path, "controller/node[a='foo']")
        self.assertEqual(node.filter("a=$x", x="foo")._path, "controller/node[a='foo']")
        self.assertEqual(node.filter("b=$x", x=1)._path, "controller/node[b=1]")

    def test_root_call(self):
        self.client.get.return_value = dict(foo="bar")
        self.assertEqual(self.root(), dict(foo="bar"))
        self.client.get.assert_called_with("controller", None)
