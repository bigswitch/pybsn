import requests, json
PREFIX = "/api/v1/data/"

class Node(object):
    def __init__(self, path, session):
        self.path = path
        self.session = session

    def __getattr__(self, name):
        name = name.replace("_", "-")
        return Node(self.path + "/" + name, self.session)

    def request(self, method, data=None, params=None):
        url = self.session.url + PREFIX + self.path
        return self.session.request(method, url, data=data, params=params)

    def get(self, params=None):
        return self.request("GET", params=params).json()[0]

    def post(self, data):
        self.request("POST", data=json.dumps(data))

    def patch(self, data):
        self.request("PATCH", data=json.dumps(data))

    def __call__(self):
        return self.get()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

def connect(url, username, password):
    session = requests.Session()
    session.url = url
    data = json.dumps({ 'user': username, 'password': password })
    session.post(url + "/api/v1/auth/login", data).json()
    return Node("controller", session)
