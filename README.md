## ampy2

An experimental flavour of the original micropython tool from adafruit.

### Why?

This project aims to rectify the inherent problems that `ampy` and the underlying `pyboard.py` face, due to lack of a _proper_  serial interface in micropython itself.

These tools end up simulating a human on the REPL, which is not very ideal. (See - [#64](https://github.com/pycampers/ampy/issues/64))

### Ideas

- [x] Easy building and flashing frozen micropython firmware. 

    `$ ampy build` is a command that will detect the user's micropython board, build and flash firmware for it.
- [ ] RPC interface that works transparently over both serial and WiFi.
	- [x] RPC over WiFi, using `$ ampy run`
	- [ ] RPC over Serial
- [ ] Faster development cycles, similar to flutter's hot restart.
- [ ] Collaborative environment hat allows N developers to work on M devices at the same time.
- [ ] Expose an API that other toolchains and GUIs can exploit.
- [ ] A plugin system that allows 3rd parties to extend ampy's functionality. (Like [cargo plugins](https://lib.rs/development-tools/cargo-plugins))
- [ ] Install-able without a Python environment, by building distributable EXEs.

### Try

```
$ pip install -e git+https://github.com/scientifichackers/ampy.git@ampy2#egg=ampy2
$ ampy2 --help
$ ampy2 build --dev  # build (and flash) the development firmware
```
