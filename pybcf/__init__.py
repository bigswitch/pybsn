import requests, json

AUTH_URL = "/api/v1/auth/login"
PREFIX = "/api/v1/data/"
SCHEMA_PREFIX = "/api/v1/schema/"

ALIASES = {"switches":"/core/switch"}

class AttrDict(dict):
    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v

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
    def __init__(self, path, session):
        self._path = path
        self._session = session

    def __getattr__(self, name):
        name = name.replace("_", "-")
        return Node(self._path + "/" + name, self._session)

    def _request(self, method, data=None, params=None):
        url = self._session.url + PREFIX + self._path
        return self._session.request(method, url, data=data, params=params)

    def get(self, params=None):
        return from_json(self._request("GET", params=params).text)

    def post(self, data):
        self._request("POST", data=to_json(data))

    def patch(self, data):
        self._request("PATCH", data=to_json(data))

    def schema(self):
        url = self._session.url + SCHEMA_PREFIX + self._path
        return from_json(self._session.request("GET", url, data=None, params=None).text)

    def __call__(self):
        return self.get()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

class BCF(object):
    def __init__(self, url, username, password):
        self.session = requests.Session()
        self.session.url = url
        data = json.dumps({ 'user': username, 'password': password })
        self.session.post(url + AUTH_URL, data).json()

    def connect(self):
        return Node("controller", self.session)

    def __getattr__(self, name):
        aliased_path = ALIASES[name]
        return Node("controller" + aliased_path, self.session)
