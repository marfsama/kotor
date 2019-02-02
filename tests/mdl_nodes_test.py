#!/usr/bin/env python3

import kotor.model.nodes as nodes
import kotor.tools as tools
from .testutil import *
import io
import struct


def test_node_read():
    file = io.BytesIO(struct.pack("h", 1))
    node = nodes.Node(file, tools.Block("root",  0,  file))
    assert node
    assert node.node_type_id == 1

