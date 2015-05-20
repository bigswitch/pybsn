from betamax import Betamax
from requests import Session
from unittest import TestCase
from ..api import Api

with Betamax.configure() as config:
    config.cassette_library_dir = 'fixtures/cassettes/switch'

def test_get_switches():
	api = Api("192.168.142.213", "admin", "taco")
	with Betamax(api.client.session).use_cassette('get_switches'):
		switches = api.get_switches()

		assert len(switches) == 14

		for sw in switches:
			assert sw.name == None
			assert sw.dpid != None