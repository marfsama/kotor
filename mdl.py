#!/usr/bin/env python3

import argparse
import os

from functools import partial
from collections import OrderedDict

from tools import *

# based on xoreos/src/graphics/aurora/model_kotor.cpp from https://github.com/xoreos/xoreos

# size of file header. each offset in mdl must be adjusted by the header offset.
HEADER_OFFSET = 12

class NodeHeader:
    def __init__(self, file):
        self.parent_node = readu16(file)
        self.node_id = readu16(file)
        file.read(4+2) # unknown
        self.parent_node_start = readu32(file)
        self.position = readlist(readfloat, file, 3) # x,y,z
        self.rotation = readlist(readfloat, file, 4) # w,x,y,z
        self.childlist_offset = readu32(file)
        self.child_count = readu32(file)
        file.read(4) # copy of child_count
        self.controller_offset = readu32(file)
        self.controller_count = readu32(file)
        file.read(4) # copy of controller_count
        self.controller_data_start = readu32(file)
        self.controller_data_count = readu32(file)
        file.read(4) # copy of controller_data_count


    def read_node(self, file):
        file.seek(self.childlist_offset + HEADER_OFFSET)
        self.child_offsets = readlist(readu32, file, self.child_count)

    def __str__(self):
        return """{type_name}: {{parent_node: 0x{parent_node:x}, node_id: {node_id}, parent_node_start: {parent_node_start}, position: {position}, rotation: {rotation}, childlist_offset: 0x{childlist_offset:x}, child_count: {child_count}, controller_offset: {controller_offset}, controller_count: {controller_count}, controller_data_start: {controller_data_start}, controller_data_count: {controller_data_count}, child_offsets: {child_offsets}}}""".format(type_name=type(self).__name__, **vars(self))

class MeshHeader:
    def __init__(self, file):
        file.read(4+4) # unknown
        self.faces_offset = readu32(file);
        self.faces_count = readu32(file);
        file.read(4) # copy of faces_count
        self.bounding_box = (readlist(readfloat, file, 3), readlist(readfloat, file, 3))
        self.radius = readfloat(file)
        self.averange = readlist(readfloat, file, 3)
        self.diffuse = readlist(readfloat, file, 3)
        self.ambient = readlist(readfloat, file, 3)
        self.transparency_hint = readu32(file)
        self.texture_name = file.read(32).partition(b'\0')[0].decode("utf-8")

    def read_node(self, file):
        pass

    def __str__(self):
        return """{type_name}: {{faces_offset: 0x{faces_offset:x}, faces_count: {faces_count}, bounding_box: {bounding_box}, radius: {radius}, averange: {averange}, diffuse: {diffuse}, ambient: {ambient}, transparency_hint: {transparency_hint}, texture_name: {texture_name}}}""".format(type_name=type(self).__name__, **vars(self))

class NodeType:
    def __init__(self, name, bitfield, header_type = None):
        self.name = name
        self.bitfield = bitfield
        self.header_type = header_type

    def matches(self, value):
        return value & self.bitfield
    
    def __str__(self):
        return """{type_name}: {{name: {name}, bitfield: {bitfield}}}""".format(type_name=type(self).__name__, **vars(self))

NODE_TYPES = [
  NodeType("HEADER",    0x00000001, NodeHeader),
  NodeType("LIGHT",     0x00000002 ),
  NodeType("EMITTER",   0x00000004 ),
  NodeType("CAMERA",    0x00000008 ),
  NodeType("REFERENCE", 0x00000010 ),
  NodeType("MESH",      0x00000020, MeshHeader),
  NodeType("SKIN",      0x00000040 ),
  NodeType("ANIM",      0x00000080 ),
  NodeType("DANGLY",    0x00000100 ),
  NodeType("AABB",      0x00000200 ),
  NodeType("SABER",     0x00000800 )
]


class Header:
    def __init__(self, file):
        file.read(4) # skip first dword (always 0x0)
        self.mdl_size = readu32(file)
        self.mdx_size = readu32(file)

    def __str__(self):
        return """{name}: {{mdl_size: {mdl_size}, mdx_size: {mdx_size}}}""".format(name=type(self).__name__, **vars(self))

