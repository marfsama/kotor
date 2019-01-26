#!/usr/bin/env python3

import argparse
import os
import json

from functools import partial
from collections import OrderedDict

from kotor.tools import *

# TODO: evaluate part numbers for models with super models. @see: http://web.archive.org/web/20050213205343/torlack.com/index.html?topics=nwndata_binmdl

# based on xoreos/src/graphics/aurora/model_kotor.cpp from https://github.com/xoreos/xoreos

# size of file header. each offset in mdl must be adjusted by the header offset.
HEADER_OFFSET = 12


class Model:
    pass

class NodeHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("NodeHeader", file):
            self.parent_node = readu16(file)
            self.node_id = readu16(file)
            file.read(4+2) # unknown
            self.parent_node_start = readu32(file)
            self.position = Vertex(file)
            self.rotation = Quaternion(file)
            self.child_offsets = Array(file)
            self.controllers = Array(file)
            self.controller_data = Array(file)

    def read_node(self, file):
        file.seek(self.child_offsets.offset + HEADER_OFFSET)
        with self.parent_block.block("NodeHeader.child_offsets", file):
            self.child_offsets.data = readlist(readu32, file, self.child_offsets.allocated_entries) 

        if self.controllers.allocated_entries > 0:
            file.seek(self.controllers.offset + HEADER_OFFSET)
            with self.parent_block.block("Controller.array", file):
                self.controllers.data = readlist(Controller, file, self.controllers.allocated_entries)

            file.seek(self.controller_data.offset + HEADER_OFFSET)
            with self.parent_block.block("Controller.data", file):
                self.controller_data.data = readlist(readfloat, file, self.controller_data.allocated_entries)

        # each controller can read its values from the data array
        for controller in self.controllers.data:
            controller.read_data_rows(self.controller_data.data)

    def __serialize__(self):
        base_attributes = object_attributes_to_ordered_dict(self,  ['parent_node', 'node_id' , 'parent_node_start',  'position', 'rotation', 'child_offsets', 'controllers', 'controller_data'])
        base_attributes["controllers"] = self.controllers.data
        return base_attributes

    def __str__(self):
        return """{type_name}: {{parent_node: 0x{parent_node:x}, node_id: {node_id}, parent_node_start: {parent_node_start}, position: {position}, rotation: {rotation}, child_offsets: {child_offsets}, controllers: {controllers}, controller_data: {controller_data}}}""".format(type_name=type(self).__name__, **vars(self))


class ControllerRow:
    def __init__(self, timekey,  values):
        self.timekey = timekey
        self.values = values
        
    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['timekey', 'values'])


class Controller:
    def __init__(self, file):
        self.controller_type_id = readu32(file)
        self.controller_type = CONTROLLER_TYPES.get(self.controller_type_id,  ControllerType('unknown',  self.controller_type_id))
        self.unknown1 = file.read(2)
        self.row_count = readu16(file)
        self.timekey_offset = readu16(file)
        self.datakey_offset = readu16(file)
        self.column_count = readu8(file)
        self.unknown2 = file.read(3)
        # read later
        self.rows = []
        
    def read_data_rows(self,  data):
        for row_index in range(self.row_count):
            start_slice = self.datakey_offset + self.column_count * row_index
            row = ControllerRow(data[self.timekey_offset+row_index],  data[start_slice:start_slice+self.column_count])
            self.rows.append(row)
        
    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['controller_type_id', 'controller_type','unknown1', 'row_count' , 'timekey_offset',  'datakey_offset', 'column_count','unknown2',  'rows'])

    def __str__(self):
        return """{type_name}: {{controller_type: {controller_type}, row_count: {row_count}, column_count: {column_count}, timekey_offset: {timekey_offset}, datakey_offset: {datakey_offset}}}""".format(type_name=type(self).__name__, **vars(self))


class LightHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("LightHeader", file):
#http://web.archive.org/web/20050213205343/torlack.com/index.html?topics=nwndata_binmdl
            self.flare_radius = readfloat(file)
            self.unknown_array = Array(file)
            self.flare_sizes = Array(file)
            self.flare_positions = Array(file)
            self.flare_color_shifts = readlist(readu32,  file,  3)
            self.flare_texture_names_offsets = Array(file)
            self.light_priority = readu32(file)
            self.ambient_only = readu32(file)
            self.dynamic_type = readu32(file)
            self.affect_dynamic_flag = readu32(file)
            self.shadow_flag = readu32(file)
            self.generate_flare_flag = readu32(file)
            self.fading_flag = readu32(file)

    def read_node(self, file):
        pass

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['flare_radius', 'unknown_array', 'flare_sizes', 'flare_positions', 'flare_color_shifts',  'flare_texture_names_offsets', 'light_priority', 'ambient_only',  'dynamic_type', 'affect_dynamic_flag', 'shadow_flag','generate_flare_flag',   'fading_flag'])

class MeshHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("MeshHeader", file):
            self.unknown1 = file.read(4+4)
            self.faces = Array(file);
            self.bounding_box = (readlist(readfloat, file, 3), readlist(readfloat, file, 3))
            self.radius = readfloat(file)  # radius of bounding sphere
            self.averange = Vertex(file) # midpoint of bounding sphere
            self.diffuse = readlist(readfloat, file, 3)
            self.ambient = readlist(readfloat, file, 3)
            self.transparency_hint = readu32(file)
            self.texture_name = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.texture_name2 = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.unknown2 = file.read(24) # unknown
            # read array where the vertex counts are saved. array always has size 1.
            self.vertex_count_array = Array(file);
            # read array where the vertex offsets are saved. array always has size 1.
            self.vertex_offset_array = Array(file);
            if self.vertex_count_array.used_entries != 1 or self.vertex_offset_array.used_entries != 1:
                raise ValueError("Illegal vertex array count. Only 1 is supported at the moment.")
            self.unknown_array = Array(file)
            self.unknown3 = file.read(24 + 16) # other unknown stuff
            self.mdx_structure_size = readu32(file)
            self.unknown4 = file.read(8) # unknown
            self.vertex_normals_offset = readu32(file);
            self.unknown5 = file.read(4) # unknown
            self.uv_offset1 = read32(file)
            self.uv_offset2 = read32(file)
            self.unknown6 = file.read(24) # unknown
            self.vertex_count  = readu16(file)
            self.texture_count = readu16(file)
            self.unknown7 = file.read(2) # unknown
            self.shadow = readu16(file) != 0
            self.render = readu16(file) != 0
            self.unknown8 = file.read(10) # unknown
