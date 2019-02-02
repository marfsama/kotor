#!/usr/bin/env python3

import argparse
import os
import json
import io

from functools import partial
from collections import OrderedDict

from kotor.tools import *
from .nodes import *

# TODO: evaluate part numbers for models with super models. @see: http://web.archive.org/web/20050213205343/torlack.com/index.html?topics=nwndata_binmdl

# based on xoreos/src/graphics/aurora/model_kotor.cpp from https://github.com/xoreos/xoreos


class Model:
    pass


def update_node_name(names, node, depth):
    node.name = names[node.headers["HEADER"].node_id]


def read_model_file(filename, block):
    def put_node_in_dict(node_by_name,  node_by_id,  node,  depth):
        node_by_name[node.name] = node
        node_by_id[node.headers["HEADER"].node_id] = node
        
    with open(filename, "rb") as file:
        model = Model()
        model.header = Header(file, block)
        
        # read entire model data into memory
        model_data = file.read(model.header.mdl_size)
        # read remaining model data from byte stream
        data_file = io.BytesIO(model_data)

        model.geometry_header = GeometryHeader(data_file, block)
        model.model_header = ModelHeader(data_file, block)
        model.names_header = NamesHeader(data_file, block)
        # read animations
        model.model_header.read_animations(data_file)

        model.names_header.read_names(data_file)
        model.root_node = read_node_tree(data_file, model.names_header.root_node, block)
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
    if parsed.func:
        parsed.func(parsed)

#    print_block(block, parsed.input)

def main():
    parse_command_line()

if __name__ == "__main__":
    main()

