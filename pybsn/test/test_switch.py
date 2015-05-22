import os
from betamax import Betamax
from requests import Session
from nose import with_setup
from ..api import Api

with Betamax.configure() as config:
    config.cassette_library_dir = 'fixtures/cassettes/switch'


def test_get_switches():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'])
	with Betamax(api.client.session).use_cassette('get_switches'):
		switches = api.get_switches()

		assert len(switches) == 14

		for sw in switches:
			assert sw.name == None
			assert sw.dpid != None

def test_get_switches():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'])
	with Betamax(api.client.session).use_cassette('get_switches_filtered'):
		switches = api.get_switches(filter={"dpid":"00:00:00:00:00:01:00:01"})

		assert len(switches) == 1

		sw = switches[0]

		assert sw != None
		assert sw.name == None
		assert sw.dpid != None

def test_disconnect_switch():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'])
	with Betamax(api.client.session).use_cassette('disconnect_switch'):
		switches = api.get_switches()

		assert len(switches) == 14

		for sw in switches:
			sw.disconnect()

def test_get_interfaces():
	api = Api(os.environ['PYBSN_HOST'], os.environ['PYBSN_USER'], os.environ['PYBSN_PASS'])
	with Betamax(api.client.session).use_cassette('get_interfaces'):
		switches = api.get_switches(filter={"dpid":"00:00:00:00:00:01:00:01"})

		assert len(switches) == 1

		sw = switches[0]

		interfaces = sw.get_interfaces()

		assert len(interfaces) == 9