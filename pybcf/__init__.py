import requests, json
from string import Template

AUTH_URL = "/api/v1/auth/login"
LEGACY_AUTH_URL = "/auth/login"
PREFIX = "/api/v1/data/"
SCHEMA_PREFIX = "/api/v1/schema/"

ALIASES = {"switches":"/core/switch",
            "fabric_switches":"/applications/bcf/info/fabric/switch",
            "interfaces":"/core/switch/interface",
            "links":"/applications/bcf/info/fabric/link",
            "controllers":"/cluster",
            "lags":"/core/switch/fabric-lag",
            "users":"/core/aaa/local-user",
            "groups":"/core/aaa/group",
            "fabric":"/applications/bcf/info/summary/fabric"}

class AttrDict(object):
    __slots__ = ['_values']

    def __init__(self, values=None):
        object.__setattr__(self, "_values", {})
        if values is not None:
            for k, v in values.items():
                self[k] = v

    @staticmethod
    def _key(k):
        return k.replace("_", "-")

    def keys(self):
        return self._values.keys()

    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v

    def __getitem__(self, k):
        return self._values[self._key(k)]

    def __setitem__(self, k, v):
        self._values[self._key(k)] = v

    def __contains__(self, k):
        return self._key(k) in self._values

    def __repr__(self):
        return self._values.__repr__()

    def __str__(self):
        return self._values.__str__()

    def __iter__(self):
        return self._values.__iter__()

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

    def put(self, data):
        return self._connection.put(self._path, data)

    def patch(self, data):
        return self._connection.patch(self._path, data)

    def delete(self):
        return self._connection.delete(self._path)

    def schema(self):
        return self._connection.schema(self._path)

    def filter(self, template, *args, **kwargs):
        # TODO escape values better than repr()
        kwargs = { k: repr(v) for k, v in kwargs.items() }
        predicate = '[' + Template(template).substitute(**kwargs) + ']'
        return Node(self._path + predicate, self._connection)

    def match(self, **kwargs):
        for k, v in kwargs.items():
            self = self.filter("%s=$x" % k.replace('_', '-'), x=v)
        return self

    def __call__(self):
        return self.get()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

# class DataNode(object):
#     def __init__(self, path, connection, value):
#         self._path = path
#         self._connection = connection
#         self._value = value

#     def get(self, name):
#         return DataNode(self._path, self._connection, self._value[name])

#     def __getattr__(self, name):
#         print "get attr"
#         print self._value[name]
#         return DataNode(self._path, self._connection, self._value[name])

#     def __getitem__(self, k):
#         print self._value[k]
#         return DataNode(self._path, self._connection, self._value[k])

#     def __call__(self):
#         return self.get()

class BCF(object):
    def __init__(self, url, username, password, verify=True):
        self.session = requests.Session()
        self.url = url
        data = json.dumps({ 'user': username, 'password': password })
        self.session.post(url + AUTH_URL, data, verify=verify).raise_for_status()
        self.root = Node("controller", self)
        self.verify = verify

    # deprecated
    def connect(self):
        return self.root

    def __getattr__(self, name):
        aliased_path = ALIASES[name]
        return Node("controller" + aliased_path, self)

    def request(self, method, path, data=None, params=None):
        url = self.url + PREFIX + path
        response = self.session.request(method, url, data=data, params=params, verify=self.verify)
        try:
            # Raise an HTTPError for 4xx/5xx codes
            response.raise_for_status()
        except requests.exceptions.HTTPError, e:
            if e.response.text:
                error_json = json.loads(e.response.text)
                if 'description' in error_json:
                    e.args = (e.args[0] + ': ' + error_json['description'],)
            raise
        return response

    def get(self, path, params=None):
        return from_json(self.request("GET", path, params=params).text)

    def post(self, path, data):
        return self.request("POST", path, data=to_json(data))

    def put(self, path, data):
        return self.request("PUT", path, data=to_json(data))

    def patch(self, path, data):
        return self.request("PATCH", path, data=to_json(data))

    def delete(self, path):
        return self.request("DELETE", path)

    def schema(self, path=""):
        url = self.url + SCHEMA_PREFIX + path
        response = self.session.get(url, verify=self.verify)
        response.raise_for_status()
        return from_json(response.text)

class BigTap(BCF):
    def __init__(self, url, username, password, verify=True):
        self.session = requests.Session()
        self.url = url
        data = json.dumps({ 'user': username, 'password': password })
        response = self.session.post(url + LEGACY_AUTH_URL, data, verify=verify)
        response.raise_for_status()
        # Fix up cookie path
        for cookie in self.session.cookies:
            if cookie.path == "/auth":
                cookie.path = "/api"
        self.root = Node("controller", self)
        self.verify = verify
