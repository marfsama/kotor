#!/usr/bin/env python3

import argparse
import os
import sys


from itertools import cycle
from PIL import Image, ImageDraw


COLORS = [
    ("NAVY"   , "#001f3f"),
    ("BLUE"   , "#0074D9"),
    ("AQUA"   , "#7FDBFF"),
    ("TEAL"   , "#39CCCC"),
    ("OLIVE"  , "#3D9970"),
    ("GREEN"  , "#2ECC40"),
    ("LIME"   , "#01FF70"),
    ("YELLOW" , "#FFDC00"),
    ("ORANGE" , "#FF851B"),
    ("RED"    , "#FF4136"),
    ("MAROON" , "#85144B"),
    ("FUCHSIA", "#F012BE"),
    ("PURPLE" , "#B10DC9"),
    ("GRAY"   , "#AAAAAA"),
    ("SILVER" , "#DDDDDD"),
    ("WHITE"  , "#FFFFFF")
]


class Block:
    def __init__(self, start, end, name):
        self.start = start
        self.end = end
        self.name = name

    def __str__(self):
        return "{} - {} - {}".format(self.start, self.end, self.name)


def read_block_file(filename):
    with open(filename) as f:
        content = f.readlines()
        line_parts = [line.strip().split() for line in content]
        blocks = [Block(int(line_part[0]), int(line_part[1]), line_part[2]) for line_part in line_parts]
        return blocks

def assign_colors(blocks, colors):
    """
        randomly assigns colors to block names, who don't already have a color assigned
    """
    current_color = cycle(COLORS)
    for block in blocks:
        name = block.name
        if name not in colors:
            color = next(current_color)[1]
            colors[name] = color
    return colors

def generate_image(blocks, colors, scale, width=500):
    # find size of file
    size = max([block.end for block in blocks])
    height = int(size / width) + 1

    img = Image.new('RGB', (width*scale, height*scale), color=0)
    draw = ImageDraw.Draw(img)
    for block in blocks:
        color = colors[block.name]
        for i in range(block.end-block.start):
            current_index = i + block.start
            x = current_index % width
            y = current_index // width
            draw.rectangle([x*scale,y*scale,(x+1)*scale-1,(y+1)*scale-1], fill=color)

    return img

def read_colors_file(color_file):
    colors = {}
    if color_file:
        with open(color_file) as f:
            content = f.readlines()
            line_parts = [line.strip().split() for line in content]
            colors = {line_part[1]: line_part[0] for line_part in line_parts}

    return colors

def rangetype(string):
    if string:
        min_str, max_str = string.split('-')
        min_value = 0 if not min_str else int(min_str)
        max_value = sys.maxsize if not max_str else int(max_str)
        return (min_value, max_value)
    return None

def filter_blocks(blocks, valid_range):
    # filter blocks which are not in range
    valid_blocks = [block for block in blocks if block.end > valid_range[0] and block.start < valid_range[1]]
    if not valid_blocks:
        return valid_blocks

    # modify blocks to not start before start and end after end
    for block in valid_blocks:
        if block.start < valid_range[0]:
            block.start = valid_range[0]
    
        if block.end > valid_range[1]:
            block.end = valid_range[1]

    # move all blocks to the start, so the first block starts with 0
    for block in valid_blocks:
        block.start = block.start - valid_range[0]
        block.end = block.end - valid_range[0]

    return valid_blocks

def parse_command_line():
    parser = argparse.ArgumentParser(description='Process block (.blk) files.')
    parser.add_argument('input', help='path to blk file')
    parser.add_argument('output', nargs='?', help='output png filename (optional, defaults to basename of input file with "png" extension)')
    parser.add_argument('-c', metavar='color_file', dest='color', help='specify color file')
    parser.add_argument('-s', metavar='scale', dest='scale', type=int, default=1, help='scale factor of the image')
    parser.add_argument('-w', metavar='width', dest='width', type=int, default=500, help='width of the image (in respect to scale factor 1)')
    parser.add_argument('-r', metavar='range', dest='range', type=rangetype, help='(from-to) only process bytes from index from to to')

    parsed = parser.parse_args()

    blocks = read_block_file(parsed.input)
    blocks = filter_blocks(blocks, parsed.range)
    colors = read_colors_file(parsed.color)
    colors = assign_colors(blocks, colors)

    image = generate_image(blocks, colors, scale=parsed.scale, width=parsed.width)

    if parsed.output:
        output_filename = parsed.output
    else:
        output_filename = os.path.splitext(os.path.split(parsed.input)[1])[0]+'.png'
    image.save(output_filename)

def main():
    parse_command_line()

main()

