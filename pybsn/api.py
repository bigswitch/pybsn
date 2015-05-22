from __init__ import connect
from switch import Switch

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
                password):

        self.client = connect(host, username, password)

    def get_switches(self):
        return Switch.get_switches(self.client)

    def get_switch_by_name(self, name):
        return Switch.get_switch_by_name(self.client, name)

    def get_switch_by_dpid(self, dpid):
        return Switch.get_switch_by_dpid(self.client, dpid)

    def add_switch(self, **kwargs):
        return Switch.add_switch(self.client, **kwargs)


