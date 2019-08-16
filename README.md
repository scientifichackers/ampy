## ampy2

An experimental flavour of the original micropython tool from adafruit.

### Why?

This project aims to rectify the inherent problems that `ampy` and the underlying `pyboard.py` face, due to lack of a _proper_ automate-able interface in micropython itself.

These tools end up simulating a human on the REPL, which is not very ideal. (See - [#64](https://github.com/pycampers/ampy/issues/64))

### Ideas

- [ ] Easy building and flashing frozen micropython firmware. 
	- Initial work being done [here](https://github.com/micropython/micropython/pull/5003).
- [ ] RPC interface that works transparently over both serial and WiFi.
- [ ] Faster development cycles, similar to flutter's hot restart.
- [ ] Collaborative environment hat allows N developers to work on M devices at the same time.
- [ ] Automate-able API that other toolchains and GUIs can exploit.
- [ ] Install-able without a Python environment, by building distributable EXEs.

