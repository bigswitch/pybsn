from ..__init__ import connect
from pybsn.bcf.switch import Switch


class Api(object):
    """
    Prototype BCF Specific "Porcelain" API.

    Note this API layer is currently quite incomplete. It is recommended using the generic
    Node API (e.g. client.root) to access BigDB.

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

        self.client = connect(host, username, password, login=login)

    def get_switches(self):
        return Switch.get_switches(self.client)

    def get_switch_by_name(self, name):
        return Switch.get_switch_by_name(self.client, name)

    def remove_switch_by_name(self, name):
        return Switch.remove_switch_by_name(self.client, name)

    def get_switch_by_dpid(self, dpid):
        return Switch.get_switch_by_dpid(self.client, dpid)

    def remove_switch_by_dpid(self, dpid):
        return Switch.remove_switch_by_dpid(self.client, dpid)

    def add_switch(self, **kwargs):
        return Switch.add_switch(self.client, **kwargs)


