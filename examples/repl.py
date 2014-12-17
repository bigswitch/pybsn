import pybcf
import argparse
import IPython
from IPython.config.loader import Config

parser = argparse.ArgumentParser(description='Start an IPython shell to interact with the REST API')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

args = parser.parse_args()

ctrl = pybcf.connect(args.host, args.user, args.password)

config = Config()
config.TerminalInteractiveShell.banner1 = """\
Available variables:
  - ctrl: BigDbClient instance
  - root: ctrl.root
"""
config.TerminalInteractiveShell.confirm_exit = False

IPython.start_ipython(
    argv=[],
    user_ns=dict(ctrl=ctrl, root=ctrl.root),
    config=config)
