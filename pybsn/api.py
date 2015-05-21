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

    def get_switches(self, filter=None):
        return Switch.get_switches(self.client, filter)

    def add_switch(self, **kwargs):
        return Switch.add_switch(self.client, **kwargs)


