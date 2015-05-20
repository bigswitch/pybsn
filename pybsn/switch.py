class Switch(object): 

    def __init__(self):
        # Defining Default Values
        self.name = None
        self.dpid = None

    @staticmethod
    def get_switches(client):
        response = client.root.applications.bcf.info.fabric.switch.get()

        switches = []

        for item in response:
            sw = Switch()
            for attr in item.keys():
                setattr(sw, attr, item[attr])
            switches.append(sw)

        return switches

    @staticmethod
    def add_switch(client, **kwargs):
        sw = Switch()

        # Load arguments into switch object
        for key, value in kwargs.iteritems():
            setattr(sw, key, value)

        # Validate switch object
        sw.validate()

        # Write switch object to REST API
        client.root.core.switch_config.put({
            'name': sw.name,
            'dpid': sw.dpid,
        })

        return sw

    # Potentially generate the validations based on the schema dynamically
    def validate(self):
        assert self.name != None
