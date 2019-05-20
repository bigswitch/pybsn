import copy
import json
import logging
import os
import sys
import unittest
from contextlib import contextmanager

import responses
from pybsn.bcf.api import Api


pybsn_host = "http://127.0.0.1:8080"

my_dir = os.path.dirname(__file__)

logging.basicConfig()


@contextmanager
def responses_from_cassette(cassette):
    with responses.RequestsMock() as rsps:
        with open(os.path.join(my_dir, 'fixtures/cassettes/switch',cassette + ".json")) as file_:
            json_ = json.load(file_)

        def _handle_interaction_cb(req, interaction):
            if interaction["request"]["body"]["string"]:
                expected_req_body = json.loads(interaction["request"]["body"]["string"])
                assert json.loads(req.body) == expected_req_body

            return (interaction["response"]["status"]["code"], interaction["response"]["headers"],
                    interaction["response"]["body"]["string"])

        for h in json_["http_interactions"]:
            url = h["request"]["uri"].replace("<PYBSN_HOST>", pybsn_host)
            if sys.version_info < (3,0):
                # python2 hack - py2 quotes the square brackets, py3 does not
                url = url.replace("[", "%5B").replace("]", "%5D")
            method = h["request"]["method"]
            cb = lambda req, interaction=h: _handle_interaction_cb(req, interaction)
            rsps.add_callback(method, url,
                 callback = cb,
                 content_type = "application/json")

            print("registered callback %s %s" % (method, url))

        yield


class TestSwitch(unittest.TestCase):
    def setUp(self):
        self.api = Api('http://127.0.0.1:8080', "admin", "pass", login=False)

    def test_get_switches(self):
        with responses_from_cassette('get_switches'):
            switches = self.api.get_switches()

            assert len(switches) == 14

            for sw in switches:
                assert sw.name == None
                assert sw.dpid != None


    def test_get_switch_by_name(self):
        with responses_from_cassette('get_switch_by_name'):
            sw = self.api.get_switch_by_name("test")

            assert sw is not None
            assert sw.name == "test"

    def test_get_switch_by_name_fail(self):
        with responses_from_cassette('get_switch_by_name_fail'):
            sw = self.api.get_switch_by_name("test")

            assert sw is None

    def test_remove_switch_by_name(self):
        with responses_from_cassette('remove_switch_by_name'):
            # Add a switch first
            self.api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

            # Verify it has been pushed
            sw = self.api.get_switch_by_name("test")
            assert sw is not None

            # Remove it
            self.api.remove_switch_by_name("test")

        with responses_from_cassette('remove_switch_by_name_2'):
            sw = self.api.get_switch_by_name("test")
            assert sw is None

    def test_remove_switch_by_dpid(self):
        with responses_from_cassette('remove_switch_by_dpid'):
            # Add a switch first
            self.api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

            # Verify it has been puseed
            sw = self.api.get_switch_by_dpid("00:00:00:00:01:01:01:01")
            assert sw is not None

            # Remove it
            self.api.remove_switch_by_dpid("00:00:00:00:01:01:01:01")

        with responses_from_cassette('remove_switch_by_dpid_2'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:01:01:01:01")
            assert sw is None

    def test_get_switch_by_dpid(self):
        with responses_from_cassette('get_switch_by_dpid'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

            assert sw is not None
            assert sw.dpid == "00:00:00:00:00:01:00:01"

    def test_get_switch_by_dpid_fail(self):
        with responses_from_cassette('get_switch_by_dpid_fail'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:00:00:01")

            assert sw is None

    def test_update(self):
        with responses_from_cassette('update'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

            assert sw is not None

            sw.update()

            assert sw != None

    def test_remove(self):
        with responses_from_cassette("remove"):
            # Add a switch first
            self.api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

            # Verify it has been puseed
            sw = self.api.get_switch_by_name("test")
            assert sw is not None

            # Remove it
            sw.remove()

        with responses_from_cassette("get_switch_by_name_fail"):
            sw = self.api.get_switch_by_name("test")
            assert sw is None


    def test_add_switch(self):
        with responses_from_cassette('add_switch'):
            sw = self.api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

            assert sw is not None
            assert sw.name == "test"
            assert sw.dpid == "00:00:00:00:01:01:01:01"

            sw = self.api.get_switch_by_name("test")

            assert sw is not None


    def test_disconnect_switch(self):
        with responses_from_cassette('disconnect_switch'):
            switches = self.api.get_switches()

            assert len(switches) == 14

            for sw in switches:
                sw.disconnect()


    def test_get_interfaces(self):
        with responses_from_cassette('get_interfaces'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

            assert sw is not None

            interfaces = sw.get_interfaces()

            assert len(interfaces) == 9


    def test_get_connections(self):
        with responses_from_cassette('get_connections'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

            assert sw is not None

            connections = sw.get_connections()

            assert len(connections) == 4
