#!/usr/bin/env bash

set -ex
make -C mpy-cross
make -C ${AMPY_BOARD_DIR} BOARD=${AMPY_BOARD} ESPIDF=${AMPY_ESPIDF}
