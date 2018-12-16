#!/usr/bin/env python3
import struct

def readlist(function, file, count):
    list = []
    for i in range(count):
        list.append(function(file))
    return list

def readu32(file):
    data = file.read(4);
    return struct.unpack("I", data)[0]

def read32(file):
    data = file.read(4);
    return struct.unpack("i", data)[0]

def readfloat(file):
    data = file.read(4);
    return struct.unpack("f", data)[0]

def readu16(file):
    data = file.read(2);
    return struct.unpack("H", data)[0]

def read16(file):
    data = file.read(2);
    return struct.unpack("h", data)[0]

def readu8(file):
    data = file.read(1);
    return struct.unpack("B", data)[0]

def read8(file):
    data = file.read(1);
    return struct.unpack("b", data)[0]

def printHex(name, number):
    print(name, ":" , number, "0x{0:x}".format(number))

def printHexListOneLine(name, numbers):
    s = "";
    for number in numbers:
        s += "{0} 0x{1:x}, ".format(number, number)
    print(name, ":", s)

def printHexListMultiLine(name, numbers):
    for index in range(len(numbers)):
        printHex(name+str(index+1), numbers[index])

def toHex(list):
    return ["0x{0:x}".format(s) for s in list] 

