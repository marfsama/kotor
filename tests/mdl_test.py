#!/usr/bin/env python3

import kotor.model.base as base
import io

def test_read_array():
    file = io.BytesIO(bytearray([ 0x01,  0x02,  0x03,  0x04,  0x05,  0x00,  0x00,  0x00,  0x05,  0x00,  0x00,  0x00 ]) )
    array = base.Array(file)
    assert array
    assert array.offset == 0x04030201
    assert array.used_entries == 5
    assert array.allocated_entries == 5


def test_array_read_data():
    pass