#	    if (ctx.kotor2)
            self.unknown9 = file.read(8) # unknown

            self.mdx_offset = readu32(file)
            self.vertex_coordinates_offset = readu32(file)

        # read later
        self.vertices = []
        self.vertex_indices = []
        
    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['unknown1','faces', 'bounding_box', 'radius' , 'averange',  'diffuse', 'ambient','transparency_hint',  
        'texture_name',  'texture_name2', 'unknown2','vertex_count_array', 'vertex_offset_array','unknown_array', 'unknown3',  'mdx_structure_size', 'unknown4', 
        'vertex_normals_offset', 'unknown5', 'uv_offset1', 'uv_offset2', 'unknown6', 'vertex_count', 'texture_count', 'unknown7', 'shadow', 'render', 'unknown8', 'unknown9', 
        'mdx_offset', 'vertex_coordinates_offset'])
        

    def read_node(self, file):
        # read vertex count array and vertex offset array
        file.seek(self.vertex_count_array.offset+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.vertex_count_array", file):
            self.vertex_count_array.data = readlist(readu32, file, self.vertex_count_array.allocated_entries)

        file.seek(self.vertex_offset_array.offset+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.vertex_offset_array", file):
            self.vertex_offset_array.data = readlist(readu32, file, self.vertex_offset_array.allocated_entries)
            # note: directly after this array there is an unknown 32bit value.

        # read faces
        file.seek(self.faces.offset+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.face_array", file):
            self.faces.data = readlist(Face, file, self.faces.allocated_entries)
        
        # read vertex coordinates
        file.seek(self.vertex_coordinates_offset+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.vertex_array", file):
            self.vertices = readlist(Vertex, file, self.vertex_count)

        # read vertex indices
        file.seek(self.vertex_offset_array.data[0]+HEADER_OFFSET)
        with self.parent_block.block("MeshHeader.vertex_indices_array", file):
            self.vertex_indices = readlist(readu16, file, self.vertex_count_array.data[0])

    def __str__(self):
        return """{type_name}: {{faces: {faces}, bounding_box: {bounding_box}, radius: {radius}, averange: {averange}, diffuse: {diffuse}, ambient: {ambient}, transparency_hint: {transparency_hint}, texture_name: {texture_name}, texture_name2: {texture_name2}, mdx_structure_size: {mdx_structure_size}, vertex_normals_offset: 0x{vertex_normals_offset:x}, uv_offset1: 0x{uv_offset1:x}, uv_offset2: 0x{uv_offset2:x}, vertex_count: {vertex_count}, texture_count: {texture_count}, shadow: {shadow}, render: {render}, mdx_offset: 0x{mdx_offset:x}, vertex_coordinates_offset: 0x{vertex_coordinates_offset:x}, vertex_count_array: {vertex_count_array}, vertex_offset_array: {vertex_offset_array}, faces: {faces}, vertices: [{verticesstr}], vertex_indices: [{vertex_indices}] }}""".format(type_name=type(self).__name__, **vars(self), verticesstr=", ".join([str(vertex) for vertex in self.vertices]))


class SkinMeshHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("SkinMeshHeader", file):
            self.unknown1 = readlist(readu32,  file,  5)
            self.bone_map_offset = readu32(file)
            self.bone_map_count = readu32(file)
            self.bone_quaternions = Array(file)
            self.bone_vertices = Array(file)
            self.bone_constants = Array(file)
            self.bone_nodes = readlist(readu16, file, 17) # list of nodes which can affect vertices from this node
            self.unknown2 = file.read(2)
        # read later
        self.bone_map = []

    def read_node(self, file):
        # read bone map
        file.seek(self.bone_map_offset+HEADER_OFFSET)
        with self.parent_block.block("SkinMeshHeader.bone_map", file):
            self.bone_map = readlist(readu32, file, self.bone_map_count)

        # 4 floats each node. rotation quaternion?
        file.seek(self.bone_quaternions.offset+HEADER_OFFSET)
        with self.parent_block.block("SkinMeshHeader.bone_quaternions", file):
            self.bone_quaternions .data = readlist(readfloat, file, self.bone_quaternions.allocated_entries*4)
    
        # 3 floats each node. translation?
        file.seek(self.bone_vertices.offset+HEADER_OFFSET)
        with self.parent_block.block("SkinMeshHeader.bone_vertices", file):
            self.bone_vertices.data = readlist(readfloat, file, self.bone_vertices.allocated_entries*3)

        # 1 floats each node. scale/length of bone?
        file.seek(self.bone_constants.offset+HEADER_OFFSET)
        with self.parent_block.block("SkinMeshHeader.bone_constants", file):
            self.bone_constants.data = readlist(readfloat, file, self.bone_constants.allocated_entries)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['unknown1','bone_map_offset', 'bone_map_count', 'bone_quaternions' , 'bone_vertices',  'bone_constants', 'bone_nodes','unknown2'])

    def __str__(self):
        return """{type_name}: {{bone_map_offset: 0x{bone_map_offset:x}, bone_map_count: {bone_map_count}, bone_nodes: {bone_nodes}}}""".format(type_name=type(self).__name__, **vars(self))

class DanglyMeshHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("DanglyMeshHeader", file):
            self.constraints = Array(file)
            self.displacement = readfloat(file)
            self.tightness = readfloat(file)
            self.period = readfloat(file)
            self.unknown_array_offset = readu32(file)
        # read later
        self.unknown_array = []

    def read_node(self, file):
        file.seek(self.constraints.offset+HEADER_OFFSET)
        with self.parent_block.block("DanglyMeshHeader.constraints", file):
            self.constraints.data = readlist(readfloat, file, self.constraints.allocated_entries)

        # read unknown array. same size as constraints, 3 floats for each entry
        file.seek(self.unknown_array_offset+HEADER_OFFSET)
        with self.parent_block.block("DanglyMeshHeader.unknown_array", file):
            self.unknown_array = readlist(readfloat, file, self.constraints.allocated_entries*3)

    def __serialize__(self):
        base_attributes = object_attributes_to_ordered_dict(self,  ['constraints','displacement', 'tightness', 'period' , 'unknown_array_offset',  'unknown_array'])
        base_attributes["constraints_data"] = self.constraints.data
        return base_attributes

    def __str__(self):
        return """{type_name}: {{displacement: {displacement}, tightness: {tightness}, period: {period}, constraints: {constraints}}}""".format(type_name=type(self).__name__, **vars(self))

class AabbHeader:
    """axis oriented bounding box."""
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("AabbHeader", file):
            self.entry_point_offset = readu32(file)
        # read later
        self.aabb_tree = None

    def read_node(self, file):
        file.seek(self.entry_point_offset+HEADER_OFFSET)
        self.aabb_tree = AabbEntry(file,  self.parent_block)
        self.aabb_tree.read_childs(file,  self.parent_block)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['entry_point_offset',  'aabb_tree'])


class AabbEntry:
    def __init__(self,  file,  parent_block):
        with parent_block.block("AABB_Node", file):
            self.bounding_box = readlist(Vertex,  file,  2)
            self.left_node_offset = readu32(file)
            self.right_node_offset = readu32(file)
            self.leaf_node_nr = read32(file)
            self.plane= readu32(file)
        # read later
        self.left_node = None
        self.right_node = None

    def read_childs(self, file,  parent_block):
        if self.left_node_offset > 0:
            file.seek(self.left_node_offset+HEADER_OFFSET)
            self.left_node = AabbEntry(file,  parent_block)
            self.left_node.read_childs(file,  parent_block)
            
        if self.right_node_offset > 0:
            file.seek(self.right_node_offset+HEADER_OFFSET)
            self.right_node = AabbEntry(file,  parent_block)
            self.right_node.read_childs(file,  parent_block)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['bounding_box',  'left_node_offset',  'right_node_offset',  'leaf_node_nr',  'left_node',  'right_node'])


class NodeType:
    def __init__(self, name, bitfield, header_type = None):
        self.name = name
        self.bitfield = bitfield
        self.header_type = header_type

    def matches(self, value):
        return value & self.bitfield
    
    def __serialize__(self):
        return self.name
        
    def __str__(self):
        return """{type_name}: {{name: {name}, bitfield: {bitfield}}}""".format(type_name=type(self).__name__, **vars(self))

NODE_TYPES = [
  NodeType("HEADER",    0x00000001, NodeHeader),
  NodeType("LIGHT",     0x00000002,  LightHeader),
  NodeType("EMITTER",   0x00000004 ),
  NodeType("CAMERA",    0x00000008 ),
  NodeType("REFERENCE", 0x00000010 ),
  NodeType("MESH",      0x00000020, MeshHeader),
  NodeType("SKIN",      0x00000040, SkinMeshHeader),
  NodeType("ANIM",      0x00000080 ),
  NodeType("DANGLY",    0x00000100, DanglyMeshHeader),
  NodeType("AABB",      0x00000200,  AabbHeader),
  NodeType("SABER",     0x00000800 )
]

class ControllerType:
    def __init__(self, name, id, controller_class = None):
        self.name = name
        self.id = id
        self.controller_class = controller_class

    def __serialize__(self):
        return self.name


CONTROLLER_TYPES = {
    8: ControllerType("position", 8), 
    20: ControllerType("orientation", 20), 
    36: ControllerType("scale", 36), 
    76: ControllerType("color", 76), 
    88: ControllerType("birth rate", 88), 
    100: ControllerType("vertical displacement", 100), 
    132: ControllerType("frame end", 132), 
    140: ControllerType("gravitation", 140), 
}


class Header:
    def __init__(self, file, parent_block):
        with parent_block.block("Header", file):
            file.read(4) # skip first dword (always 0x0)
            self.mdl_size = readu32(file)
            self.mdx_size = readu32(file)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['mdl_size', 'mdx_size'])

    def __str__(self):
        return """{name}: {{mdl_size: {mdl_size}, mdx_size: {mdx_size}}}""".format(name=type(self).__name__, **vars(self))


