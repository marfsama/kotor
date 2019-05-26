#!/usr/bin/env python3

import argparse

from kotor.tools import *
from PIL import Image, ImageDraw


ENCODING_DXT_1 = 2
ENCODING_DXT_5 = 4

class DX1Texel:
    def rgb565ToRgba32(self, color):
        return ((color & 0x1F) << 3) | (((color >> 5) & 0x3F) << 10) | (((color >> 11) & 0x1F) << 19) | 0xFF000000

    def interpolateRgba32(self, weight, color0, color1):
        r = (int) ((1.0 - weight) * (color0 & 0xFF) + weight * (color1 & 0xFF))
        g = (int) ((1.0 - weight) * ((color0 & 0xFF00) >> 8)+ weight * ((color1 & 0xFF00) >> 8))
        b = (int) ((1.0 - weight) * ((color0 & 0xFF0000) >> 16) + weight * ((color1 & 0xFF0000) >> 16))
        a = (int) ((1.0 - weight) * ((color0 & 0xFF000000) >> 24) + weight * ((color1 & 0xFF000000) >> 24))
        return (r | (g << 8) | (b << 16) | (a << 24))

    def read(self,  file):
        c0 = self.rgb565ToRgba32(readu16(file))
        c1 = self.rgb565ToRgba32(readu16(file))
        if c0 > c1: 
            c2 = self.interpolateRgba32(0.333333, c0, c1)
            c3 = self.interpolateRgba32(0.666666, c0, c1)
        else:
            c2 = self.interpolateRgba32(0.5, c0, c1)
            c3 = 0
        self.colors = [c0,  c1,  c2,  c3] 
        self.pixels = readu32(file)


    def get_pixel(self, x, y):
        pos = y * 4 + x
        pos = (self.pixels >> (pos * 2)) & 3 
        return self.colors[pos]


class DX5Texel:
    def read(self,  file):
        a0 = readu8(file)
        a1 = readu8(file)
        # read 6 Bytes alpha pixels
        self.alphal = readu8(file)
        self.alphal |= readu8(file) << 8
        self.alphal |= readu8(file) << 16
        self.alphal |= readu8(file) << 24
        self.alphal |= readu8(file) << 32
        self.alphal |= readu8(file) << 40

        self.alpha = [a0,  a1]
        if a0 > a1:
            self.alpha.append((int) ((6.0 * a0 + 1.0 * a1 + 3.0) / 7.0))
            self.alpha.append((int) ((5.0 * a0 + 2.0 * a1 + 3.0) / 7.0))
            self.alpha.append((int) ((4.0 * a0 + 3.0 * a1 + 3.0) / 7.0))
            self.alpha.append((int) ((3.0 * a0 + 4.0 * a1 + 3.0) / 7.0))
            self.alpha.append((int) ((2.0 * a0 + 5.0 * a1 + 3.0) / 7.0))
            self.alpha.append((int) ((1.0 * a0 + 6.0 * a1 + 3.0) / 7.0))
        else:
            self.alpha.append((int) ((4.0 * a0 + 1.0 * a1 + 2.0) / 5.0))
            self.alpha.append((int) ((3.0 * a0 + 2.0 * a1 + 2.0) / 5.0))
            self.alpha.append((int) ((2.0 * a0 + 3.0 * a1 + 2.0) / 5.0))
            self.alpha.append((int) ((1.0 * a0 + 4.0 * a1 + 2.0) / 5.0))
            self.alpha.append(0)
            self.alpha.append(255)
        
        self.dx1_texel = DX1Texel()
        self.dx1_texel.read(file)


    def get_pixel(self, x, y):
        return (self.dx1_texel.get_pixel(x, y) & 0x00FFFFFF) | (self.alpha[(int) ((self.alphal >> (3 * (4 * (3 - y) + x))) & 7)] << 24)


class Header:
    def __init__(self, file):
        self.data_size = readu32(file)
        self.reserved = readu32(file)
        self.width = readu16(file)
        self.height = readu16(file)
        self.encoding = readu8(file)
        self.mipmaps = readu8(file)
        self.unknown = readu16(file)
        # reserved
        file.read(112)

    def __serialize__(self):
        return object_attributes_to_ordered_dict(self, ['data_size', 'reserved', 'width', 'height', 'encoding',  'mipmaps',  'unknown'])


def not_yet_implemented(parsed, erfFile):
    print("not yet implemented")


def swapByte1And3(inValue):
        swap = inValue & 0xFF
        swap = (swap << 16) | (inValue >> 16 & 0xFF)
        return inValue & 0xFF00FF00 | swap

texel_types = {
    2: DX1Texel, 
    4: DX5Texel
}

def extract(parsed, tpc_file):
    with open(tpc_file, 'rb') as f:
        header = Header(f);

        img = Image.new('RGBA', (header.width,  header.height), color = 'cyan')
        draw = ImageDraw.Draw(img)
        for y in range(0,  header.height,  4):
            for x in range(0, header.width, 4):
                texel = texel_types.get(header.encoding)()
                texel.read(f)
                for dy in range(0, 4):
                    for dx in range(0, 4):
                        pixel = texel.get_pixel(dx, dy)
                        draw.point( (x+dx, (header.height-1)-(y+dy)) ,  swapByte1And3(pixel))

        img.save(tpc_file+'.png')
        return img


def execute_action(parsed, erfFile):
    switcher= {
        "extract" : extract,
    }
    func = switcher.get(parsed.action, not_yet_implemented)
    func(parsed, erfFile)


def parse_command_line():
    parser = argparse.ArgumentParser(description='Process ERF files.')
    parser.add_argument('input', help='path to erf file')
    parser.add_argument('-x', action='store_const', dest='action', const='extract', help='Extract file <file> from erf file')

    parsed = parser.parse_args()

    execute_action(parsed, parsed.input)


def main():
    parse_command_line()

main()

