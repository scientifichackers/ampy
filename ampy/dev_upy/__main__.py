import network
from machine import Timer

from . import virtual_term
from . import command_server
from . import discovery_server
from .settings import DISCOVERY_POLL_MS, RECEIVE_POLL_MS, DISCOVERY_PORT, COMMANDS_PORT

print("[ampy] Configuring WiFi...")
ap_if = network.WLAN(network.AP_IF)
ap_if.active(True)

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(";;", "barfoo99")

timers = []

t = Timer(-1)
t.init(period=DISCOVERY_POLL_MS, callback=command_server.main())
timers.append(t)
print("[ampy] Command server running on port:", COMMANDS_PORT)

t = Timer(-1)
t.init(period=RECEIVE_POLL_MS, callback=discovery_server.main())
timers.append(t)
print("[ampy] Discovery server running on port:", DISCOVERY_PORT)

virtual_term.main()
print("[ampy] Started virtual terminal")

try:
    while True:
        pass
except KeyboardInterrupt:
    for t in timers:
        t.deinit()
