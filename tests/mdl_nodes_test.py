#!/usr/bin/env python3

import kotor.model.nodes as nodes
import kotor.tools as tools
from .testutil import *
import io
import struct


def test_node_read():
    file = io.BytesIO(struct.pack("h", 0x21))
    node = nodes.Node(file, tools.Block("root",  0,  file))
    assert node
    assert node.node_type_id == 0x21
    assert [node_type.name for node_type in node.node_types] == ['HEADER',  'MESH']


def test_node_get_childs():
    file = io.BytesIO(struct.pack("h", 0x21))
    node = nodes.Node(file, tools.Block("root",  0,  file))
    node.childs.append('foo')
    assert node.get_childs() == ['foo']


def test_node_serialize():
    file = io.BytesIO(struct.pack("h", 1))
    node = nodes.Node(file, tools.Block("root",  0,  file))
    serialized = node.__serialize__()
    assert 'node_type_id' in serialized
    assert 'node_types' in serialized
    assert 'name' in serialized
    assert 'headers' in serialized


def assert_vertex(vertex):
    return [vertex.x, vertex.y, vertex.z]


def assert_quaternion(quaternion):
    return [quaternion.w, quaternion.x, quaternion.y, quaternion.z]
    

def assert_array(array):
    return [array.offset, array.used_entries, array.allocated_entries]


def test_node_header_read():
    input = struct.pack("=hh hhh i fff ffff iii iii iii", 1, 2, 3, 4, 5, 0x06070809, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 1, 2, 3, 2, 3, 4, 3, 4, 5)
    print(input)
    file = io.BytesIO(input)
    node_header = nodes.NodeHeader(file, tools.Block("root",  0,  file))
    assert node_header
    assert node_header.parent_node == 1
    assert node_header.node_id == 2
    assert node_header.unknown == bytearray([3, 0, 4, 0, 5, 0])
    assert node_header.parent_node_start == 0x06070809
    assert node_header.position.x == 1
    assert assert_vertex(node_header.position) == [1, 2, 3]
    assert assert_quaternion(node_header.rotation) == [4, 5, 6, 7]
    assert assert_array(node_header.child_offsets) == [1, 2, 3]
    assert assert_array(node_header.controllers) == [2, 3, 4]
    assert assert_array(node_header.controller_data) == [3, 4, 5]
