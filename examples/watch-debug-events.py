#!/usr/bin/env python
import pybsn
import argparse
import time
import textwrap
import re

parser = argparse.ArgumentParser(description='Display debug events in realtime')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

args = parser.parse_args()

MAX_EVENT_RATE = 10

ctrl = pybsn.connect(args.host, args.user, args.password)
events = ctrl.root.core.controller.debugeventinfo.event

def sort_key(x):
    return -x['event-instance-id']

latest_id_by_name = {}

for event in events.match(num_of_events=1)():
    latest_id_by_name[event['mod-event-name']] = event['event-instance-id']

while True:
    new_events = []
    for event in events.match(num_of_events=1)():
        name = str(event['mod-event-name'])
        latest_id = latest_id_by_name.get(name)
        if latest_id is None or event['event-instance-id'] < latest_id:
            new_latest_id = latest_id
            for new_event in events.match(num_of_events=MAX_EVENT_RATE, mod_event_name=name)():
                if latest_id is None or new_event['event-instance-id'] < latest_id:
                    new_events.append(new_event)
                    new_latest_id = min(new_event['event-instance-id'], new_latest_id)
            latest_id_by_name[name] = new_latest_id

    for event in sorted(new_events, key=sort_key):
        description = "\n" + textwrap.fill(
            re.sub(r'\s+', ' ', event['datastring']),
            initial_indent='  ',
            subsequent_indent='  ',
            width=78)
        print event['timestamp'], event['mod-event-name'], description

    time.sleep(0.1)
