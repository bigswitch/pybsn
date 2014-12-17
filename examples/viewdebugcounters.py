#!/usr/bin/env python
#!/usr/bin/env python
help = """
This program displays the debug counters exposed by all switches in
the fabric in real time. Counters with zero values are not shown.

Keybindings:

  '?' - this message
  'q' - quit
  'j' or down-arrow - go down one line
  'k' or up-arrow - go up one line
  '/' - begin searching
  'L' - clear search
  'n' - go to next match
  'p' - go to previous match
  'z' - zero counters
  'Z' - unzero counters (show absolute values)
"""
import pybsn
import argparse
import time
import npyscreen
from collections import namedtuple

parser = argparse.ArgumentParser(description='View debug counters for all switches')

parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")
parser.add_argument('filter', nargs='*', help="Limit counters to those containing this string")

args = parser.parse_args()

bcf = pybsn.connect(args.host, args.user, args.password)

class DebugCounter(namedtuple("DebugCounter",
        ["name", "description", "value", "initial_value"])):
    pass

class DebugCounterSource(object):
    def __init__(self, bcf):
        self.bcf = bcf
        self.initial_values = {}

    def get_debug_counters(self):
        switch_counters = self.bcf.root.applications.bcf.info.statistic.switch_counter()
        for switch_counter in switch_counters:
            for counter in switch_counter['counter']:
                name = switch_counter['switch-name'] + ':' + counter['name']
                if not all(x in name for x in args.filter):
                    continue
                yield DebugCounter(
                    name=name,
                    description=counter['description'],
                    value=counter['value'],
                    initial_value=self.initial_values.get(name, 0))

    def zero(self):
        switch_counters = self.bcf.root.applications.bcf.info.statistic.switch_counter()
        for switch_counter in switch_counters:
            for counter in switch_counter['counter']:
                name = switch_counter['switch-name'] + ':' + counter['name']
                self.initial_values[name] = counter['value']

    def unzero(self):
        self.initial_values = {}

    def list(self):
        for c in self.get_debug_counters():
            if c.value != c.initial_value:
                yield c

class DebugCounterList(npyscreen.MultiLine):
    def __init__(self, *args, **keywords):
        super(DebugCounterList, self).__init__(*args, **keywords)

    def display_value(self, v):
        return "%s: %d" % (v.name, v.value - v.initial_value)

class DebugCounterForm(npyscreen.FormBaseNew):
    FRAMED = False

    def __init__(self, source, *args, **keywords):
        super(DebugCounterForm, self).__init__(*args, help=help, **keywords)
        self.source = source
        self.zero_time = None
        self.add_handlers({
            ord('q'): self.handle_quit,
            ord('z'): self.handle_zero,
            ord('Z'): self.handle_unzero,
            ord('/'): self.handle_search,
            ord('?'): self.handle_help,
        })

    def create(self):
        self.wStatus1 = self.add(npyscreen.Textfield, editable=False,
                                 rely=0, relx=0, color="CAUTION")
        self.wMain = self.add(DebugCounterList, rely=2, relx=0, max_height=-2)
        self.wDescription = self.add(npyscreen.Textfield, editable=False,
                                     rely=self.lines-3, relx=0)

    def beforeEditing(self):
        self.update_list()
        self.update_status()

    def update_list(self):
        self.wMain.values = list(self.source.list())
        self.wMain.update()

    def update_status(self):
        self.wStatus1.value = "Debug counters"
        self.wStatus1.value += " - updated %s" % time.asctime()
        if self.zero_time:
            self.wStatus1.value += " - zeroed %s" % self.zero_time
        self.wStatus1.value += " - press '?' for help"
        self.wStatus1.update()
        if self.wMain.values:
            counter = self.wMain.values[self.wMain.cursor_line]
            self.wDescription.value = "%s: %s" % (counter.name, counter.description)
        else:
            self.wDescription.value = ""
        self.wDescription.update()

    def while_waiting(self):
        self.update_list()
        self.update_status()

    def adjust_widgets(self):
        self.update_status()

    def handle_quit(self, ch):
        self.parentApp.switchForm(None)

    def handle_zero(self, ch):
        self.zero_time = time.asctime()
        self.source.zero()
        self.update_list()

    def handle_unzero(self, ch):
        self.zero_time = None
        self.source.unzero()
        self.update_list()

    def handle_search(self, ch):
        self.wMain.h_set_filter(ch)

    def handle_help(self, ch):
        self.h_display_help(ch)

class ViewDebugCountersApp(npyscreen.NPSAppManaged):
    keypress_timeout_default = 3
    def onStart(self):
        source = DebugCounterSource(bcf)
        self.addForm("MAIN", DebugCounterForm, source=source)

if __name__ == "__main__":
    App = ViewDebugCountersApp()
    try:
        App.run()
    except KeyboardInterrupt:
        pass
