import os
import unittest

from betamax import Betamax
from pybsn.bcf.api import Api

pybsn_host = os.environ.get('PYBSN_HOST', 'http://127.0.0.1:8080')
pybsn_user = os.environ.get('PYBSN_USER', 'admin')
pybsn_pass = os.environ.get('PYBSN_PASS', 'admin')

my_dir = os.path.dirname(__file__)

with Betamax.configure() as config:
    config.cassette_library_dir = os.path.join(my_dir, 'fixtures/cassettes/switch')
    config.define_cassette_placeholder('<PYBSN_HOST>', pybsn_host)

class TestSwitch(unittest.TestCase):
    def setUp(self):
        self.api = Api(pybsn_host, pybsn_user, pybsn_pass, login=False)

    def test_get_switches(self):
        with Betamax(self.api.client.session).use_cassette('get_switches'):
            switches = self.api.get_switches()

            assert len(switches) == 14

            for sw in switches:
                assert sw.name == None
                assert sw.dpid != None


    def test_get_switch_by_name(self):
        with Betamax(self.api.client.session).use_cassette('get_switch_by_name'):
            sw = self.api.get_switch_by_name("test")

            assert sw is not None
            assert sw.name == "test"


    def test_get_switch_by_name_fail(self):
        with Betamax(self.api.client.session).use_cassette('get_switch_by_name_fail'):
            sw = self.api.get_switch_by_name("test")

            assert sw is None


    def test_remove_switch_by_name(self):
        with Betamax(self.api.client.session).use_cassette('remove_switch_by_name'):
            # Add a switch first
            self.api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

            # Verify it has been pushed
            sw = self.api.get_switch_by_name("test")
            assert sw is not None

            # Remove it
            self.api.remove_switch_by_name("test")

        with Betamax(self.api.client.session).use_cassette('remove_switch_by_name_2'):
            sw = self.api.get_switch_by_name("test")
            assert sw is None


    def test_remove_switch_by_dpid(self):
        with Betamax(self.api.client.session).use_cassette('remove_switch_by_dpid'):
            # Add a switch first
            self.api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

            # Verify it has been puseed
            sw = self.api.get_switch_by_dpid("00:00:00:00:01:01:01:01")
            assert sw is not None

            # Remove it
            self.api.remove_switch_by_dpid("00:00:00:00:01:01:01:01")

        with Betamax(self.api.client.session).use_cassette('remove_switch_by_dpid_2'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:01:01:01:01")
            assert sw is None


    def test_get_switch_by_dpid(self):
        with Betamax(self.api.client.session).use_cassette('get_switch_by_dpid'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

            assert sw is not None
            assert sw.dpid == "00:00:00:00:00:01:00:01"


    def test_get_switch_by_dpid_fail(self):
        with Betamax(self.api.client.session).use_cassette('get_switch_by_dpid_fail'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:00:00:01")

            assert sw is None


    def test_update(self):
        with Betamax(self.api.client.session).use_cassette('update'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

            assert sw is not None

            sw.update()

            assert sw != None


    def test_remove(self):
        with Betamax(self.api.client.session) as vcr:
            vcr.use_cassette('remove')
            # Add a switch first
            self.api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

            # Verify it has been puseed
            sw = self.api.get_switch_by_name("test")
            assert sw is not None

            # Remove it
            sw.remove()

            vcr.use_cassette('get_switch_by_name_fail')
            sw = self.api.get_switch_by_name("test")
            assert sw is None


    def test_add_switch(self):
        with Betamax(self.api.client.session).use_cassette('add_switch'):
            sw = self.api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

            assert sw is not None
            assert sw.name == "test"
            assert sw.dpid == "00:00:00:00:01:01:01:01"

            sw = self.api.get_switch_by_name("test")

            assert sw is not None


    def test_disconnect_switch(self):
        with Betamax(self.api.client.session).use_cassette('disconnect_switch'):
            switches = self.api.get_switches()

            assert len(switches) == 14

            for sw in switches:
                sw.disconnect()


    def test_get_interfaces(self):
        with Betamax(self.api.client.session).use_cassette('get_interfaces'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

            assert sw is not None

            interfaces = sw.get_interfaces()

            assert len(interfaces) == 9


    def test_get_connections(self):
        with Betamax(self.api.client.session).use_cassette('get_connections'):
            sw = self.api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

            assert sw is not None

            connections = sw.get_connections()

            assert len(connections) == 4
