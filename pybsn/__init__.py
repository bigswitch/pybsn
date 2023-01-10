import json
import logging
import re
from string import Template
from typing import Union
from urllib.parse import urlparse
import requests
from requests import Response
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib3.util import Timeout as TimeoutSauce
import warnings

warnings.simplefilter("ignore", InsecureRequestWarning)

logger = logging.getLogger("pybsn")

DATA_PREFIX = "/api/v1/data/"
RPC_PREFIX = "/api/v1/rpc/"
SCHEMA_PREFIX = "/api/v1/schema/"


class _ClientTimeout:
    pass


"""Use the timeout that has been specified by the client."""
CLIENT_TIMEOUT = _ClientTimeout()

TimeoutOverride = Union[type(None), type(CLIENT_TIMEOUT), TimeoutSauce, float]
"""Type of argument to pass in requests, that indicates the time out behaviour
   for waiting for a response.  None indicates to wait forever.
   CLIENT_TIMEOUT uses the default value for the BigDbClient.  Otherwise
   the value specified is the number of seconds.
"""

TimeoutDefault = Union[type(None), TimeoutSauce, float]
"""Type of argument to use to indicate the default value for
   BigDbClient requests timing out. None indicates to wait forever.
   Otherwise the value specified is the number of seconds.
"""