class GeometryHeader:
    def __init__(self, file):
        file.read(8) # unknown
        self.name = file.read(32).partition(b'\0')[0].decode("utf-8")
        self.node_offset = readu32(file)
        self.node_count = readu32(file)
        file.read(28) # unknown
        self.type = readu8(file)
        file.read(5) # unknown

    def __str__(self):
        return """{type_name}: {{name: {name}, node_offset: 0x{node_offset:x}, node_count: {node_count}, type: {type}}}""".format(type_name=type(self).__name__, **vars(self))

class ModelHeader:
    def __init__(self, file):
        self.classification = readu8(file)
        self.fogged = readu8(file)
        file.read(4)
        self.animation_start = readu32(file)
        self.animation_count = readu32(file)
        readu32(file) # copy of animation_count
        file.read(4)
        self.bounding_box = readlist(readfloat, file, 6)
        self.radius = readfloat(file)
        self.scale = readfloat(file)
        self.super_model = file.read(32).partition(b'\0')[0].decode("utf-8")

    def __str__(self):
        return """{type_name}: {{classification: {classification}, fogged: {fogged}, animation_start: 0x{animation_start:x}, animation_count: {animation_count}, bounding_box: {bounding_box}, radius: {radius}, scale: {scale}, super_model: {super_model}}}""".format(type_name=type(self).__name__, **vars(self))


class NamesHeader:
    def __init__(self, file):
        self.root_node = readu32(file)
        file.read(4) # unknown
        file.read(4) # copy of Header.mdx_size
        file.read(4) # unknown
        self.names_offset = readu32(file)
        self.names_count = readu32(file)
        file.read(4) # copy of names_count

    def __str__(self):
        return """{type_name}: {{root_node: 0x{root_node:x}, names_offset: 0x{names_offset:x}, names_count: {names_count}}}""".format(type_name=type(self).__name__, **vars(self))

class Node:
    def __init__(self, file):
        self.node_type_id = readu16(file)
        self.node_types = [node_type for node_type in NODE_TYPES if node_type.matches(self.node_type_id)]
        # set later
        self.headers = OrderedDict() # keep insertion order
        self.name = ""
        self.childs = []

    def get_childs(self):
        return self.childs

    def __str__(self):
        return """{type_name}: {{node_type_id: 0x{node_type_id:x}}}""".format(type_name=type(self).__name__, **vars(self))


def read_node_tree(file, node_offset):
    file.seek(node_offset + HEADER_OFFSET)
    node = Node(file)
    # read header
    for node_type in node.node_types:
        if node_type.header_type:
            node_type_header = node_type.header_type(file)
            node.headers[node_type.name] = node_type_header

    # read content of node type
    for name, node_type_header in node.headers.items():
         node_type_header.read_node(file)

    # read child nodes
    for child_offset in node.headers["HEADER"].child_offsets:
        node.childs.append(read_node_tree(file, child_offset))
    return node


def update_node_name(names, node, depth):
    node.name = names[node.headers["HEADER"].node_id]


def readModelFile(fileName):
    with open(fileName, "rb") as file:
        header = Header(file)
        print(header)
        geometry_header = GeometryHeader(file)
        print(geometry_header)
        model_header = ModelHeader(file)
        print(model_header)
        names_header = NamesHeader(file)
        print(names_header)
        # seek to start of names offset table
        file.seek(names_header.names_offset + HEADER_OFFSET)
        names_offsets = readlist(readu32, file, names_header.names_count)
        print(toHex(names_offsets))
        names = []
        for name_offset in names_offsets:
            file.seek(name_offset + HEADER_OFFSET)
            names.append(next(read_terminated_token(file, null_terminated)).decode("utf-8"))
        print(names)
        root_node = read_node_tree(file, names_header.root_node)
        # update names
        visit_tree(root_node, Node.get_childs, partial(update_node_name, names))
        # print tree
        visit_tree(root_node, Node.get_childs, lambda node, depth : print("  "*depth, node.headers["HEADER"].node_id, node.name, hex(node.node_type_id), *[node_type.name for node_type in node.node_types], *[header for name, header in node.headers.items()]))
        print(hex(file.tell()))

def parse_command_line():
    parser = argparse.ArgumentParser(description='Process MDL files.')
    parser.add_argument('input', help='path to mdl/mdx file')

    parsed = parser.parse_args()

    model = readModelFile(parsed.input)



def main():
    parse_command_line()

main()