class GeometryHeader:
    def __init__(self, file, parent_block):
        with parent_block.block("GeometryHeader", file):
            self.function_pointers = file.read(8)
            self.name = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.node_offset = readu32(file)
            self.node_count = readu32(file)
            self.unknown2 = file.read(28) # unknown
            self.type = readu8(file)
            self.unknown3 = file.read(3) # unknown

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['function_pointers','name', 'node_offset','node_count', 'unknown2', 'type',  'unknown3'])

    def __str__(self):
        return """{type_name}: {{name: {name}, node_offset: 0x{node_offset:x}, node_count: {node_count}, type: {type}}}""".format(type_name=type(self).__name__, **vars(self))

class ModelHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("ModelHeader", file):
            self.geometry_flags = readu16(file)
            self.classification = readu8(file)
            self.fogged = readu8(file)
            self.unknown1 = file.read(4)
            self.animation_offset_array = Array(file)
            self.unknown2 = file.read(4) # unknown
            self.bounding_box = readlist(Vertex, file, 2)
            self.radius = readfloat(file)
            self.scale = readfloat(file)
            self.super_model = file.read(32).partition(b'\0')[0].decode("utf-8")
        # read later
        self.animations = []

    def read_animations(self, file):
        file.seek(self.animation_offset_array.offset+HEADER_OFFSET)
        with self.parent_block.block("Animations.offset_array", file):
            self.animation_offset_array.data = readlist(readu32, file, self.animation_offset_array.allocated_entries)

        for offset in self.animation_offset_array.data:
            file.seek(offset+HEADER_OFFSET)
            animation_header = AnimationHeader(file, self.parent_block)
            animation_header.read_events(file)
            animation_header.read_animation_node(file)
            self.animations.append(animation_header)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['geometry_flags', 'classification','fogged', 'unknown1','animation_offset_array','unknown2','bounding_box', 'radius', 'scale', 'super_model'])

    def __str__(self):
        return """{type_name}: {{classification: {classification}, fogged: {fogged}, animation_offset_array: {animation_offset_array}, bounding_box: {bounding_box}, radius: {radius}, scale: {scale}, super_model: {super_model}, animations: \n[{animations_str}]}}""".format(type_name=type(self).__name__, **vars(self), animations_str="\n".join([str(animation) for animation in self.animations]))

class AnimationHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        self.geometry_header = GeometryHeader(file, parent_block)
        with parent_block.block("AnimationHeader", file):
            self.length = readfloat(file)
            self.transition_time = readfloat(file)
            self.name = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.events = Array(file)
            file.read(4) # unknown

        # read later
        self.animation_node = None

    def read_events(self, file):
        if self.events.allocated_entries > 0:
            file.seek(self.events.offset + HEADER_OFFSET)
            with self.parent_block.block("Animations.events", file):
                self.events.data = readlist(Event, file, self.events.allocated_entries)


    def read_animation_node(self, file):
        self.animation_node = read_node_tree(file, self.geometry_header.node_offset,  self.parent_block)
        
    def __str__(self):
        return """{type_name}: {{geometry_header: {geometry_header}, length: {length}, transition_time: {transition_time}, name: {name}, events: [{eventsstr}], node: {animation_node}}}""".format(type_name=type(self).__name__, **vars(self), eventsstr=", ".join([str(event) for event in self.events.data]))

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
            self.unknown1 = readu32(file)
            self.mdx_size = readu32(file)
            self.unknown2 = readu32(file)
            self.names_offset_array = Array(file)

    def read_names(self, file):
        # seek to start of names offset table
        file.seek(self.names_offset_array.offset + HEADER_OFFSET)
        with self.parent_block.block("Names.offset_array", file):
            names_offsets = readlist(readu32, file, self.names_offset_array.allocated_entries)

        self.names = []
        block = self.parent_block.start_block("Names", names_offsets[0] + HEADER_OFFSET)
        for name_offset in names_offsets:
            file.seek(name_offset + HEADER_OFFSET)
            self.names.append(next(read_terminated_token(file, null_terminated)).decode("utf-8"))
        block.close_block(file.tell())

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['root_node', 'unknown1' , 'mdx_size', 'unknown2',  'names_offset_array'])

    def __str__(self):
        return """{type_name}: {{root_node: 0x{root_node:x}, names_offset_array: {names_offset_array}}}""".format(type_name=type(self).__name__, **vars(self))

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

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['node_type_id', 'node_types' , 'name',  'headers'])

    def __str__(self):
        return """{type_name}: {{node_type_id: 0x{node_type_id:x} ({node_types_str})}}""".format(type_name=type(self).__name__, **vars(self),  node_types_str=",".join([type.name for type in self.node_types])) 


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
    if "HEADER" in node.headers:
        for child_offset in node.headers["HEADER"].child_offsets.data:
            node.childs.append(read_node_tree(file, child_offset, parent_block))
    return node


