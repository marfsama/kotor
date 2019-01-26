#!/usr/bin/env python3

import kotor.model.base as base
import io

def test_read_array():
    file = io.BytesIO(b"\x01\x02\x03\x04\x05\x00\x00\x00\x05\x00\x00\x00")
    array = base.Array(file)
    assert array
    assert array.offset == 0x04030201
    assert array.used_entries == 5
    assert array.allocated_entries == 5
