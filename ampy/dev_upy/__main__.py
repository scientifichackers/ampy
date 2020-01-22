from . import command_server
from . import config
from . import discovery_server
from . import remote_term
from . import settings
from .repl_man import ReplMan


def main():
    p1 = discovery_server.main()
    p2 = command_server.main()
    p3 = remote_term.main()

    def poll(t):
        p1(t)
        p2(t)
        p3(t)

    return poll


config.load()

print("[ampy] Configuring WiFi...")
config.get_ap_if()
config.get_sta_if()

timer = config.get_timer()
timer.init(period=settings.TIMER_POLL_MS, callback=main())
print("[ampy] Discovery server running on port:", settings.DISCOVERY_PORT)
print("[ampy] Command server running on port:", settings.COMMANDS_PORT)
print("[ampy] Virtual terminal running on port:", settings.TERMINAL_PORT)

try:
    ReplMan.get_instance().main()
finally:
    timer.deinit()
