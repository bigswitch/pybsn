class Switch(object): 

    def __init__(self):
        # Defining Default Values
        self.dpid = None
        self.name = None

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