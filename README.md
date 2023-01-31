# pybsn
pybsn is a python interface to [Big Switch Network](http://bigswitch.com) products

[![PyPI version](https://badge.fury.io/py/pybsn.svg)](https://pypi.python.org/pypi/pybsn/)

## Installation

pybsn supports Python versions 3.6 to 3.11. pybsn with Python 3.6
support has been deprecated, and may be removed in the
next release.


```bash
pip3 install pybsn
```
As of version 0.4.0, pybsn is only compatible with python 3.6 or newer.

---
## PyBSN Repl - Interactive Shell

`pybsn-repl` is a powerful, interactive shell for the REST API. It is based on and requires python3.5 or newer and ipython 7.9 or newer.

### Installing Python3 on Mac

[Homebrew](https://brew.sh/) is a recommended option to install python3 on mac.

After you install homebrew, install python3 with

```
brew install python
```

### Installing IPython 7
```bash
pip3 install ipython
```

### Running pybsn-repl
```bash
./bin/pybsn-repl -H <controller_host> -u <user> -p <passwd>
```
**Note:** `pybsn-repl` requires `pybsn` to be available; you can either install it from `pip3` (see above); or use it directly from the source by prefixing the
command with `PYTHONPATH=<dir>`, e.g.,

```bash
~/dev/pybsn $ PYTHONPATH=. ./bin/pybsn-repl -H <controller_host> -u <user> -p <passwd>
```

### Using pybsn-repl

PyBSN-repl presents an IPython shell to interact with the REST API.

It accepts any python expressions, and exposes the following variables as primary
entry points:
* `ctrl`: BigDbClient instance
* `root`: ctrl.root - a reference to the root node.

#### Node Hierarchy

You can explore the DB Rest API anchored on `root`. Child nodes in the rest API are
dynamically exposed as child objects / properties of `root`. Hyphens (`-`) in the REST API
are converted to `_` for python.

E.g.,
* `root.core.switch` references the node `controller/core/switch`
* `root.core.switch_config` references the node `controller/core/switch-config`

Nodes that cannot be represented as properties because their name is a python keyword (e.g., `global`), can be accessed by dictionary style access, e.g.
```python
root.os.config["global"]
```

#### Operations on nodes:
* add a `#` at the end of the line to show the *Schema* at the given node.
```python
In [12]: root.core.switch_config#
controller/core/switch-config (list)
  # List of switches that are configured in the controller. Switch
  # configuration is keyed by a logical switch name and is bound to a
  # specific physical switch by its dpid
  banner : string (config)
    # The switch banner, which is displayed on login.
  description : string (config)
    # A description of this configured switch.
[...]
```

* invoke the node as a functon `<node>()` to perform a `GET` request against the node:
```python
In [8]: root.core.switch_config()
Out[8]:
[{'mac-address': '52:54:00:21:4c:56',
  'name': 'sn1',
  'role': 'service',
  'shutdown': False},
 {'mac-address': '52:54:00:c1:40:1e',
  'name': 'swl1',
  'role': 'bigtap',
  'shutdown': False}]
```
* call `match(<property>=<value>)` to add an exact-match predicate to the query:
```python
In [11]: root.core.switch_config.match(name='sn1')()
Out[11]:
[{'mac-address': '52:54:00:21:4c:56',
  'name': 'sn1',
  'role': 'service',
  'shutdown': False}]
```

* call HTTP methods on the node to mutate data:
   * `node.post(data)` - inserts data at the node
   * `node.put(data)` - replaces the node entirely with the new data
   * `node.patch(data)` - selectively updates the node with the given data, leaving unspecified values untouched
   * `node.delete()` - delete the node

In these examples, `data` is a JSON serializable object, often a dictionary. Note that the dictionary keys must be in schema format at present (i.e., with hyphens, `some-long-property` not `some_long_property`).

* call `node.rpc(input_data)` to make an RPC call to the RPC specified in the node.

`input_data` is a JSON serializable object, often a dictionary. Note that the dictionary keys must be in schema format at present (i.e., with hyphens, `some-long-property` not `some_long_property`).

The output/result of the RPC returned as a dictionary.


#### More Examples:

```python
# Show the schema for controller.core.switch
root.core.switch#

# Get info for all switches
root.core.switch()

# Get info for a specific switch
root.core.switch.match(name="leaf0a").get()
```


---
## Example Programmatic Usage

```python
import pybsn

# recommended: use with an access token, generated for the user with
# conf t
# user admin
#    access-token my-api-token
# >>> access-token : <token>
client = pybsn.connect(host=args.host, token="<token>", verify_tls=True|False)

# alternatively, can use user-name password
client = pybsn.connect(host=args.host, username="<user>", password="<password>", verify_tls=True|False)

# can use client directly to make requests:
## get all switch configs
switch_configs = client.get("core/switch-config")
## get config of a particular switch
particular_config = client.get('core/switch-config[name="leaf-1a"]')
## insert a new switch config
client.post("core/switch-config", data={ "name": "leaf-1a", "mac-address": "01:02:03:04:05:06" } )
## disconnect a switch (RPC)
client.rpc('core/switch[name="leaf-1a"]/disconnect')

# Or, can use the node abstraction layer for more convenient access:

root = client.root

## get all switch configs
switch_configs = root.core.switch_config()
## get config of a particular switch
particular_config = root.core.switch_config.match(name="leaf-1a")
## insert a new switch config
root.core.switch_config.post({ "name": "leaf-1a", "mac-address": "01:02:03:04:05:06" })
## disconnect a switch (RPC)
root.core.switch.match(name="leaf-1a").disconnect.rpc()
```

---
## Contributing

If you'd like to contribute a feature or bugfix: Thanks! To make sure your
fix/feature has a high chance of being included, please read the following
guidelines:

1. Post a [pull request](https://github.com/floodlight/pybsn/compare/).
2. Make sure there are tests! We will not accept any patch that is not tested.
   It's a rare time when explicit tests aren't needed. If you have questions
   about writing tests for pybsn, please open a
   [GitHub issue](https://github.com/floodlight/pybsn/issues/new).

Please see `CONTRIBUTING.md` for more details on contributing and running test.

---

## License

Please see LICENSE at the top level of the repository.
