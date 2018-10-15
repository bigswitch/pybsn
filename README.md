# pybsn
pybsn is a python interface to [Big Switch Network's](http://bigswitch.com) products

[![Build Status](https://travis-ci.org/floodlight/pybsn.svg)](https://travis-ci.org/floodlight/pybsn)
[![Coverage Status](https://coveralls.io/repos/floodlight/pybsn/badge.svg)](https://coveralls.io/r/floodlight/pybsn)
## Installation

```bash
pip install pybsn
# ... or ...
pip3 install pybsn
```
pybsn is compatible with python 2.7+ and python 3.

---
## PyBSN Repl - Interactive Shell

`pybsn-repl` is a powerful, interactive shell for the REST API. It is based on and requires python3 and ipython 7.0.

### Installing IPython 7
```bash
pip3 install ipython
```
* Note: make sure you use the `pip` module associated with `python3`. Often, it is available as `pip3`; otherwise you may want to try `python3 -m pip install ...` instead.

### Running pybsn-repl
```bash
./bin/pybsn-repl -H <controller_host> -u <user> -p <passwd>
```
**Note:** `pybsn-repl` requires `pybsn` to be available; you can either install it from `pip` (see above); or use it directly from the source by prefixing the
command with `PYTHONPATH=<dir>`, e.g.,

```bash
~/dev/pybsn $ PYTHONPATH=. ./bin/pybsn-repl -H <controller_host> -u <user> -p <passwd>
```

### Using pybsn-repl

PyBSN-reply presents an IPython shell to interact with the REST API.

It accepts any python expressions, and exposes the following variables as primary
entry points:
* `ctrl`: BigDbClient instance
* `root`: ctrl.root - a reference to the root node.

#### Node Hierarchy

You can explore the DB Rest API anchored on `root`. Child nodes in the rest API are
dynamically as python child properties of `root`. Hyphens (`-`) in the REST API
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
from pybsn.bcf.api import Api
api = Api("127.0.0.1", "admin", "adminadmin")

switches = api.get_switches()
print switches
[<pybsn.bcf.switch.Switch object at 0x10f3c7390>, <pybsn.bcf.switch.Switch object at 0x10f3c7790>, <pybsn.bcf.switch.Switch object at 0x10f3ec4d0>, <pybsn.bcf.switch.Switch object at 0x10f3ec610>, <pybsn.bcf.switch.Switch object at 0x10f3ec750>, <pybsn.bcf.switch.Switch object at 0x10f3ec890>, <pybsn.bcf.switch.Switch object at 0x10f3ec9d0>, <pybsn.bcf.switch.Switch object at 0x10f3ecb10>, <pybsn.bcf.switch.Switch object at 0x10f3ecc50>, <pybsn.bcf.switch.Switch object at 0x10f3ecd90>, <pybsn.bcf.switch.Switch object at 0x10f3eced0>, <pybsn.bcf.switch.Switch object at 0x10f3f6050>, <pybsn.bcf.switch.Switch object at 0x10f3f6190>, <pybsn.bcf.switch.Switch object at 0x10f3f62d0>]

for sw in switches:
   sw.disconnect()
```

---
## Contributing

If you'd like to contribute a feature or bugfix: Thanks! To make sure your
fix/feature has a high chance of being included, please read the following
guidelines:

1. Post a [pull request](https://github.com/Sovietaced/pybsn/compare/).
2. Make sure there are tests! We will not accept any patch that is not tested.
   It's a rare time when explicit tests aren't needed. If you have questions
   about writing tests for pybsn, please open a
   [GitHub issue](https://github.com/Sovietaced/pybsn/issues/new).

Please see `CONTRIBUTING.md` for more details on contributing and running test.

---

## License

Please see LICENSE at the top level of the repository.
