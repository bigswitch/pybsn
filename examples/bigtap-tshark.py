#!/usr/bin/env python
import pybsn
import argparse
import time
import re
import subprocess
import signal
import os

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
parser.add_argument('--rule', '-r', default='all', choices=['all', 'tcp-syn'], help="Filter rule")
parser.add_argument('--tool', '-t', default='tshark', type=str, help="Packet display tool (tshark or wireshark")

args = parser.parse_args()

bt = pybsn.connect(args.host, args.user, args.password)

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

if args.rule == 'all':
    policy.rule.match(sequence=1).put({
        'sequence': 1,
        'any-traffic': True,
    })
elif args.rule == 'tcp-syn':
    policy.rule.match(sequence=1).put({
        'sequence': 1,
        'ether-type': 0x0800,
        'ip-proto': 6,
        'tcp-flags': 2,
        'tcp-flags-mask': 63,
    })

policy.patch({
    'start-time': now,
    'duration': args.duration,
})

try:
    print "Waiting for policy to be applied"

    while not finished:
        events = policy.policy_history.match(policy_event="installation complete")()
        if events:
            event = events[-1]
            if event['timestamp'] >= now:
                url = re.search(r'http://.*\.pcap', event['event-detail']).group()
                break
        time.sleep(0.5)

    print "Capturing packets"

    if 'tshark' in args.tool:
        tool_args = ['-i-']
    elif 'wireshark' in args.tool:
        tool_args = ['-i-', '-k']
    else:
        raise Exception("unknown tool %r" % args.tool)

    tshark = subprocess.Popen([args.tool] + tool_args, stdin=subprocess.PIPE, preexec_fn=os.setsid)

    try:
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
    finally:
        tshark.stdin.close()
        tshark.wait()

finally:
    policy.delete()
