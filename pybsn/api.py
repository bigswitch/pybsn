from __init__ import connect
from switch import Switch

class Api(object): 

    def __init__(self,
                host,
                username,
                password):

        self.client = connect(host, username, password)

    def get_switches(self):
        return Switch.get_switches(self.client)