class TimeoutSession(requests.Session):
    """Have a configurable value for timing out requests."""

    """How long to wait for a request to timeout.
        None is used to indicate to wait forever."""
    timeout: TimeoutDefault = None

    def _effective_timeout(self, timeout: TimeoutOverride) -> \
            TimeoutDefault:
        """Calculate the timeout value for a request.

        :param timeout: Override for this request.  None indicates there is no
        timeout, and CLIENT_DEFAULT indicates use the default value for this
        session.

        :return: None or the value to use to limit the waiting time.
        """
        if timeout == CLIENT_TIMEOUT:
            return self.timeout
        return timeout

    def __init__(self, timeout: TimeoutDefault = None) -> None:
        """
        :param timeout: Amount of time to wait for a response.  None
        indicates to wait forever.
        """
        super().__init__()
        self.timeout = timeout

    def send(self, request, timeout: TimeoutOverride = CLIENT_TIMEOUT,
             **kwargs) -> Response:
        """Send a given PreparedRequest.

        :rtype: requests.Response
        """
        kwargs['timeout'] = self._effective_timeout(timeout)
        return super().send(request, **kwargs)

    def request(
            self,
            method,
            url,
            params=None,
            data=None,
            headers=None,
            cookies=None,
            files=None,
            auth=None,
            timeout=None,
            allow_redirects=True,
            proxies=None,
            hooks=None,
            stream=None,
            verify=None,
            cert=None,
            json=None,
    ) -> requests.Response:
        """Constructs a :class:`Request <Request>`, prepares it and sends it.
        Returns :class:`Response <Response>` object.

        :param method: method for the new :class:`Request` object.
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary or bytes to be sent in the query
            string for the :class:`Request`.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the
            :class:`Request`.
        :param headers: (optional) Dictionary of HTTP Headers to send with the
            :class:`Request`.
        :param cookies: (optional) Dict or CookieJar object to send with the
            :class:`Request`.
        :param files: (optional) Dictionary of ``'filename': file-like-objects``
            for multipart encoding upload.
        :param auth: (optional) Auth tuple or callable to enable
            Basic/Digest/Custom HTTP Auth.
        :param timeout: (optional) How long to wait for the server to send
            data before giving up, as a float, or a :ref:`(connect timeout,
            read timeout) <timeouts>` tuple.
        :type timeout: float or tuple
        :param allow_redirects: (optional) Set to True by default.
        :type allow_redirects: bool
        :param proxies: (optional) Dictionary mapping protocol or protocol and
            hostname to the URL of the proxy.
        :param stream: (optional) whether to immediately download the response
            content. Defaults to ``False``.
        :param verify: (optional) Either a boolean, in which case it controls whether we verify
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use. Defaults to ``True``. When set to
            ``False``, requests will accept any TLS certificate presented by
            the server, and will ignore hostname mismatches and/or expired
            certificates, which will make your application vulnerable to
            man-in-the-middle (MitM) attacks. Setting verify to ``False``
            may be useful during local development or testing.
        :param cert: (optional) if String, path to ssl client cert file (.pem).
            If Tuple, ('cert', 'key') pair.
        :rtype: requests.Response
        """
        return super().request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            files=files,
            auth=auth,
            timeout=timeout,
            allow_redirects=allow_redirects,
            proxies=proxies,
            hooks=hooks,
            stream=stream,
            verify=verify,
            cert=cert,
            json=json)


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

    def get(self, params=None, timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Retrieve the data stored in BigDB at the path identified by this node.

        :params params: Optional hash of parameters that will be appended to the query
            e.g., {'state-type': 'global-config'} would restrict the state to global config.
        :param timeout: Amount of time to wait for response.  None indicates
            to wait forever.  CLIENT_TIMEOUT indicates to use the default value
            from BigDbClient
        """
        return self._connection.get(self._path, params, timeout=timeout)

    def post(self, data, params=None, timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Inserts (POST) the given data to BigDB at the path identified by this node.

        :param data: JSON serializable data to post, often a dictionary.
            Note that the data provided here is passed to BigDB as-is; i.e., use hyphens.
        :params params: Optional hash of parameters that will be appended to the query
            e.g., {'state-type': 'global-config'} would restrict the state to global config.
        :param timeout: Amount of time to wait for response.  None indicates
            to wait forever.  CLIENT_TIMEOUT indicates to use the default value
            from BigDbClient
        """
        return self._connection.post(self._path, data, params, timeout=timeout)

    def put(self, data, params=None, timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Replaces (PUT) the given data in BigDB at the path identified by this node.

        :param data: JSON serializable data to post, often a dictionary.
            Note that the data provided here is passed to BigDB as-is; i.e., use hyphens.
        :params params: Optional hash of parameters that will be appended to the query
            e.g., {'state-type': 'global-config'} would restrict the state to global config.
        :param timeout: Amount of time to wait for response.  None indicates
            to wait forever.  CLIENT_TIMEOUT indicates to use the default value
            from BigDbClient
        """
        return self._connection.put(self._path, data, params, timeout=timeout)

    def patch(self, data, params=None, timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Updates (PATCH) the given data in BigDB at the path identified by this node.

        :param data: JSON serializable data to post, often a dictionary.
            Note that the data provided here is passed to BigDB as-is; i.e., use hyphens.
        :params params: Optional hash of parameters that will be appended to the query
            e.g., {'state-type': 'global-config'} would restrict the state to global config.
        :param timeout: Amount of time to wait for response.  None indicates
            to wait forever.  CLIENT_TIMEOUT indicates to use the default value
            from BigDbClient
        """
        return self._connection.patch(self._path, data, params, timeout=timeout)

    def delete(self, params=None, timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Delete the data stored in BigDB at the path identified by this node.
        :params params: Optional hash of parameters that will be appended to the query
            e.g., {'state-type': 'global-config'} would restrict the state to global config.
        :param timeout: Amount of time to wait for response.  None indicates
            to wait forever.  CLIENT_TIMEOUT indicates to use the default value
            from BigDbClient
        """
        return self._connection.delete(self._path, params=params, timeout=timeout)

    def schema(self, timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Retrieve the schema for BigDB at the path identified by this node.
        :param timeout: Amount of time to wait for response.  None indicates
            to wait forever.  CLIENT_TIMEOUT indicates to use the default value
            from BigDbClient
        """
        return self._connection.schema(self._path, timeout=timeout)

    def rpc(self, data=None, params=None, timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Invoke the BigDB RPC endpoint identified by this node.

         :param data to provide as RPC input to BigDB.
            Note that the data provided here is passed to BigDB as-is; i.e., use hyphens.
         :params params: Optional hash of parameters that will be appended to the query
e.g., {'initiate-async-id': '(async-id-here)'} would initiate RPC call asynchronously.
         :return the output data returned by the RPC endpoint.
        :param timeout: Amount of time to wait for response.  None indicates
            to wait forever.  CLIENT_TIMEOUT indicates to use the default value
            from BigDbClient
        """
        return self._connection.rpc(self._path, data, params, timeout=timeout)

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

    def __call__(self, timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Execute get method.
        :param timeout: Amount of time to wait for response.  None indicates
            to wait forever.  CLIENT_TIMEOUT indicates to use the default value
            from BigDbClient
        """
        return self.get(timeout=timeout)

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

    def set_default_timeout(self, timeout: TimeoutDefault):
        """ Change the default timeout for operational responses.

        Parameters:
            :param timeout: New time out value.  None indicates to wait
            until the response arrives, without timing out.
        """
        self.session.timeout = timeout

    def get_default_timeout(self) -> TimeoutDefault:
        return self.session.timeout

    def get(self, path, params=None,
            timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Retrieves information from the REST API using the GET method.

        :param path: the URL path to retrieve the data from; does not include the prefix
              (/api/v1/data).
        :param params: request parameters to attach
        :param timeout: Amount of time to wait for response.  None indicates
            to wait forever.  CLIENT_TIMEOUT indicates to use the default value
            from BigDbClient
        :return: the deserialized result as list.
        """
        return self._request("GET", path, params=params, timeout=timeout).json()

    def rpc(self, path, data, params=None, timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Invokes an RPC endpoint on the REST API.

        :param path: the path path of the RPC to invoke. Does not include the prefix.
              (/api/v1/rpc).
        :param data: JSON serializable input data for the RPC.
        :param params: request parameters to attach
        :param timeout: Amount of time to wait for a response.  None indicates
            to wait forever.  CLIENT_DEFAULT uses the strategy as specified by
            the BigDBClient.
        :return: the deserialized RPC output (for most RPCs, a dict).
        """
        response = self._request("POST", path, data=self._dump_if_present(data),
                                 rpc=True, params=params,
                                 timeout=timeout)
        if response.status_code == requests.codes.no_content:
            return None
        elif response.status_code == requests.codes.accepted:
            try:
                return response.json()
            except (json.JSONDecodeError, ValueError):
                return None
        else:
            return response.json()

    def post(self, path, data, params=None,
             timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Inserts new data to the BigDB REST API via the POST method.

        :param path: the path at which to insert data. Does not include the prefix.
              (/api/v1/data).
        :param data: JSON serializable data to insert
        :param params: request parameters to attach
        :param timeout: Amount of time to wait for a response.  None indicates
          to wait forever.  CLIENT_DEFAULT uses the strategy as specified by the
          BigDBClient.
        :return: None on success
        """
        return self._request("POST", path, data=self._dump_if_present(data),
                             params=params, timeout=timeout)

    def put(self, path, data, params=None,
            timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Replaces data in the BigDB REST API via the PUT method.

        :param path: the path at which to insert data. Does not include the prefix.
              (/api/v1/data).
        :param data: JSON serializable to replace.
        :param params: request parameters to attach
        :param timeout: Amount of time to wait for a response.  None indicates
            to wait forever.  CLIENT_DEFAULT uses the strategy as specified by
            the BigDBClient.
        :return: None on success
        """
        return self._request("PUT", path, data=self._dump_if_present(data),
                             params=params, timeout=timeout)

    def patch(self, path, data, params=None,
              timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Updates data in the BigDB REST API via the PATCH method.

        :param path: the path at which to update data. Does not include the prefix.
              (/api/v1/data).
        :param data: JSON serializable of the data to update.
        :param params: request parameters to attach
        :param timeout: Amount of time to wait for a response.  None indicates
            to wait forever.  CLIENT_DEFAULT uses the strategy as specified by
            the BigDBClient.
        :return: None on success
        """
        return self._request("PATCH", path, data=self._dump_if_present(data),
                             params=params, timeout=timeout)

    def delete(self, path, params=None,
               timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """  Deletes data from the BigDB REST API via the DELETE method.

        Parameters:

            :param path: the path from which to delete data. Does not include the prefix.
              (/api/v1/data).
            :param params: request parameters to attach
        :param timeout: Amount of time to wait for a response.  None indicates
            to wait forever.  CLIENT_DEFAULT uses the strategy as specified by
            the BigDBClient.
        """
        return self._request("DELETE", path, params=params, timeout=timeout)

    def schema(self, path="",
               timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """  Retrieves the schema for a given path from BigDB.

            :param path: the path for which to retrieve the schema. Does not include the prefix
              (/api/v1/schema).
            :param timeout: Amount of time to wait for a response.  None indicates
               to wait forever.  CLIENT_DEFAULT uses the strategy as specified
               by the BigDBClient.
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

    def _request(self, method, path, data=None, params=None, rpc=False,
                 timeout: TimeoutOverride = CLIENT_TIMEOUT):
        """ Low level request method; generally, use the specialized methods below. """
        url = self.url + (RPC_PREFIX if rpc else DATA_PREFIX) + path

        request = requests.Request(method=method, url=url, data=data, params=params)
        response = logged_request(self.session, request, timeout=timeout)

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


def logged_request(session, request, timeout: TimeoutOverride = CLIENT_TIMEOUT):
    """ Helper method that logs HTTP requests made by this library, if configured. """
    prepared = session.prepare_request(request)

    marker = "-" * 30
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s Request: %s\n%s\n%s\n\n%s", marker, marker, prepared.method + ' ' + prepared.url,
                     '\n'.join('{}: {}'.format(k, v) for k, v in prepared.headers.items()),
                     prepared.body)

    response = session.send(prepared, timeout=timeout)

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


def connect(host, username=None, password=None, token=None, login=None,
            verify_tls=False, session_headers=None,
            timeout: TimeoutDefault = None,
            *args, **kwargs) -> BigDbClient:
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

    :parameter timeout Amount of time to wait for a response. None indicates
        to wait forever. The timeout value will be used as the default
        for future operations unless it is changed.

    (other parameters for advanced/internal use).

    :return A connected BigDBClient instance
    :raises Exception on error
    """
    session = TimeoutSession(timeout=timeout)
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
