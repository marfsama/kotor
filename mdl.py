#!/usr/bin/env python3

import argparse
import os

from functools import partial
from collections import OrderedDict

from tools import *

# based on xoreos/src/graphics/aurora/model_kotor.cpp from https://github.com/xoreos/xoreos

# size of file header. each offset in mdl must be adjusted by the header offset.
HEADER_OFFSET = 12

class Block:
    """
        Block of data read from the file. It is specified by it's start and length.
    """
    def __init__(self, name, start, file=None):
        self.start = start
        self.end = start
        self.name = name
        self.file = file
        self.blocks = []
        pass

    def start_block(self, name, start):
        block = Block(name, start)
        self.blocks.append(block)
        return block

    def block(self, name, file):
        block = Block(name, 0, file)
        self.blocks.append(block)
        return block

    def __enter__(self):
        if self.file:
            self.start = self.file.tell()
        return self

    def __exit__(self, type, value, traceback):
        self.close_block(self.file.tell())

    def close_block(self, end):
        self.end = end

    def get_childs(self):
        return self.blocks

    def sort(self):
        self.blocks.sort(key=lambda block: block.start)


    def __str__(self):
        return "{}, {}".format(self.start, self.end)

class NodeHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("NodeHeader", file):
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
            self.controller_data_offset = readu32(file)
            self.controller_data_count = readu32(file)
            file.read(4) # copy of controller_data_count

        # read later
        self.child_offsets = []
        self.controllers = []
        self.controller_data = []

    def read_node(self, file):
        file.seek(self.childlist_offset + HEADER_OFFSET)
        with self.parent_block.block("NodeHeader.child_offsets", file):
            self.child_offsets = readlist(readu32, file, self.child_count)

        if self.controller_count > 0:
            file.seek(self.controller_offset + HEADER_OFFSET)
            with self.parent_block.block("Controller.array", file):
                self.controllers = readlist(Controller, file, self.controller_count)

            file.seek(self.controller_data_offset + HEADER_OFFSET)
            with self.parent_block.block("Controller.data", file):
                self.controller_data = readlist(readfloat, file, self.controller_data_count)

    def __str__(self):
        return """{type_name}: {{parent_node: 0x{parent_node:x}, node_id: {node_id}, parent_node_start: {parent_node_start}, position: {position}, rotation: {rotation}, childlist_offset: 0x{childlist_offset:x}, child_count: {child_count}, controller_offset: 0x{controller_offset:x}, controller_count: {controller_count}, controller_data_offset: 0x{controller_data_offset:x}, controller_data_count: {controller_data_count}, child_offsets: {child_offsets}}}""".format(type_name=type(self).__name__, **vars(self))

class Controller:
    def __init__(self, file):
        self.controller_type = readu32(file)
        file.read(2) # unknown
        self.rows = readu16(file)
        self.timekey_offset = readu16(file)
        self.datakey_offset = readu16(file)
        self.columns = readu8(file)
        file.read(3) # unknown
            

    def __str__(self):
        return """{type_name}: {{controller_type: {controller_type}, rows: {rows}, columns: {columns}, timekey_offset: {timekey_offset}, datakey_offset: {datakey_offset}}}""".format(type_name=type(self).__name__, **vars(self))
    

class MeshHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("MeshHeader", file):
            file.read(4+4) # unknown
            self.faces_offset = readu32(file);
            self.faces_count = readu32(file);
            file.read(4) # copy of faces_count
            self.bounding_box = (readlist(readfloat, file, 3), readlist(readfloat, file, 3))
            self.radius = readfloat(file)  # radius of bounding sphere
            self.averange = readlist(readfloat, file, 3) # midpoint of bounding sphere
            self.diffuse = readlist(readfloat, file, 3)
            self.ambient = readlist(readfloat, file, 3)
            self.transparency_hint = readu32(file)
            self.texture_name = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.texture_name2 = file.read(32).partition(b'\0')[0].decode("utf-8")
            file.read(24) # unknown
            # read array where the vertex counts are saved. array always has size 1.
            self.vertex_count_offset = readu32(file);
            self.vertex_count_count = readu32(file);
            file.read(4) # copy of vertex_count_count
            # read array where the vertex offsets are saved. array always has size 1.
            self.vertex_offset_offset = readu32(file);
            self.vertex_offset_count = readu32(file);
            if self.vertex_count_count != 1 or self.vertex_offset_count != 1:
                raise ValueError("Illegal vertex array count. Only 1 is supported at the moment.")
            file.read(4) # copy of vertex_offset_count
            file.read(12) # another unknown array (offset, count, copy of count)
            file.read(24 + 16) # other unknown stuff
            self.mdx_structure_size = readu32(file)
            file.read(8) # unknown
            self.vertex_normals_offset = readu32(file);
            file.read(4) # unknown
            self.uv_offset1 = readu32(file)
            self.uv_offset2 = readu32(file)
            file.read(24) # unknown
            self.vertex_count  = readu16(file)
            self.texture_count = readu16(file)
            file.read(2) # unknown
            self.shadow = readu16(file) != 0
            self.render = readu16(file) != 0
            file.read(10) # unknown
