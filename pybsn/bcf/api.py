from ..__init__ import connect
from switch import Switch

AUTH_PATH = "/api/v1/auth/login"
AUTH_PORT = 8443
AUTH_PROTOCOL = "https"

class Api(object):
    """A python interface into the Big Switch Networks Big Cloud Fabric API

    Example usage:
  
      To create an instance of the pybsn.Api class:
  
        >>> import pybsn
        >>> api = pybsn.Api(<controller_ip>, <user>, <password>)
    """ 

    def __init__(self,
                host,
                username,
                password,
                login=True):

        url = "%s://%s:%d" % (AUTH_PROTOCOL, host, AUTH_PORT)
        self.client = connect(url, AUTH_PATH, username, password, login=login)

    def get_switches(self):
        return Switch.get_switches(self.client)

    def get_switch_by_name(self, name):
        return Switch.get_switch_by_name(self.client, name)

    def get_switch_by_dpid(self, dpid):
        return Switch.get_switch_by_dpid(self.client, dpid)

    def add_switch(self, **kwargs):
        return Switch.add_switch(self.client, **kwargs)