def update_node_name(names, node, depth):
    node.name = names[node.headers["HEADER"].node_id]


def read_model_file(filename, block):
    def put_node_in_dict(node_by_name,  node_by_id,  node,  depth):
        node_by_name[node.name] = node
        node_by_id[node.headers["HEADER"].node_id] = node
        
    with open(filename, "rb") as file:
        model = Model()
        model.header = Header(file, block)
        model.geometry_header = GeometryHeader(file, block)
        model.model_header = ModelHeader(file, block)
        model.names_header = NamesHeader(file, block)
        # read animations
        model.model_header.read_animations(file)

        model.names_header.read_names(file)
        model.root_node = read_node_tree(file, model.names_header.root_node, block)
        # update names
        visit_tree(model.root_node, Node.get_childs, partial(update_node_name, model.names_header.names))
        # create node dictionary by name and id
        model.node_by_name = OrderedDict()
        model.node_by_id = {}
        visit_tree(model.root_node, Node.get_childs, partial(put_node_in_dict, model.node_by_name, model.node_by_id))

#        visit_tree(root_node, Node.get_childs, lambda node, depth : print("  "*depth, node.headers["HEADER"].node_id, node.name, hex(node.node_type_id), *[node_type.name for node_type in node.node_types]))

        # export SKIN nodes
#        export_mesh_backup([node for node in iterate_tree(root_node, Node.get_childs) if "MESH" in node.headers and "SKIN" not in node.headers], filename)
#        export_mesh_backup([node for node in iterate_tree(root_node, Node.get_childs) if "SKIN" in node.headers], filename)
    return model


def export_mesh_backup(nodes, filename):
    basename = os.path.splitext(os.path.split(filename)[1])[0]
    with open(basename+".obj", 'w') as f:
        f.write("# OBJ file\n")
        vertex_offset = 1
        for node in nodes:
            mesh = node.headers["MESH"]

            f.write("o {name}\n".format(name=node.name))
            for v in mesh.vertices:
                f.write("v %.4f %.4f %.4f\n" % (v.x, v.y, v.z))
            for face in mesh.faces.data:
                f.write("f")
                for i in face.vertex_indices:
                    f.write(" %d" % (i + vertex_offset))
                f.write("\n")
            vertex_offset = vertex_offset + len(mesh.vertices)
    print("mesh written to "+basename+".obj")

def export_block(args):
    block = Block("root", 0)
    read_model_file(args.input, block)
    block.close_block(os.stat(args.input).st_size)
    block.sort()
    basename = os.path.splitext(os.path.split(args.input)[1])[0]
    with open(basename+".blk", 'w') as f:
        visit_tree(block, Block.get_childs, lambda block, depth : f.write("{}{} {} {}\n".format("  "*depth, block.start, block.end, block.name)))
    print("block file written to "+basename+".blk")

def export_header(args):
    block = Block("root", 0)
    model = read_model_file(args.input, block)
    block.close_block(os.stat(args.input).st_size)
    json_dict = OrderedDict()
    if args.f:
        json_dict["header"] = model.header

    if args.g:
        json_dict["geometry_header"] = model.geometry_header

    if args.m:
        json_dict["model_header"] = model.model_header
        
    if args.n:
        json_dict["names_header"] = model.names_header
        
    print(json.dumps(json_dict, indent=4, cls=Encoder))

