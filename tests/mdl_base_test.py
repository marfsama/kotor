#!/usr/bin/env python3

import kotor.model.base as base
import kotor.tools as tools
from .testutil import *
import io
import struct


def test_array_read():
    file = io.BytesIO(struct.pack("3i",  0x04030201,  5, 5))
    array = base.Array(file)
    assert array
    assert array.offset == 0x04030201
    assert array.used_entries == 5
    assert array.allocated_entries == 5


def test_array_read_data():
    file = SeekLoggingBytesIO(bytearray([0x01,  0x02,  0x03,  0x04,  0x04,  0x00,  0x00,  0x00,  0x05,  0x00,  0x00,  0x00,  0x01,  0x02, 0x03, 0x04,  0x05]))
    array = base.Array(file)
    array.read_data(file, tools.readu8)
    assert 0x04030201 in file.seeks
    assert len(array.data) == 4
    assert array.data == [1, 2, 3, 4]
    assert file.tell() == 17


def test_array_use_block():
    file = SeekLoggingBytesIO(bytearray([0x01,  0x02,  0x03,  0x04,  0x04,  0x00,  0x00,  0x00,  0x05,  0x00,  0x00,  0x00,  0x01,  0x02, 0x03, 0x04,  0x05]))
    array = base.Array(file)
    root_block = tools.Block("root",  0,  file)
    array.read_data(file, tools.readu8,  root_block.start_block("foo",  0))
    assert len(root_block.blocks) == 1
    block = root_block.blocks[0];
    assert block.name == "foo"
    assert block.start == 12
    assert block.end == 12+5

def test_array_serialize():
    file = SeekLoggingBytesIO(bytearray([0x01,  0x02,  0x03,  0x04,  0x04,  0x00,  0x00,  0x00,  0x05,  0x00,  0x00,  0x00,  0x01,  0x02, 0x03, 0x04,  0x05]))
    array = base.Array(file)
    array.read_data(file, tools.readu8)
    serialized = array.__serialize__()
    assert 'offset' in serialized
    assert 'used_entries' in serialized
    assert 'allocated_entries' in serialized


def test_face_read():
    file = io.BytesIO(struct.pack("4fi6h",  1.0, 2.0, 3.0, 4.0, 5, 10, 11, 12,  20,  21,  22))
    face = base.Face(file)
    assert face.plane_normal.x == 1.0
    assert face.plane_normal.y == 2.0
    assert face.plane_normal.z == 3.0
    assert face.plane_distance == 4.0
    assert face.adjected_faces == [10,  11,  12]
    assert face.vertex_indices == [20,  21,  22]


def test_face_serialize():
    file = io.BytesIO(struct.pack("4fi6h",  1.0, 2.0, 3.0, 4.0, 5, 10, 11, 12,  20,  21,  22))
    face = base.Face(file)
    serialized = face.__serialize__()
    assert 'plane_normal' in serialized
    assert 'plane_distance' in serialized
    assert 'adjected_faces' in serialized
    assert 'vertex_indices' in serialized


def test_vertex_read():
    file = io.BytesIO(struct.pack("3f",  9.0, 8.0, 7.0))
    vertex = base.Vertex(file)
    assert vertex.x == 9.0
    assert vertex.y == 8.0
    assert vertex.z == 7.0


def test_vertex_serialize():
    file = io.BytesIO(struct.pack("3f",  9.0, 8.0, 7.0))
    vertex = base.Vertex(file)
    serialized = vertex.__serialize__()
    assert 'x' in serialized
    assert 'y' in serialized
    assert 'z' in serialized


def test_quaternion_read():
    file = io.BytesIO(struct.pack("4f", 10.0,  9.0, 8.0, 7.0))
    quaternion = base.Quaternion(file)
    assert quaternion.w == 10.0
    assert quaternion.x == 9.0
    assert quaternion.y == 8.0
    assert quaternion.z == 7.0


def test_quaternion_serialize():
    file = io.BytesIO(struct.pack("4f", 10.0,  9.0, 8.0, 7.0))
    quaternion = base.Quaternion(file)
    serialized = quaternion.__serialize__()
    assert 'w' in serialized
    assert 'x' in serialized
    assert 'y' in serialized
    assert 'z' in serialized
