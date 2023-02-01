import json
import logging
import re
from string import Template
from urllib.parse import urlparse
import requests
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", InsecureRequestWarning)

logger = logging.getLogger("pybsn")

DATA_PREFIX = "/api/v1/data/"
RPC_PREFIX = "/api/v1/rpc/"
SCHEMA_PREFIX = "/api/v1/schema/"


class Node(object):
    """ Higher level "Node" abstraction for PyBSN.

    In this abstraction, the BigDB tree is represented as dynamically created nodes. You can
    navigate through the tree by traversing the child nodes of the root object.

    Hyphens (-) in the REST API are converted to _ for python.

    E.g.,
      root.core.switch references the node controller/core/switch
      root.core.switch_config references the node controller/core/switch-config

    On a node, you can call HTTP methods, e.g.,

    root.core.switch_config.post(switch_data)

    would insert the switch as defined by switch_data to /controller/core/switch-config.

    You can also add predicates to the path using filter() and map():

    E.g.,
      root.core.switch.match(mac_address='14:18:77:96:8b:d6').get()
    is converted to
      GET .../controller/core/switch[mac-address="14:18:77:96:8b:d6"]
    and retrieves the core/switch subtree for the given switch.

    Nodes that cannot be represented as properties because their name is a python
    keyword (e.g., global), can be accessed by dictionary style access, e.g.

    root.os.config["global"].
    """
    def __init__(self, path, connection):
        self._path = path
        self._connection = connection

    def __getattr__(self, name):
        """ Provides node traversal access to child nodes (root.core.switch_config).

        As hyphens cannot be used in identifiers in python, they are converted to underscores here.
        """
        return self[name.replace("_", "-")]

    def __getitem__(self, name):
        """ Provides dictionary style access to child nodes, e.g., root["os"]["global"]["config"].

        Note that the parameter values are used as-is in BigDB, i.e., use hyphens not underscores here.

        E.g., root["core"]["switch-config"].

        """
        return Node(self._path + "/" + name, self._connection)

    def get(self, params=None):
        """ Retrieve the data stored in BigDB at the path identified by this node.

        :params params: Optional hash of parameters that will be appended to the query
            e.g., {'state-type': 'global-config'} would restrict the state to global config.
        """
        return self._connection.get(self._path, params)

    def post(self, data, params=None):
        """ Inserts (POST) the given data to BigDB at the path identified by this node.

        :param data: JSON serializable data to post, often a dictionary.
            Note that the data provided here is passed to BigDB as-is; i.e., use hyphens.
        :params params: Optional hash of parameters that will be appended to the query
            e.g., {'state-type': 'global-config'} would restrict the state to global config.
        """
        return self._connection.post(self._path, data, params)

    def put(self, data, params=None):
        """ Replaces (PUT) the given data in BigDB at the path identified by this node.

        :param data: JSON serializable data to post, often a dictionary.
            Note that the data provided here is passed to BigDB as-is; i.e., use hyphens.
        :params params: Optional hash of parameters that will be appended to the query
            e.g., {'state-type': 'global-config'} would restrict the state to global config.
        """
        return self._connection.put(self._path, data, params)

    def patch(self, data, params=None):
        """ Updates (PATCH) the given data in BigDB at the path identified by this node.

        :param data: JSON serializable data to post, often a dictionary.
            Note that the data provided here is passed to BigDB as-is; i.e., use hyphens.
        :params params: Optional hash of parameters that will be appended to the query
            e.g., {'state-type': 'global-config'} would restrict the state to global config.
        """
        return self._connection.patch(self._path, data, params)

    def delete(self, params=None):
        """ Delete the data stored in BigDB at the path identified by this node. """
        return self._connection.delete(self._path, params=params)

    def schema(self):
        """ Retrieve the schema for BigDB at the path identified by this node. """
        return self._connection.schema(self._path)

    def rpc(self, data=None, params=None):
        """ Invoke the BigDB RPC endpoint identified by this node.

         :param data to provide as RPC input to BigDB.
            Note that the data provided here is passed to BigDB as-is; i.e., use hyphens.
         :params params: Optional hash of parameters that will be appended to the query
e.g., {'initiate-async-id': '(async-id-here)'} would initiate RPC call asynchronously.
         :return the output data returned by the RPC endpoint.
        """
        return self._connection.rpc(self._path, data, params)

    def match(self, **kwargs):
        """ Adds exact match predicates to the path represented by the current Node. Returns
        a Node representing the new path.

        Supply the child element(s) to match on as keyword parameters:
        * The name of the parameter indicates the child element to match on
           (hyphens converted to underscores)
        * The value of the parameter indicates the desired value

        E.g.,
        node.match(mac_address="01:02:03:04:05:05:06")
        translates into the BigDB Path

        .../node[mac-address="14:18:77:96:8b:d6"]
        """
        for k, v in kwargs.items():
            self = self.filter("%s=$x" % k.replace('_', '-'), x=v)
        return self

    def filter(self, template, *args, **kwargs):
        """ Adds a predicate to the path represented by the current Node. Returns
        a Node representing the new path.

        :param :template the predicate to add. Any template variables (e.g., $x)
               will be replaced with values retrieved from the keyword arguments

        E.g., to retrieve all BCF segments with a member ID smaller than 1000, you
        might do:
        root.applications.bcf.tenant.segment.filter("member-vlan<$max", max=1000).get()

        Here,
        segment.filter("member-vlan<$max", max=1000)
        translates into the BigDB path:
        .../segment[member-vlan<1000]
        """

        kwargs = {k: repr(v) for k, v in kwargs.items()}
        predicate = '[' + Template(template).substitute(**kwargs) + ']'
        return Node(self._path + predicate, self._connection)

    def __call__(self):
        return self.get()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __repr__(self):
        return "Node(%s)" % self._path


