from time import sleep

import network
from machine import Timer

from . import command_server
from . import discovery_server
from . import virtual_term
from .settings import DISCOVERY_POLL_MS, RECEIVE_POLL_MS, DISCOVERY_PORT, COMMANDS_PORT

timers = [Timer(-1), Timer(-1)]

timers[0].init(period=DISCOVERY_POLL_MS, callback=command_server.main())
print("[ampy] Command server running on port:", COMMANDS_PORT)

timers[1].init(period=RECEIVE_POLL_MS, callback=discovery_server.main())
print("[ampy] Discovery server running on port:", DISCOVERY_PORT)

virtual_term.main()
print("[ampy] Started virtual terminal")

print("[ampy] Configuring WiFi...")
ap_if = network.WLAN(network.AP_IF)
ap_if.active(True)

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(";;", "barfoo99")


def main():
    try:
        try:
            print("[ampy] Running user code...")
            __import__("user_main").main()
        except ImportError:
            print("[ampy] User code not found! Wait for 1s...")
            sleep(1)
    except KeyboardInterrupt:
        try:
            print("[ampy] Quickly press Ctrl+C again to exit >")
            sleep(1)
        except KeyboardInterrupt:
            for t in timers:
                t.deinit()
            raise


while True:
    main()