def export_nodes(args):
    def node_details(node, depth):
        node_header = node.headers["HEADER"]
        node_json = OrderedDict()
        node_json["id"] = node_header.node_id
        node_json["name"] = node.name
        node_json["types"] = [type.name for type in node.node_types]
        node_json["parent"] = node_header.parent_node
        names_tree[node_json["id"]] = node_json

    block = Block("root", 0)
    model = read_model_file(args.input, block)
    block.close_block(os.stat(args.input).st_size)
    
    json_dict = OrderedDict()
    if args.ln:
        names = list(model.node_by_name.keys())
        json_dict["names"] = names

    if args.ld:
        names_tree = {}
        visit_tree(model.root_node, Node.get_childs, node_details)
        json_dict["names_tree"] = names_tree

    if args.x:
        if not args.n:
            print ("error: need to specify node name or number (-n) for export header (-x)")
            return
        node = model.node_by_name.get(args.n)
        if not node:
            node = model.node_by_id.get(args.n)
        if not node:
            print("cannot find node",  args.n,  "in model")
            return
        json_dict["nodes"] = [node]

    print(json.dumps(json_dict, indent=4, cls=Encoder))


def export_mesh(args):
    block = Block("root", 0)
    model = read_model_file(args.input, block)
    block.close_block(os.stat(args.input).st_size)

    if args.n:
        nodes = [model.node_by_name.get(node_name) for node_name in args.n.split(',')  ]
    else:
        nodes = list(model.node_by_name.values())

    print("# OBJ file")
    vertex_offset = 1
    for node in nodes:
        if node and "MESH" in node.headers:
            mesh = node.headers["MESH"]

            print("o {name}".format(name=node.name))
            for v in mesh.vertices:
                print("v %.4f %.4f %.4f" % (v.x, v.y, v.z))
            for face in mesh.faces.data:
                print("f",  end='')
                for i in face.vertex_indices:
                    print(" %d" % (i + vertex_offset),  end='')
                print()
            vertex_offset = vertex_offset + len(mesh.vertices)

def parse_command_line():
    parser = argparse.ArgumentParser(description='Process MDL files.')
    subparsers = parser.add_subparsers(help='sub-command help',  description='')
    
    parser_header = subparsers.add_parser('exportheader', help='export file header')
    parser_header.add_argument('input',  help ='Model file path')
    parser_header.add_argument('-f', action="store_true",  help ='file header')
    parser_header.add_argument('-g', action="store_true",  help='geometry header')
    parser_header.add_argument('-m', action="store_true",  help='model header')
    parser_header.add_argument('-n', action="store_true",  help='names header')
    parser_header.set_defaults(func=export_header)

    parser_nodes = subparsers.add_parser('exportnodes', help='export geometry nodes')
    parser_nodes.add_argument('input',  help ='Model file path')
    parser_nodes.add_argument('-ln', action="store_true",  help ='list node names')
    parser_nodes.add_argument('-ld', action="store_true",  help ='list node hierarchy details') 
    parser_nodes.add_argument('-n',  help ='node name or id') 
    parser_nodes.add_argument('-x', action="store_true",  help ='export node headers') 
    parser_nodes.set_defaults(func=export_nodes)

    parser_mesh = subparsers.add_parser('exportmesh', help='export mesh from geometry nodes') 
    parser_mesh.add_argument('input',  help ='Model file path')
    parser_mesh.add_argument('-n',  help ='node name(s) or id(s)') 
    parser_mesh.set_defaults(func=export_mesh)

    parser_blocks = subparsers.add_parser('exportblocks', help='export blocks')
    parser_blocks.add_argument('input',  help ='Model file path')
    parser_blocks.set_defaults(func=export_block)


    parsed = parser.parse_args()
    parsed.func(parsed)

#    print_block(block, parsed.input)

def main():
    parse_command_line()

if __name__ == "__main__":
    main()