class BigDbClient(object):
    """
    Low level BigDB API client. Exposes Basic API methods to retrieve and manipulate data in the API,
    as well as to invoke RPCs.

    The higher-level Node interface to pybsn can be accessed via
    client.root
    """

    def __init__(self, url, session):
        """ Create a new BigDBClient. Generally, you should use pybsn.connect() to get an instance.

        Parameters:
            :param url: the base URL/origin of the BigDB server. Usually, https://<ip>:8443/
            :param session: requests session to use; set by connect
        """
        self.url = url
        self.session = session
        self.root = Node("controller", self)

    def get(self, path, params=None):
        """ Retrieves information from the REST API using the GET method.

        :param path: the URL path to retrieve the data from; does not include the prefix
              (/api/v1/data).
        :param params: request parameters to attach
        :return: the deserialized result as list.
        """
        return self._request("GET", path, params=params).json()

    def rpc(self, path, data, params=None):
        """ Invokes an RPC endpoint on the REST API.

        :param path: the path path of the RPC to invoke. Does not include the prefix.
              (/api/v1/rpc).
        :param data: JSON serializable input data for the RPC.
        :param params: request parameters to attach
        :return: the deserialized RPC output (for most RPCs, a dict).
        """
        response = self._request("POST", path, data=self._dump_if_present(data), rpc=True, params=params)
        if response.status_code == requests.codes.no_content:
            return None
        elif response.status_code == requests.codes.accepted:
            try:
                return response.json()
            except (json.JSONDecodeError, ValueError):
                return None
        else:
            return response.json()

    def post(self, path, data, params=None):
        """ Inserts new data to the BigDB REST API via the POST method.

        :param path: the path at which to insert data. Does not include the prefix.
              (/api/v1/data).
        :param data: JSON serializable data to insert
        :param params: request parameters to attach
        :return: None on success
        """
        return self._request("POST", path, data=self._dump_if_present(data), params=params)

    def put(self, path, data, params=None):
        """ Replaces data in the BigDB REST API via the PUT method.

        :param path: the path at which to insert data. Does not include the prefix.
              (/api/v1/data).
        :param data: JSON serializable to replace.
        :param params: request parameters to attach
        :return: None on success
        """
        return self._request("PUT", path, data=self._dump_if_present(data), params=params)

    def patch(self, path, data, params=None):
        """ Updates data in the BigDB REST API via the PATCH method.

        :param path: the path at which to update data. Does not include the prefix.
              (/api/v1/data).
        :param data: JSON serializable of the data to update.
        :param params: request parameters to attach
        :return: None on success
        """
        return self._request("PATCH", path, data=self._dump_if_present(data), params=params)

    def delete(self, path, params=None):
        """  Deletes data from the BigDB REST API via the DELETE method.

            :param path: the path from which to delete data. Does not include the prefix.
              (/api/v1/data).
            :param params: request parameters to attach
        """
        return self._request("DELETE", path, params=params)

    def schema(self, path=""):
        """  Retrieves the schema for a given path from BigDB.

            :param path: the path for which to retrieve the schema. Does not include the prefix
              (/api/v1/schema).
        """
        url = self.url + SCHEMA_PREFIX + path
        request = requests.Request(method="GET", url=url)
        response = logged_request(self.session, request)
        response.raise_for_status()
        return json.loads(response.text)

    def close(self):
        """ Closes the client.
           If this client was created by user/password (i..e, it holds an interactive session),
           then logs out of the session. Persistent API Tokens are not deleted.
        """
        token = self.session.cookies.get_dict().get("session_cookie")
        if token:
            # This is a no-op/fine for api tokens
            self.root.core.aaa.session.match(auth_token=token).delete()

    def _request(self, method, path, data=None, params=None, rpc=False):
        """ Low level request method; generally, use the specialized methods below. """
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

    def _dump_if_present(self, data):
        if data is not None:
            return json.dumps(data)
        else:
            return None

    def __enter__(self):
        return self

    def __exit__(self, type, value, trace_back):
        """ For using BigDbClient as a context manager (e.g., with "with"); closes the client on exit. """
        self.close()

    def __repr__(self):
        return "BigDbClient(%s)" % self.url


