class Switch(object): 
    """Switch based API operations

    """
    def __init__(self, client):
        self.client = client

        # Default configurable values
        self.name = None
        self.dpid = None
        self.fabric_role = None
        self.leaf_group = None

    @staticmethod
    def get_switches(client):

        response = client.root.applications.bcf.info.fabric.switch.get()

        switches = []

        for item in response:
            sw = Switch(client)
            sw.set_attributes(item)
            switches.append(sw)

        return switches

    @staticmethod
    def get_switch_by_name(client, name):
        assert name != None

        response = client.root.applications.bcf.info.fabric.switch.filter("name=$name", name=name).get()

        if len(response) > 0:
            item = response[0]
            sw = Switch(client)
            sw.set_attributes(item)
            return sw

    @staticmethod
    def remove_switch_by_name(client, name):
        assert name != None

        client.root.core.switch_config.filter("name=$name", name=name).delete()

    @staticmethod
    def get_switch_by_dpid(client, dpid):
        assert dpid != None

        response = client.root.applications.bcf.info.fabric.switch.filter("dpid=$dpid", dpid=dpid).get()

        if len(response) > 0:
            item = response[0]
            sw = Switch(client)
            sw.set_attributes(item)
            return sw

    @staticmethod
    def add_switch(client, **kwargs):
        sw = Switch(client)
        sw.set_attributes(kwargs)

        # Write switch object to REST API
        client.root.core.switch_config.put({
            'name': sw.name,
            'dpid': sw.dpid,
            'fabric-role': sw.fabric_role,
            'leaf-group': sw.leaf_group
        })

        sw.update()

        return sw

    # Update this reference with the most recent data from the REST API
    def update(self):
        assert self.name != None or self.dpid != None

        if self.name != None:
            sw = self.get_switch_by_name(self.client, self.name)
        elif self.dpid != None:
            sw = self.get_switch_by_dpid(self.client, self.dpid)

        if sw != None:
            self.set_attributes(sw.__dict__)

    def remove(self):
        assert self.name != None

        self.remove_switch_by_name(self.client, self.name)

    # Set dictionary of values onto switch object
    def set_attributes(self, attributes):
        for key, value in attributes.iteritems():
            if isinstance(value, basestring):
                value = str(value)
            setattr(self, key.replace('-', '_'), value)

    # Disconnect a switch from the controller (reset the connection)
    def disconnect(self):
        assert self.dpid != None
        
        # Make REST CALL
        self.client.root.core.switch.filter("dpid=$dpid", dpid=self.dpid).disconnect.post(True)

    # Get the switch interfaces
    def get_interfaces(self):
        assert self.dpid != None 

        # Make REST CALL
        return self.client.root.core.switch.filter("dpid=$dpid", dpid=self.dpid).interface.get()

        # Get the switch interfaces
    def get_connections(self):
        assert self.dpid != None 

        # Make REST CALL
        return self.client.root.core.switch.filter("dpid=$dpid", dpid=self.dpid).connection.get()
