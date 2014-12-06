import requests, json

AUTH_URL = "/api/v1/auth/login"
PREFIX = "/api/v1/data/"
SCHEMA_PREFIX = "/api/v1/schema/"

ALIASES = {"switches":"/core/switch"}

class AttrDict(object):
    def __init__(self, values=None):
        self.__dict__["_values"] = {}
        if values is not None:
            for k, v in values.items():
                self[k] = v

    @staticmethod
    def _key(k):
        return k.replace("_", "-")

    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v

    def __getitem__(self, k):
        return self._values[self._key(k)]

    def __setitem__(self, k, v):
        self._values[self._key(k)] = v

    def __repr__(self):
        return self._values.__repr__()

    def __str__(self):
        return self._values.__str__()

class BCFJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AttrDict):
            return obj._values
        return json.JSONEncoder.default(self, obj)

def to_json(data):
    return json.dumps(data, cls=BCFJSONEncoder)

def from_json(text):
    return json.loads(text, object_hook=AttrDict)

class Node(object):
    def __init__(self, path, connection):
        self._path = path
        self._connection = connection

    def __getattr__(self, name):
        return self[name.replace("_", "-")]

    def __getitem__(self, name):
        return Node(self._path + "/" + name, self._connection)

    def get(self, params=None):
        return self._connection.get(self._path, params)

    def post(self, data):
        return self._connection.post(self._path, data)

    def patch(self, data):
        return self._connection.patch(self._path, data)

    def schema(self):
        return self._connection.schema(self._path)

    def __call__(self):
        return self.get()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

class BCF(object):
    def __init__(self, url, username, password):
        self.session = requests.Session()
        self.url = url
        data = json.dumps({ 'user': username, 'password': password })
        self.session.post(url + AUTH_URL, data).json()
        self.root = Node("controller", self)

    # deprecated
    def connect(self):
        return root

    def __getattr__(self, name):
        aliased_path = ALIASES[name]
        return Node("controller" + aliased_path, self.session)

    def request(self, method, path, data=None, params=None):
        url = self.url + PREFIX + path
        response = self.session.request(method, url, data=data, params=params)
        response.raise_for_status()
        return response

    def get(self, path, params=None):
        return from_json(self.request("GET", path, params=params).text)

    def post(self, path, data):
        return self.request("POST", path, data=to_json(data))

    def patch(self, path, data):
        return self.request("PATCH", path, data=to_json(data))

    def schema(self, path=""):
        url = self.url + SCHEMA_PREFIX + path
        response = self.session.get(url)
        response.raise_for_status()
        return from_json(response.text)
