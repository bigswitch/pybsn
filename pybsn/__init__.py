import requests, json
from string import Template

try:
    import warnings
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    warnings.simplefilter("ignore", InsecureRequestWarning)
except ImportError:
    pass

PREFIX = "/api/v1/data/"
SCHEMA_PREFIX = "/api/v1/schema/"

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

    def __repr__(self):
        return "Node(%s)" % self._path

class BigDbClient(object):
    def __init__(self, url, session, verify=True):
        self.url = url
        self.session = session
        self.root = Node("controller", self)
        self.verify = verify

    def request(self, method, path, data=None, params=None):
        url = self.url + PREFIX + path
        response = self.session.request(method, url, data=data, params=params, verify=self.verify)
        try:
            # Raise an HTTPError for 4xx/5xx codes
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.text:
                error_json = json.loads(e.response.text)
                # Attempt to capture the REST API error description and pass it along to the HTTPError
                if 'description' in error_json:
                    e.args = (e.args[0] + ': ' + error_json['description'],)
            raise
        return response

    def get(self, path, params=None):
        return json.loads(self.request("GET", path, params=params).text)

    def post(self, path, data):
        return self.request("POST", path, data=json.dumps(data))

    def put(self, path, data):
        return self.request("PUT", path, data=json.dumps(data))

    def patch(self, path, data):
        return self.request("PATCH", path, data=json.dumps(data))

    def delete(self, path):
        return self.request("DELETE", path)

    def schema(self, path=""):
        url = self.url + SCHEMA_PREFIX + path
        response = self.session.get(url, verify=self.verify)
        response.raise_for_status()
        return json.loads(response.text)

    def __repr__(self):
        return "BigDbClient(%s)" % self.url

AUTH_ATTEMPTS = [
    ('https', 8443, "/api/v1/auth/login"),
    ('https', 443, "/auth/login"),
    ('http', 8080, "/api/v1/auth/login"),
]

def attempt_login(session, host, username, password, verify):
    auth_data = json.dumps({ 'user': username, 'password': password })
    for schema, port, path in AUTH_ATTEMPTS:
        url = "%s://%s:%d" % (schema, host, port)
        try:
            response = session.post(url + path, auth_data, verify=verify)
        except requests.exceptions.ConnectionError:
            continue
        if response.status_code == 200: # OK
            # Fix up cookie path
            for cookie in session.cookies:
                if cookie.path == "/auth":
                    cookie.path = "/api"
            return url
        elif response.status_code == 401: # Unauthorized
            response.raise_for_status()
    raise Exception("Login failed")

def connect(host, username, password, verify=False):
    session = requests.Session()
    url = attempt_login(session, host, username, password, verify)
    return BigDbClient(url, session, verify=verify)
