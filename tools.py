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

# size of byte chunks to read
CHUNK_SIZE = 4096

def read_partial_stream(file, offset, size):
    """
        returns an iterator over 4k blocks of byte data
        @param file an IOBase Stream, i.e. File
        @param offset offset from where to read
        @param size size of block to read

    """
    remaining = size
    file.seek(offset)
    while remaining > 0:
        data = file.read(min(remaining, CHUNK_SIZE))
        if not data:
            raise IOError("unexpected end of stream, {} bytes remaining".format(remaining))
        remaining = remaining - len(data)
        yield data

def read_byte_by_byte(file):
    """
        returns the file as a byte by byte iterator
    """
    while True:
        yield file.read(1)

def read_terminated_token(file, terminator_function):
    """
        returns tokens until a separator is found. the separator is not returned.
    """
    result = b""
    for byte in read_byte_by_byte(file):
        if terminator_function(byte):
            yield result
            result = b""
        else:
            result = result + byte

def null_terminated(byte):
    return byte == b"\x00"

def visit_tree(node, get_childs_function, visitor, depth=0):
    visitor(node, depth)
    for child in get_childs_function(node):
         visit_tree(child, get_childs_function, visitor, depth + 1)


def iterate_tree(node, get_childs_function):
    yield node
    for child in get_childs_function(node):
        yield from iterate_tree(child, get_childs_function)





