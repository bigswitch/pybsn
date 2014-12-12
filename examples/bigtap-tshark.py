import pybcf
import argparse
import time
import re
import subprocess
import signal

finished = False
def sigint(signal, frame):
    global finished
    finished = True
signal.signal(signal.SIGINT, sigint)

parser = argparse.ArgumentParser(description='Display captured traffic in realtime')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

parser.add_argument('filter_interface', help="Filter interface to capture from")
parser.add_argument('--duration', '-d', type=int, default=60, help="Duration of the policy in seconds (0 for unlimited)")
parser.add_argument('--priority', '-P', type=int, default=100, help="Priority of the policy")

args = parser.parse_args()

bt = pybcf.BigTap("http://%s:8082" % args.host, args.user, args.password)

policies = bt.root.applications.bigtap.view.match(name='admin-view').policy

now = int(time.time())
name = 'tshark-%d' % now
policy = policies.match(name=name)

print "Installing policy", name

policy.put({
    'name': name,
    'action': 'capture',
    'priority' : args.priority,
})

policy.filter_group.match(name=args.filter_interface).put({
    'name': args.filter_interface,
})

policy.rule.match(sequence=1).put({
    'sequence': 1,
    'any-traffic': True,
})

policy.patch({
    'start-time': now,
    'duration': args.duration,
})

print "Waiting for policy to be applied"

while not finished:
    events = policy.policy_history.match(policy_event="installation complete")()
    if events:
        event = events[-1]
        if event.timestamp >= now:
            url = re.search(r'http://.*\.pcap', event.event_detail).group()
            break
    time.sleep(0.5)

print "Capturing packets"

tshark = subprocess.Popen(["tshark", "-i-"], stdin=subprocess.PIPE)

offset = 0
while not finished:
    r = bt.session.get(url, stream=True, headers={ 'Range': 'bytes=%d-' % offset })
    if r.status_code == 416:
        time.sleep(1.0)
        continue
    r.raise_for_status()
    for chunk in r.iter_content(128):
        tshark.stdin.write(chunk)
        offset += len(chunk)
    if offset == 0:
        time.sleep(1.0)

tshark.stdin.close()
tshark.wait()

policy.delete()
