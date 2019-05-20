import json
import logging
import re
from string import Template

import requests

try:
    import warnings
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    warnings.simplefilter("ignore", InsecureRequestWarning)
except ImportError:
    pass

logger = logging.getLogger("pybsn")

DATA_PREFIX = "/api/v1/data/"
RPC_PREFIX = "/api/v1/rpc/"
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

    def rpc(self, data=None):
        return self._connection.rpc(self._path, data)

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
    def __init__(self, url, session):
        self.url = url
        self.session = session
        self.root = Node("controller", self)

    def request(self, method, path, data=None, params=None, rpc=False):
        url = self.url + (RPC_PREFIX if rpc else DATA_PREFIX) + path

        request = requests.Request(method=method, url=url, data=data, params=params)
        response = logged_request(self.session, request)

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
        return self.request("GET", path, params=params).json()

    def rpc(self, path, data):
        response = self.request("POST", path, data=self._dump_if_present(data), rpc=True)
        if response.status_code == requests.codes.no_content:
            return None
        else:
            return response.json()

    def post(self, path, data):
        return self.request("POST", path, data=self._dump_if_present(data))

    def put(self, path, data):
        return self.request("PUT", path, data=self._dump_if_present(data))

    def patch(self, path, data):
        return self.request("PATCH", path, data=self._dump_if_present(data))

    def _dump_if_present(self, data):
        if data is not None:
            return json.dumps(data)
        else:
            return None

    def delete(self, path):
        return self.request("DELETE", path)

    def schema(self, path=""):
        url = self.url + SCHEMA_PREFIX + path
        response = self.session.get(url)
        response.raise_for_status()
        return json.loads(response.text)

    def __repr__(self):
        return "BigDbClient(%s)" % self.url


BIGDB_PROTO_PORTS = [
    ('https', 8443),
    ('http', 8080),
]


def logged_request(session, request):
    prepared = session.prepare_request(request)

    marker = "-" * 30
    logger.debug("%s Request: %s\n%s\n%s\n\n%s", marker, marker, prepared.method + ' ' + prepared.url,
                  '\n'.join('{}: {}'.format(k, v) for k, v in prepared.headers.items()),
                  prepared.body)

    response = session.send(prepared)

    logger.debug("%s Response: %s\n%s\n%s\n\n%s", marker, marker, response.status_code,
                  '\n'.join('{}: {}'.format(k, v) for k, v in response.headers.items()),
                  response.content)

    return response


def guess_url(session, host, validate_path="/api/v1/auth/healthy"):
    if re.match(r'^https?://', host):
        return host
    else:
        for schema, port in BIGDB_PROTO_PORTS:
            url = "%s://%s:%d" % (schema, host, port)
            try:
                response = session.get(url + validate_path, timeout=2)
            except requests.exceptions.ConnectionError as e:
                logger.debug("Error connecting to %s: %s", url, str(e))
                continue
            if response.status_code == 200: # OK
                return url
            else:
                logger.debug("Could connect to URL %s: %s", url, response)
    raise Exception("Could not find available BigDB service on {}".format(host))

def attempt_login(session, url, username, password):
    auth_data = json.dumps({ 'user': username, 'password': password })
    path = "/api/v1/auth/login"
    request = requests.Request(method="POST", url=url + path, data=auth_data)
    response = logged_request(session, request)
    if response.status_code == 200: # OK
        # Fix up cookie path
        for cookie in session.cookies:
            if cookie.path == "/auth":
                cookie.path = "/api"
        return url
    else:
        response.raise_for_status()

def connect(host, username=None, password=None, token=None, login=None, verify_tls=False):
    session = requests.Session()
    session.verify = verify_tls
    url = guess_url(session, host)
    if login is None:
        login = (token is None) and username is not None and password is not None

    if login:
        attempt_login(session=session, url=url, username=username, password=password)
    elif token:
        cookie = requests.cookies.create_cookie(name="session_cookie", value=token)
        session.cookies.set_cookie(cookie)
        request = requests.Request(method="GET", url=url + "/api/v1/data/controller/core/aaa/auth-context")
        response = logged_request(session, request)
        if response.status_code != 200:
            response.raise_for_status()

    return BigDbClient(url, session)
