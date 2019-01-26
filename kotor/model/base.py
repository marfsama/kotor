from kotor.tools import *

class Array:
    def __init__(self, file):
        self.offset = readu32(file)
        self.used_entries = readu32(file)
        self.allocated_entries= readu32(file)
        # read later
        self.data = []

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['offset', 'used_entries','allocated_entries'])


class Face:
    def __init__(self, file):
        self.plane_normal = Vertex(file)
        self.plane_distance = readfloat(file)
        self.surface = readu32(file)
        self.adjected_faces = readlist(readu16, file, 3)
        self.vertex_indices = readlist(readu16, file, 3)

    def __str__(self):
        return """{type_name}: {{plane_normal: {plane_normal}, plane_distance: {plane_distance}, surface: {surface}, adjected_faces: {adjected_faces}, vertex_indices: {vertex_indices}}}""".format(type_name=type(self).__name__, **vars(self))


class Vertex:
    def __init__(self, file):
        self.x = readfloat(file)
        self.y = readfloat(file)
        self.z = readfloat(file)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['x', 'y','z'])


class Quaternion:
    def __init__(self, file):
        self.w = readfloat(file)  # real part
        self.x = readfloat(file)  # imaginary
        self.y = readfloat(file)  # imaginary
        self.z = readfloat(file)  # imaginary

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self,  ['w','x', 'y','z'])