def logged_request(session, request):
    """ Helper method that logs HTTP requests made by this library, if configured. """
    prepared = session.prepare_request(request)

    marker = "-" * 30
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s Request: %s\n%s\n%s\n\n%s", marker, marker, prepared.method + ' ' + prepared.url,
                     '\n'.join('{}: {}'.format(k, v) for k, v in prepared.headers.items()),
                     prepared.body)

    response = session.send(prepared)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s Response: %s\n%s\n%s\n\n%s", marker, marker, response.status_code,
                     '\n'.join('{}: {}'.format(k, v) for k, v in response.headers.items()),
                     response.content)

    return response


BIGDB_PROTO_PORTS = [
    ('https', 8443),
    ('http', 8080),
]


def guess_url(session, host, validate_path="/api/v1/auth/healthy"):
    """ Guess the correct BigDB URL for a given host if not specified completely.
    :param session: requests session to use
    :param host: host as specified by the user
    :param validate_path: BigDB path to use to validate the correctness of the guess
    :return fully qualified BigDB URL
    """
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
            if response.status_code == 200:  # OK
                return url
            else:
                logger.debug("Could connect to URL %s: %s", url, response)
    raise Exception("Could not find available BigDB service on {}".format(host))


def _attempt_login(session, url, username, password):
    """ Attempts to create an interactive BigDB session by calling the login endpoint
        with user and password.

        If successful, stores the resulting cookie in the provided requests objects.
        Raises a requests exception (e.g., requests.exceptions.HTTPError) on error.
    """
    request = requests.Request(method="HEAD", url=url + "/api/v2/schema/controller/root/core/aaa/session/login")
    response = logged_request(session, request)
    if response.status_code == 200:
        return _attempt_modern_login(session, url, username, password)
    else:
        return _attempt_legacy_login(session, url, username, password)


def _attempt_legacy_login(session, url, username, password):
    auth_data = json.dumps({'user': username, 'password': password})
    path = "/api/v1/auth/login"
    request = requests.Request(method="POST", url=url + path, data=auth_data)
    response = logged_request(session, request)
    if response.status_code == 200:  # OK
        # Fix up cookie path
        for cookie in session.cookies:
            if cookie.path == "/auth":
                cookie.path = "/api"
        return url
    else:
        response.raise_for_status()


def _attempt_modern_login(session, url, username, password):
    auth_data = json.dumps({'user': username, 'password': password})
    path = "/api/v1/rpc/controller/core/aaa/session/login"
    request = requests.Request(method="POST", url=url + path, data=auth_data)
    response = logged_request(session, request)
    if response.status_code == 200:
        json_ = response.json()
        session_cookie = requests.cookies.create_cookie(
            name="session_cookie", value=json_["session-cookie"],
            domain=urlparse(url).hostname, path="/api")
        session.cookies.set_cookie(session_cookie)
        return url
    else:
        response.raise_for_status()


def connect(host, username=None, password=None, token=None, login=None, verify_tls=False, session_headers=None):
    """ Creates a connected BigDb client.

    Main entrypoint to pybsn.

    :param host: BigDB Host to connect to; can be just the hostname/IP (1.2.3.4) or the BigDB URL
                 prefix (https://1.2.3.4:8443/)

    To use user/password authentication (interactive session):
    :parameter username
    :parameter password

    To use an API token to authenticate against BigDB:
    :parameter token - API to use

    TLS verification:
    :parameter verify_tls: if set to True, requires that the BigDB API server has a valid/trusted
     management certificate configured.

    (other parameters for advanced/internal use).

    :return A connected BigDBClient instance
    :raises Exception on error
    """
    session = requests.Session()
    session.verify = verify_tls
    if session_headers:
        for k, v in session_headers.items():
            session.headers[k] = v

    url = guess_url(session, host)
    if login is None:
        login = (token is None) and username is not None and password is not None

    if login:
        _attempt_login(session=session, url=url, username=username, password=password)
    elif token:
        cookie = requests.cookies.create_cookie(name="session_cookie", value=token)
        session.cookies.set_cookie(cookie)
        request = requests.Request(method="GET", url=url + "/api/v1/data/controller/core/aaa/auth-context")
        response = logged_request(session, request)
        if response.status_code != 200:
            response.raise_for_status()

    return BigDbClient(url, session)
