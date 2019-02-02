from collections import OrderedDict

from kotor.tools import *
from .base import Array, Vertex, Quaternion, Face


class Node:
    def __init__(self, file, parent_block):
        with parent_block.block("Node.type"):
            self.node_type_id = readu16(file)
            self.node_types = [node_type for node_type in NODE_TYPES if node_type.matches(self.node_type_id)]
        # set later
        self.headers = OrderedDict()  # keep insertion order
        self.name = ""
        self.childs = []

    def get_childs(self):
        return self.childs

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self, ['node_type_id', 'node_types', 'name', 'headers'])


class NodeHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("NodeHeader"):
            self.parent_node = readu16(file)
            self.node_id = readu16(file)
            self.unknown = file.read(4+2)
            self.parent_node_start = readu32(file)
            self.position = Vertex(file)
            self.rotation = Quaternion(file)
            self.child_offsets = Array(file)
            self.controllers = Array(file)
            self.controller_data = Array(file)

    def read_node(self, file):
        self.child_offsets.read_data(file, readu32, self.parent_block.block("NodeHeader.child_offsets"))

        if self.controllers.allocated_entries > 0:
            self.controllers.read_data(file, Controller, self.parent_block.block("Controller.array"))
            self.controller_data.read_data(file, readfloat, self.parent_block.block("Controller.data"))

            # each controller can read its values from the data array
            for controller in self.controllers.data:
                controller.read_data_rows(self.controller_data.data)

    def __serialize__(self):
        base_attributes = object_attributes_to_ordered_dict(self,  ['parent_node', 'node_id', 'unknown', 'parent_node_start',  'position', 'rotation', 'child_offsets', 'controllers', 'controller_data'])
        base_attributes["controllers"] = self.controllers.data
        return base_attributes


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
        return object_attributes_to_ordered_dict(self,  ['controller_type_id', 'controller_type', 'unknown1', 'row_count', 'timekey_offset',  'datakey_offset', 'column_count', 'unknown2',  'rows'])


class LightHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("LightHeader"):
            # http://web.archive.org/web/20050213205343/torlack.com/index.html?topics=nwndata_binmdl
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
        return object_attributes_to_ordered_dict(self,  ['flare_radius', 'unknown_array', 'flare_sizes', 'flare_positions', 'flare_color_shifts',  'flare_texture_names_offsets', 'light_priority', 'ambient_only',  'dynamic_type', 'affect_dynamic_flag', 'shadow_flag', 'generate_flare_flag', 'fading_flag'])


class MeshHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("MeshHeader"):
            self.unknown1 = file.read(4+4)
            self.faces = Array(file)
            self.bounding_box = (readlist(readfloat, file, 3), readlist(readfloat, file, 3))
            self.radius = readfloat(file)  # radius of bounding sphere
            self.averange = Vertex(file)  # midpoint of bounding sphere
            self.diffuse = readlist(readfloat, file, 3)
            self.ambient = readlist(readfloat, file, 3)
            self.transparency_hint = readu32(file)
            self.texture_name = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.texture_name2 = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.unknown2 = file.read(24)  # unknown
            # read array where the vertex counts are saved. array always has size 1.
            self.vertex_count_array = Array(file)
            # read array where the vertex offsets are saved. array always has size 1.
            self.vertex_offset_array = Array(file)
            if self.vertex_count_array.used_entries != 1 or self.vertex_offset_array.used_entries != 1:
                raise ValueError("Illegal vertex array count. Only 1 is supported at the moment.")
            self.unknown_array = Array(file)
            self.unknown3 = file.read(24 + 16)  # other unknown stuff
            self.mdx_structure_size = readu32(file)
            self.unknown4 = file.read(8)  # unknown
            self.vertex_normals_offset = readu32(file)
            self.unknown5 = file.read(4)  # unknown
            self.uv_offset1 = read32(file)
            self.uv_offset2 = read32(file)
            self.unknown6 = file.read(24)  # unknown
            self.vertex_count = readu16(file)
            self.texture_count = readu16(file)
            self.unknown7 = file.read(2)  # unknown
            self.shadow = readu16(file) != 0
            self.render = readu16(file) != 0
            self.unknown8 = file.read(10)  # unknown
            # if (ctx.kotor2)
            self.unknown9 = file.read(8)  # unknown

            self.mdx_offset = readu32(file)
            self.vertex_coordinates_offset = readu32(file)

        # read later
        self.vertices = []
        self.vertex_indices = []

    def read_node(self, file):
        # read vertex count array and vertex offset array
        self.vertex_count_array.read_data(file, readu32, self.parent_block.block("MeshHeader.vertex_count_array"))
        self.vertex_offset_array.read_data(file, readu32, self.parent_block.block("MeshHeader.vertex_offset_array"))
        # note: directly after this array there is an unknown 32bit value.

        # read faces
        self.faces.read_data(file, Face,  self.parent_block.block("MeshHeader.face_array"))

        # read vertex coordinates
        file.seek(self.vertex_coordinates_offset)
        with self.parent_block.block("MeshHeader.vertex_array"):
            self.vertices = readlist(Vertex, file, self.vertex_count)

        # read vertex indices
        file.seek(self.vertex_offset_array.data[0])
        with self.parent_block.block("MeshHeader.vertex_indices_array"):
            self.vertex_indices = readlist(readu16, file, self.vertex_count_array.data[0])

    def __serialize__(self):
        return object_attributes_to_ordered_dict(
            self,  [
                'unknown1', 'faces', 'bounding_box', 'radius', 'averange',  'diffuse', 'ambient', 'transparency_hint',
                'texture_name',  'texture_name2', 'unknown2', 'vertex_count_array', 'vertex_offset_array', 'unknown_array', 'unknown3',  'mdx_structure_size', 'unknown4',
                'vertex_normals_offset', 'unknown5', 'uv_offset1', 'uv_offset2', 'unknown6', 'vertex_count', 'texture_count', 'unknown7', 'shadow', 'render', 'unknown8', 'unknown9',
                'mdx_offset', 'vertex_coordinates_offset'])


class SkinMeshHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("SkinMeshHeader"):
            self.unknown1 = readlist(readu32,  file,  5)
            self.bone_map_offset = readu32(file)
            self.bone_map_count = readu32(file)
            self.bone_quaternions = Array(file)
            self.bone_vertices = Array(file)
            self.bone_constants = Array(file)
            self.bone_nodes = readlist(readu16, file, 17)  # list of nodes which can affect vertices from this node
            self.unknown2 = file.read(2)
        # read later
        self.bone_map = []

    def read_node(self, file):
        # read bone map
        file.seek(self.bone_map_offset)
        with self.parent_block.block("SkinMeshHeader.bone_map"):
            self.bone_map = readlist(readu32, file, self.bone_map_count)

        self.bone_quaternions.read_data(file, Quaternion, self.parent_block.block("SkinMeshHeader.bone_quaternions"))
        self.bone_vertices.read_data(file, Vertex, self.parent_block.block("SkinMeshHeader.bone_vertices"))
        self.bone_constants.read_data(file, readfloat, self.parent_block.block("SkinMeshHeader.bone_constants"))

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['unknown1', 'bone_map_offset', 'bone_map_count', 'bone_quaternions', 'bone_vertices',  'bone_constants', 'bone_nodes', 'unknown2'])


class DanglyMeshHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("DanglyMeshHeader"):
            self.constraints = Array(file)
            self.displacement = readfloat(file)
            self.tightness = readfloat(file)
            self.period = readfloat(file)
            self.unknown_array_offset = readu32(file)
        # read later
        self.unknown_array = []

    def read_node(self, file):
        self.constraints.read_data(file, readfloat, self.parent_block.block("DanglyMeshHeader.constraints"))

        # read unknown array. same size as constraints, 3 floats for each entry
        file.seek(self.unknown_array_offset)
        with self.parent_block.block("DanglyMeshHeader.unknown_array"):
            self.unknown_array = readlist(readfloat, file, self.constraints.allocated_entries*3)

    def __serialize__(self):
        base_attributes = object_attributes_to_ordered_dict(self,  ['constraints', 'displacement', 'tightness', 'period', 'unknown_array_offset',  'unknown_array'])
        base_attributes["constraints_data"] = self.constraints.data
        return base_attributes


class AabbHeader:

    """axis oriented bounding box."""

    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("AabbHeader"):
            self.entry_point_offset = readu32(file)
        # read later
        self.aabb_tree = None

    def read_node(self, file):
        file.seek(self.entry_point_offset)
        self.aabb_tree = AabbEntry(file,  self.parent_block)
        self.aabb_tree.read_childs(file,  self.parent_block)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['entry_point_offset',  'aabb_tree'])


class AabbEntry:
    def __init__(self,  file,  parent_block):
        with parent_block.block("AABB_Node"):
            self.bounding_box = readlist(Vertex,  file,  2)
            self.left_node_offset = readu32(file)
            self.right_node_offset = readu32(file)
            self.leaf_node_nr = read32(file)
            self.plane = readu32(file)
        # read later
        self.left_node = None
        self.right_node = None

    def read_childs(self, file,  parent_block):
        if self.left_node_offset > 0:
            file.seek(self.left_node_offset)
            self.left_node = AabbEntry(file,  parent_block)
            self.left_node.read_childs(file,  parent_block)

        if self.right_node_offset > 0:
            file.seek(self.right_node_offset)
            self.right_node = AabbEntry(file,  parent_block)
            self.right_node.read_childs(file,  parent_block)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['bounding_box',  'left_node_offset',  'right_node_offset',  'leaf_node_nr',  'left_node',  'right_node'])


