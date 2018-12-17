#!/usr/bin/env python3

import struct
import argparse


from functools import partial
from tools import *
from datetime import datetime, timedelta
from hurry.filesize import size

# size of byte chunks to read
CHUCK_SIZE = 4096

class FileEntry:
    def __init__(self, file):
        self.id = read32(file) & 0xFFFFF
        self.offset = read32(file)
        self.size = read32(file)
        self.type = read32(file)

    def __str__(self):
        return """FileEntry: {{id: {id}, offset: 0x{offset:x}, size: {size}, type: {type}}}""".format(**vars(self))

class Header:
    def __init__(self, file):
        self.marker = file.read(4).decode("utf-8")
        self.version = file.read(4).decode("utf-8")
        self.numVariableResources = readu32(file)
        self.numFixedResources = readu32(file)
        self.variableTableOffset = readu32(file)

    def __str__(self):
        return """{name}: {{magic: "{marker}{version}", numVariableResources: {numVariableResources}, numFixedResources: {numFixedResources}, variableTableOffset: 0x{variableTableOffset:x}}}""".format(name=type(self).__name__, **vars(self))


def read_bif_directory(fileName):
    with open(fileName, "rb") as file:
        header = Header(file)
        file.seek(header.variableTableOffset)
        entries = readlist(FileEntry, file, header.numVariableResources)        
        entriesMap = {entry.id:entry  for entry in entries }
        return entriesMap

def read_bif_file(bif_file, bif_file_entry):
    """
        returns an iterator over 4k blocks of byte data
        @param biffile an IOBase Stream, i.e. File
        @param biffileEntry the entry which should be read
    """
    remaining = bif_file_entry.size
    bif_file.seek(bif_file_entry.offset)
    while remaining > 0:
        data = bif_file.read(min(remaining, CHUCK_SIZE))
        if not data:
            raise IOError("unexpected end of stream, {} bytes remaining".format(remaining))
        remaining = remaining - len(data)
        yield data































