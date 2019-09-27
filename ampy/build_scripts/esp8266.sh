#!/usr/bin/env bash

set -ex
export PATH=${AMPY_XTENSA_PATH}/bin:$PATH
make -C mpy-cross
make -C ${AMPY_BOARD_DIR}