class NodeType:
    def __init__(self, name, bitfield, header_type=None):
        self.name = name
        self.bitfield = bitfield
        self.header_type = header_type

    def matches(self, value):
        return value & self.bitfield

    def __serialize__(self):
        return self.name


class ControllerType:
    def __init__(self, name, id, controller_class=None):
        self.name = name
        self.id = id
        self.controller_class = controller_class

    def __serialize__(self):
        return self.name


class Header:
    def __init__(self, file, parent_block):
        with parent_block.block("Header"):
            file.read(4)  # skip first dword (always 0x0)
            self.mdl_size = readu32(file)
            self.mdx_size = readu32(file)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['mdl_size', 'mdx_size'])


class GeometryHeader:
    def __init__(self, file, parent_block):
        with parent_block.block("GeometryHeader"):
            self.function_pointers = file.read(8)
            self.name = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.node_offset = readu32(file)
            self.node_count = readu32(file)
            self.unknown2 = file.read(28)  # unknown
            self.type = readu8(file)
            self.unknown3 = file.read(3)  # unknown

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['function_pointers', 'name', 'node_offset', 'node_count', 'unknown2', 'type', 'unknown3'])


class ModelHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        with parent_block.block("ModelHeader"):
            self.geometry_flags = readu16(file)
            self.classification = readu8(file)
            self.fogged = readu8(file)
            self.unknown1 = file.read(4)
            self.animation_offset_array = Array(file)
            self.unknown2 = file.read(4)  # unknown
            self.bounding_box = readlist(Vertex, file, 2)
            self.radius = readfloat(file)
            self.scale = readfloat(file)
            self.super_model = file.read(32).partition(b'\0')[0].decode("utf-8")
        # read later
        self.animations = []

    def read_animations(self, file):
        self.animation_offset_array.read_data(file, readu32, self.parent_block.block("Animations.offset_array"))

        for offset in self.animation_offset_array.data:
            file.seek(offset)
            animation_header = AnimationHeader(file, self.parent_block)
            animation_header.read_events(file)
            animation_header.read_animation_node(file)
            self.animations.append(animation_header)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['geometry_flags', 'classification', 'fogged', 'unknown1', 'animation_offset_array', 'unknown2', 'bounding_box', 'radius', 'scale', 'super_model'])


class AnimationHeader:
    def __init__(self, file, parent_block):
        self.parent_block = parent_block
        self.geometry_header = GeometryHeader(file, parent_block)
        with parent_block.block("AnimationHeader"):
            self.length = readfloat(file)
            self.transition_time = readfloat(file)
            self.name = file.read(32).partition(b'\0')[0].decode("utf-8")
            self.events = Array(file)
            file.read(4)  # unknown

        # read later
        self.animation_node = None

    def read_events(self, file):
        self.events.read_data(file, Event, self.parent_block.block("Animations.events"))

    def read_animation_node(self, file):
        self.animation_node = read_node_tree(file, self.geometry_header.node_offset,  self.parent_block)


class Event:
    def __init__(self, file):
        self.time = readfloat(file)
        self.name = file.read(32).partition(b'\0')[0].decode("utf-8")


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
        self.names_offset_array.read_data(file, readu32, self.parent_block.block("Names.offset_array"))

        self.names = []
        with self.parent_block.start_block("Names", self.names_offset_array.data[0]):
            for name_offset in self.names_offset_array.data:
                file.seek(name_offset)
                self.names.append(next(read_terminated_token(file, null_terminated)).decode("utf-8"))

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['root_node', 'unknown1', 'mdx_size', 'unknown2', 'names_offset_array'])


def read_node_tree(file, node_offset, parent_block):
    file.seek(node_offset)
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


NODE_TYPES = [
    NodeType("HEADER", 0x00000001, NodeHeader),
    NodeType("LIGHT", 0x00000002, LightHeader),
    NodeType("EMITTER", 0x00000004),
    NodeType("CAMERA", 0x00000008),
    NodeType("REFERENCE", 0x00000010),
    NodeType("MESH", 0x00000020, MeshHeader),
    NodeType("SKIN", 0x00000040, SkinMeshHeader),
    NodeType("ANIM", 0x00000080),
    NodeType("DANGLY", 0x00000100, DanglyMeshHeader),
    NodeType("AABB", 0x00000200, AabbHeader),
    NodeType("SABER", 0x00000800)
]

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
