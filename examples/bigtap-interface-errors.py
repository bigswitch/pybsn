import pybcf
import argparse
import re

parser = argparse.ArgumentParser(description='Show interfaces with errors')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

args = parser.parse_args()

bt = pybcf.BigTap("http://%s:8082" % args.host, args.user, args.password)
topology = bt.root.applications.bigtap.topology

interfaces = []
for interface_type in ['core', 'filter', 'delivery', 'service']:
    for interface in topology[interface_type + '-interface']():
        interface.type = interface_type
        interfaces.append(interface)

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split('(\d+)', text) ]

def sort_key(interface):
    return (interface['switch'], natural_keys(interface['interface']))

for interface in sorted(interfaces, key=sort_key):
    if interface.count_rx_error > 0 or interface.count_xmit_error > 0:
        direction = interface.direction == "rx" and "<-" or "->"
        print interface.switch, interface.interface, interface.type, direction, interface.peer
        for k, v in interface._values.items():
            if re.match(r'count-[\w-]+-error', k) and v > 0:
                print "  %s: %u" % (k, v)
