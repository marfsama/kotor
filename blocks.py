#!/usr/bin/env python3

import argparse
import os


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

def parse_command_line():
    parser = argparse.ArgumentParser(description='Process block (.blk) files.')
    parser.add_argument('input', help='path to blk file')
    parser.add_argument('-c', metavar='color_file', help='specify color file')
    parser.add_argument('-s', metavar='scale', type=int, default=1, help='scale factor of the image')
    parser.add_argument('-w', metavar='width', type=int, default=500, help='width of the image (in respect to scale factor 1)')

    parsed = parser.parse_args()

    blocks = read_block_file(parsed.input)
    colors = read_colors_file(parsed.color)
    colors = assign_colors(blocks, colors)
    image = generate_image(blocks, colors, scale=parsed.scale, width=parsed.width)

    basename = os.path.splitext(os.path.split(parsed.input)[1])[0]
    image.save(basename+'.png')

def main():
    parse_command_line()

main()

