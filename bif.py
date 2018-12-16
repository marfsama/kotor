#!/usr/bin/env python3

import struct
import argparse


from functools import partial
from tools import *
from datetime import datetime, timedelta
from hurry.filesize import size


basePath = "/home/mtotz/.local/share/Steam/steamapps/common/Knights of the Old Republic II/steamassets"
bifFile = "data/dialogs.bif"

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


def readBifDirectory(fileName):
    with open(fileName, "rb") as file:
        header = Header(file)
        print (header)
        file.seek(header.variableTableOffset)
        entries = readlist(FileEntry, file, header.numVariableResources)        
        entriesMap = {entry.id:entry  for entry in entries }
        print(entriesMap, sep="\n")


def main():
     readBifDirectory(basePath+"/"+bifFile)


main()