#	    if (ctx.kotor2)
            file.read(8) # unknown

            self.mdx_offset = readu32(file)
            self.vertex_coordinates_offset = readu32(file)

        # read later
        self.vertex_count_array = []
        self.vertex_offset_array = []
        self.faces = []
        self.vertices = []

    def read_node(self, file):
        # read vertex count array and vertex offset array
        file.seek(self.vertex_count_offset+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.vertex_count_array", file):
            self.vertex_count_array = readlist(readu32, file, self.vertex_count_count)

        file.seek(self.vertex_offset_offset+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.vertex_offset_array", file):
            self.vertex_offset_array = readlist(readu32, file, self.vertex_offset_count)
            # note: directly after this array there is an unknown 32bit value.

        # read faces
        file.seek(self.faces_offset+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.face_array", file):
            self.faces = readlist(Face, file, self.faces_count)
        
        # read vertex coordinates
        file.seek(self.vertex_coordinates_offset+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.vertex_array", file):
            self.vertices = readlist(Vector, file, self.vertex_count)

        # read vertex indices
        file.seek(self.vertex_offset_array[0]+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.vertex_indices_array", file):
            self.vertex_indices = readlist(readu16, file, self.vertex_count_array[0])


    def __str__(self):
        return """{type_name}: {{faces_offset: 0x{faces_offset:x}, faces_count: {faces_count}, bounding_box: {bounding_box}, radius: {radius}, averange: {averange}, diffuse: {diffuse}, ambient: {ambient}, transparency_hint: {transparency_hint}, texture_name: {texture_name}, texture_name2: {texture_name2}, vertex_count_offset: 0x{vertex_count_offset:x}, vertex_count_count: {vertex_count_count}, vertex_offset_offset: 0x{vertex_offset_offset:x}, vertex_offset_count: {vertex_offset_count}, mdx_structure_size: {mdx_structure_size}, vertex_normals_offset: 0x{vertex_normals_offset:x}, uv_offset1: 0x{uv_offset1:x}, uv_offset2: 0x{uv_offset2:x}, vertex_count: {vertex_count}, texture_count: {texture_count}, shadow: {shadow}, render: {render}, mdx_offset: 0x{mdx_offset:x}, vertex_coordinates_offset: 0x{vertex_coordinates_offset:x}, vertex_count_array: {vertex_count_array}, vertex_offset_array: {vertex_offset_array}, faces: [{facesstr}], vertices: [{verticesstr}], vertex_indices: [{vertex_indices}] }}""".format(type_name=type(self).__name__, **vars(self), facesstr=", ".join([str(face) for face in self.faces]), verticesstr=", ".join([str(vertex) for vertex in self.vertices]))

class Face:
    def __init__(self, file):
        self.plane_normal = Vector(file)
        self.plane_distance = readfloat(file)
        self.surface = readu32(file)
        self.adjected_faces = readlist(readu16, file, 3)
        self.vertex_indices = readlist(readu16, file, 3)

    def __str__(self):
        return """{type_name}: {{plane_normal: {plane_normal}, plane_distance: {plane_distance}, surface: {surface}, adjected_faces: {adjected_faces}, vertex_indices: {vertex_indices}}}""".format(type_name=type(self).__name__, **vars(self))

class Vector:
    def __init__(self, file):
        self.x = readfloat(file)
        self.y = readfloat(file)
        self.z = readfloat(file)
    def __str__(self):
        return """{{{x}, {y}, {z}}}""".format(**vars(self))


class SkinMeshHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("SkinMeshHeader", file):
            file.read(20) # unknown
            self.bone_map_offset = readu32(file)
            self.bone_map_count = readu32(file)
            self.unknown_array1_offset = readu32(file)
            self.unknown_array1_count = readu32(file)
            file.read(4) # copy of unknown_array1_count
            self.unknown_array2_offset = readu32(file)
            self.unknown_array2_count = readu32(file)
            file.read(4) # copy of unknown_array2_count
            self.unknown_array3_offset = readu32(file)
            self.unknown_array3_count = readu32(file)
            file.read(4) # copy of unknown_array3_count
            self.bone_nodes = readlist(readu16, file, 15) # list of nodes which can affect vertices from this node
            file.read(6) # unknown
        # read later
        self.bone_map = []

    def read_node(self, file):
        # read bone map
        file.seek(self.bone_map_offset+HEADER_OFFSET)
        print(hex(self.bone_map_offset), self.bone_map_count, hex(self.unknown_array1_offset), self.unknown_array1_count, hex(self.unknown_array2_offset), self.unknown_array2_count, hex(self.unknown_array3_offset), self.unknown_array3_count)
        with self.parent_block.block("SkinMeshHeader.bone_map", file):
            self.bone_map = readlist(readu32, file, self.bone_map_count)

        file.seek(self.unknown_array1_offset+HEADER_OFFSET)
        with self.parent_block.block("SkinMeshHeader.unknown_array1", file):
            self.unknown_array1 = readlist(readfloat, file, self.unknown_array1_count*4)
    
        file.seek(self.unknown_array2_offset+HEADER_OFFSET)
        with self.parent_block.block("SkinMeshHeader.unknown_array2", file):
            self.unknown_array2 = readlist(readfloat, file, self.unknown_array2_count*3)

        file.seek(self.unknown_array3_offset+HEADER_OFFSET)
        with self.parent_block.block("SkinMeshHeader.unknown_array3", file):
            self.unknown_array3 = readlist(readfloat, file, self.unknown_array3_count)

    def __str__(self):
        return """{type_name}: {{bone_map_offset: 0x{bone_map_offset:x}, bone_map_count: {bone_map_count}, bone_nodes: {bone_nodes}}}""".format(type_name=type(self).__name__, **vars(self))

class DanglyMeshHeader:
    def __init__(self, file, parent_block):
        with parent_block.block("DanglyMeshHeader", file):
            self.constraints_offset = readu32(file)
            self.constraints_size = readu32(file)
            file.read(4) # copy of constraints_size
            self.displacement = readfloat(file)
            self.tightness = readfloat(file)
            self.period = readfloat(file)
            file.read(4) # unknown

    def read_node(self, file):
        pass

    def __str__(self):
        return """{type_name}: {{constraints_offset: 0x{constraints_offset:x}, constraints_size: {constraints_size}, displacement: {displacement}, tightness: {tightness}, period: {period}}}""".format(type_name=type(self).__name__, **vars(self))


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
  NodeType("SKIN",      0x00000040, SkinMeshHeader),
  NodeType("ANIM",      0x00000080 ),
  NodeType("DANGLY",    0x00000100, DanglyMeshHeader),
  NodeType("AABB",      0x00000200 ),
  NodeType("SABER",     0x00000800 )
]


class Header:
    def __init__(self, file, parent_block):
        with parent_block.block("Header", file):
            file.read(4) # skip first dword (always 0x0)
            self.mdl_size = readu32(file)
            self.mdx_size = readu32(file)

    def __str__(self):
        return """{name}: {{mdl_size: {mdl_size}, mdx_size: {mdx_size}}}""".format(name=type(self).__name__, **vars(self))


class GeometryHeader:
    def __init__(self, file, parent_block):
        with parent_block.block("GeometryHeader", file):
            file.read(8) # unknown
            self.name = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.node_offset = readu32(file)
            self.node_count = readu32(file)
            file.read(28) # unknown
            self.type = readu8(file)
            file.read(3) # unknown

    def __str__(self):
        return """{type_name}: {{name: {name}, node_offset: 0x{node_offset:x}, node_count: {node_count}, type: {type}}}""".format(type_name=type(self).__name__, **vars(self))

class ModelHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("ModelHeader", file):
            self.geometry_flags = readu16(file)
            self.classification = readu8(file)
            self.fogged = readu8(file)
            file.read(4)
            self.animation_start = readu32(file)
            self.animation_count = readu32(file)
            file.read(4) # copy of animation_count
            file.read(4) # unknown
            self.bounding_box = readlist(readfloat, file, 6)
            self.radius = readfloat(file)
            self.scale = readfloat(file)
            self.super_model = file.read(32).partition(b'\0')[0].decode("utf-8")
            # read later
            self.animation_offsets = []
            self.animations = []

    def read_animations(self, file):
        file.seek(self.animation_start+HEADER_OFFSET)
        with self.parent_block.block("Animations.offset_array", file):
            self.animation_offsets = readlist(readu32, file, self.animation_count)

        for offset in self.animation_offsets:
            file.seek(offset+HEADER_OFFSET)
            animation_header = AnimationHeader(file, self.parent_block)
            animation_header.read_events(file)
            self.animations.append(animation_header)


    def __str__(self):
        return """{type_name}: {{classification: {classification}, fogged: {fogged}, animation_start: 0x{animation_start:x}, animation_count: {animation_count}, bounding_box: {bounding_box}, radius: {radius}, scale: {scale}, super_model: {super_model}, animation_offsets: [{animation_offsets_str}]}}""".format(type_name=type(self).__name__, **vars(self), animation_offsets_str=", ".join([hex(offset) for offset in self.animation_offsets]))

class AnimationHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        self.geometry_header = GeometryHeader(file, parent_block)
        with parent_block.block("AnimationHeader", file):
            self.length = readfloat(file)
            self.transition_time = readfloat(file)
            self.name = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.events_offset = readu32(file)
            self.events_count = readu32(file)
            file.read(4) # copy of events_count
            file.read(4) # unknown
            self.events = []
        # TODO: read animation nodes from geometry header

    def read_events(self, file):
        if self.events_count > 0:
            file.seek(self.events_offset + HEADER_OFFSET)
            with self.parent_block.block("Animations.events", file):
                self.events = readlist(Event, file, self.events_count)

    def __str__(self):
        return """{type_name}: {{geometry_header: {geometry_header}, length: {length}, transition_time: {transition_time}, name: {name}, events_offset: 0x{events_offset:x}, events_count: {events_count}, events: [{eventsstr}]}}""".format(type_name=type(self).__name__, **vars(self), eventsstr=", ".join([str(event) for event in self.events]))

class Event:
    def __init__(self, file):
        self.time = readfloat(file)
        self.name = file.read(32).partition(b'\0')[0].decode("utf-8")

    def __str__(self):
        return """{{{name}@{time}}}""".format(type_name=type(self).__name__, **vars(self))


class NamesHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("NamesHeader", file):
            self.root_node = readu32(file)
            file.read(4) # unknown
            file.read(4) # copy of Header.mdx_size
            file.read(4) # unknown
            self.names_offset = readu32(file)
            self.names_count = readu32(file)
            file.read(4) # copy of names_count

    def read_names(self, file):
        # seek to start of names offset table
        file.seek(self.names_offset + HEADER_OFFSET)
        with self.parent_block.block("Names.offset_array", file):
            names_offsets = readlist(readu32, file, self.names_count)

        self.names = []
        block = self.parent_block.start_block("Names", names_offsets[0] + HEADER_OFFSET)
        for name_offset in names_offsets:
            file.seek(name_offset + HEADER_OFFSET)
            self.names.append(next(read_terminated_token(file, null_terminated)).decode("utf-8"))
        block.close_block(file.tell())

    def __str__(self):
        return """{type_name}: {{root_node: 0x{root_node:x}, names_offset: 0x{names_offset:x}, names_count: {names_count}}}""".format(type_name=type(self).__name__, **vars(self))

class Node:
    def __init__(self, file, parent_block):
        with parent_block.block("Node.type", file):
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


def read_node_tree(file, node_offset, parent_block):
    file.seek(node_offset + HEADER_OFFSET)
    node = Node(file, parent_block)
    # read header
    for node_type in node.node_types:
        if node_type.header_type:
            node_type_header = node_type.header_type(file, parent_block)
            node.headers[node_type.name] = node_type_header

    # read content of node type
    for name, node_type_header in node.headers.items():
         node_type_header.read_node(file)

    # read child nodes
    for child_offset in node.headers["HEADER"].child_offsets:
        node.childs.append(read_node_tree(file, child_offset, parent_block))
    return node


def update_node_name(names, node, depth):
    node.name = names[node.headers["HEADER"].node_id]


def readModelFile(filename, block):
    with open(filename, "rb") as file:
        header = Header(file, block)
        geometry_header = GeometryHeader(file, block)
        model_header = ModelHeader(file, block)
        names_header = NamesHeader(file, block)
        # read animations
        model_header.read_animations(file)
        print(header)
        print(geometry_header)
        print(model_header)
        print(names_header)

        names_header.read_names(file)
        root_node = read_node_tree(file, names_header.root_node, block)
        # update names
        visit_tree(root_node, Node.get_childs, partial(update_node_name, names_header.names))
        # print tree
#        visit_tree(root_node, Node.get_childs, lambda node, depth : print("  "*depth, node.headers["HEADER"].node_id, node.name, hex(node.node_type_id), *[node_type.name for node_type in node.node_types], *[header for name, header in node.headers.items()]))
        visit_tree(root_node, Node.get_childs, lambda node, depth : print("  "*depth, node.headers["HEADER"].node_id, node.name, hex(node.node_type_id), *[node_type.name for node_type in node.node_types], node.headers["HEADER"].position, node.headers["HEADER"].rotation, *node.headers["HEADER"].controllers))

        # export SKIN nodes
#        export_mesh([node for node in iterate_tree(root_node, Node.get_childs) if "MESH" in node.headers and "SKIN" not in node.headers], filename)
        export_mesh([node for node in iterate_tree(root_node, Node.get_childs) if "SKIN" in node.headers], filename)


def export_mesh(nodes, filename):
    basename = os.path.splitext(os.path.split(filename)[1])[0]
    with open(basename+".obj", 'w') as f:
        f.write("# OBJ file\n")
        vertex_offset = 1
        for node in nodes:
            mesh = node.headers["MESH"]

            f.write("o {name}\n".format(name=node.name))
            for v in mesh.vertices:
                f.write("v %.4f %.4f %.4f\n" % (v.x, v.y, v.z))
            for face in mesh.faces:
                f.write("f")
                for i in face.vertex_indices:
                    f.write(" %d" % (i + vertex_offset))
                f.write("\n")
            vertex_offset = vertex_offset + len(mesh.vertices)
    print("mesh written to "+basename+".obj")

def print_block(block, filename):
    block.sort()
    basename = os.path.splitext(os.path.split(filename)[1])[0]
    with open(basename+".blk", 'w') as f:
        visit_tree(block, Block.get_childs, lambda block, depth : f.write("{}{} {} {}\n".format("  "*depth, block.start, block.end, block.name)))
    print("block file written to "+basename+".blk")


def parse_command_line():
    parser = argparse.ArgumentParser(description='Process MDL files.')
    parser.add_argument('input', help='path to mdl/mdx file')

    parsed = parser.parse_args()

    block = Block("root", 0)
    model = readModelFile(parsed.input, block)
    block.close_block(os.stat(parsed.input).st_size)
    print_block(block, parsed.input)

def main():
    parse_command_line()

main()
