from machine import Timer

from .settings import DISCOVERY_POLL_MS, RECEIVE_POLL_MS
from .code_receiver import create_code_receiever
from .discovery_receiver import create_discovery_receiver

port, code_receiver = create_code_receiever()
Timer(1).init(period=DISCOVERY_POLL_MS, callback=code_receiver)
Timer(2).init(period=RECEIVE_POLL_MS, callback=create_discovery_receiver(port))
