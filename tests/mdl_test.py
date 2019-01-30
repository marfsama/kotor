#!/usr/bin/env python3

import kotor.model.base as base
import kotor.tools as tools
import io

def test_read_array():
    file = io.BytesIO(bytearray([ 0x01,  0x02,  0x03,  0x04,  0x05,  0x00,  0x00,  0x00,  0x05,  0x00,  0x00,  0x00 ]) )
    array = base.Array(file)
    assert array
    assert array.offset == 0x04030201
    assert array.used_entries == 5
    assert array.allocated_entries == 5


def test_array_read_data():
    file = SeekLoggingBytesIO(bytearray([ 0x01,  0x02,  0x03,  0x04,  0x04,  0x00,  0x00,  0x00,  0x05,  0x00,  0x00,  0x00,  0x01,  0x02, 0x03, 0x04,  0x05 ]) )
    array = base.Array(file)
    array.read_data(file, tools.readu8)
    assert 0x04030201 in file.seeks
    assert len(array.data) == 4
    assert array.data == [1, 2, 3, 4]
    assert file.tell() == 17


def test_array_use_block():
    file = SeekLoggingBytesIO(bytearray([ 0x01,  0x02,  0x03,  0x04,  0x04,  0x00,  0x00,  0x00,  0x05,  0x00,  0x00,  0x00,  0x01,  0x02, 0x03, 0x04,  0x05 ]) )
    array = base.Array(file)
    root_block = tools.Block("root",  0)
    array.read_data(file, tools.readu8,  root_block.start_block("foo",  file))
    assert len(root_block.blocks) == 1


class SeekLoggingBytesIO(io.BytesIO):
    def __init__(self,  data):
        super(SeekLoggingBytesIO,  self).__init__(data)
        self.seeks = []
        
    def seek(self,  value):
        self.seeks.append(value)
