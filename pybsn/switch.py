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
    def get_switches(client, filter=None):

        if filter:
            # Handle filtering
            if 'name' in filter:
                response = client.root.applications.bcf.info.fabric.switch.filter("name=$name", name=filter['name']).get()
            elif 'dpid' in filter:
                response = client.root.applications.bcf.info.fabric.switch.filter("dpid=$dpid", dpid=filter['dpid']).get()
            else:
                response = client.root.applications.bcf.info.fabric.switch.get()
        else: 
            response = client.root.applications.bcf.info.fabric.switch.get()

        switches = []

        for item in response:
            sw = Switch(client)
            sw.set_attributes(item)
            switches.append(sw)

        return switches

    @staticmethod
    def add_switch(client, **kwargs):
        sw = Switch(client)
        sw.set_attributes(**kwargs)

        # Validate switch object
        sw.validate()

        # Write switch object to REST API
        client.root.core.switch_config.put({
            'name': sw.name,
            'dpid': sw.dpid,
            'fabric-role': sw.fabric_role,
            'leaf-group': sw.leaf_group
        })

        return sw

    # Set dictionary of values onto switch object
    def set_attributes(self, attributes):
        for key, value in attributes.iteritems():
            setattr(self, key.replace('-', '_'), str(value))

    # Potentially generate the validations based on the schema dynamically
    def validate(self):
        assert self.name != None

    # Disconnect a switch from the controller (reset the connection)
    def disconnect(self):
        assert self.dpid != None
        
        # Make REST CALL
        self.client.root.core.switch.filter("dpid=$dpid", dpid=self.dpid).disconnect.post(True)

