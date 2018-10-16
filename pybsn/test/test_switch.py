import os
from betamax import Betamax
from requests import Session
from nose import with_setup
from ..bcf.api import Api

with Betamax.configure() as config:
    config.cassette_library_dir = 'fixtures/cassettes/switch'
    config.define_cassette_placeholder('<PYBSN_HOST>', os.environ['PYBSN_HOST'])


def test_get_switches():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('get_switches'):
		switches = api.get_switches()

		assert len(switches) == 14

		for sw in switches:
			assert sw.name == None
			assert sw.dpid != None

def test_get_switch_by_name():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('get_switch_by_name'):
		sw = api.get_switch_by_name("test")

		assert sw != None
		assert sw.name == "test"

def test_get_switch_by_name_fail():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('get_switch_by_name_fail'):
		sw = api.get_switch_by_name("test")

		assert sw == None

def test_remove_switch_by_name():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('remove_switch_by_name'):
		# Add a switch first
		api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

		# Verify it has been puseed
		sw = api.get_switch_by_name("test")
		assert sw != None

		# Remove it
		api.remove_switch_by_name("test")

	with Betamax(api.client.session).use_cassette('remove_switch_by_name_2'):
		sw = api.get_switch_by_name("test")
		assert sw == None

def test_remove_switch_by_dpid():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('remove_switch_by_dpid'):
		# Add a switch first
		api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

		# Verify it has been puseed
		sw = api.get_switch_by_dpid("00:00:00:00:01:01:01:01")
		assert sw != None

		# Remove it
		api.remove_switch_by_dpid("00:00:00:00:01:01:01:01")

	with Betamax(api.client.session).use_cassette('remove_switch_by_dpid_2'):
		sw = api.get_switch_by_dpid("00:00:00:00:01:01:01:01")
		assert sw == None

def test_get_switch_by_dpid():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('get_switch_by_dpid'):
		sw = api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

		assert sw != None
		assert sw.dpid == "00:00:00:00:00:01:00:01"

def test_get_switch_by_dpid_fail():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('get_switch_by_dpid_fail'):
		sw = api.get_switch_by_dpid("00:00:00:00:00:00:00:01")

		assert sw == None

def test_update():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('update'):
		sw = api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

		assert sw != None
		
		sw.update()

		assert sw != None

def test_remove():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session) as vcr:
		vcr.use_cassette('remove')
		# Add a switch first
		api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

		# Verify it has been puseed
		sw = api.get_switch_by_name("test")
		assert sw != None

		# Remove it
		sw.remove()

		vcr.use_cassette('get_switch_by_name_fail')
		sw = api.get_switch_by_name("test")
		assert sw == None


def test_add_switch():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('add_switch'):
		sw = api.add_switch(dpid="00:00:00:00:01:01:01:01", name="test")

		assert sw != None
		assert sw.name == "test"
		assert sw.dpid == "00:00:00:00:01:01:01:01"

		sw = api.get_switch_by_name("test")

		assert sw != None

def test_disconnect_switch():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('disconnect_switch'):
		switches = api.get_switches()

		assert len(switches) == 14

		for sw in switches:
			sw.disconnect()

def test_get_interfaces():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('get_interfaces'):
		sw = api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

		assert sw != None

		interfaces = sw.get_interfaces()

		assert len(interfaces) == 9

def test_get_connections():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'], verify=False)
	with Betamax(api.client.session).use_cassette('get_connections'):
		sw = api.get_switch_by_dpid("00:00:00:00:00:01:00:01")

		assert sw != None

		connections = sw.get_connections()

		assert len(connections) == 4