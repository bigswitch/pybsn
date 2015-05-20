class Switch(object): 

    def __init__(self, client):
        self.client = client

        # Configurable values
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
            for attr in item.keys():
                setattr(sw, attr, str(item[attr]))
            switches.append(sw)

        return switches

    @staticmethod
    def add_switch(client, **kwargs):
        sw = Switch(client)

        # Load arguments into switch object
        for key, value in kwargs.iteritems():
            setattr(sw, key, str(value))

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

    # Potentially generate the validations based on the schema dynamically
    def validate(self):
        assert self.name != None

    def disconnect(self):
        assert self.dpid != None
        
        # Make REST CALL
        self.client.root.core.switch.filter("dpid=$dpid", dpid=self.dpid).disconnect.post(True)

