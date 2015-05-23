# pybsn
pybsn is a python interface to [Big Switch Network's](http://bigswitch.com) products

[ ![Codeship Status for floodlight/pybsn](https://codeship.com/projects/4004a2e0-e23e-0132-f512-3642858bbef8/status?branch=master)](https://codeship.com/projects/81432)
[![Build Status](https://travis-ci.org/floodlight/pybsn.svg)](https://travis-ci.org/floodlight/pybsn)
[![Coverage Status](https://coveralls.io/repos/floodlight/pybsn/badge.svg)](https://coveralls.io/r/floodlight/pybsn)
## Installation

```bash
pip install pybsn
```
---
## Example Usage

```python
from pybsn.bcf.api import Api
api = Api("127.0.0.1", "admin", "adminadmin",)

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
