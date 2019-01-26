#!/usr/bin/env python3

import argparse

from tools import *
from hurry.filesize import size

from key import BuildDate, ressourceTypeTable, RessourceType

class ErfFile:
    def __init__(self, header, entries):
        self.header = header
        self.entries = entries

class FileEntry:
    def __init__(self, file):
        self.name = file.read(16).partition(b'\0')[0].decode("utf-8")
        self.id = read32(file)
        resourceTypeId = read16(file)
        self.type = ressourceTypeTable.get(resourceTypeId, RessourceType(resourceTypeId, 'NA{}'.format(resourceTypeId), 'Invalid resource type'))
        self.filename = self.name+'.'+self.type.extension
        # unused
        file.read(2)
        # read later

    def read_size_offset(self, file):
        self.offset = read32(file)
        self.size = read32(file)

    def __str__(self):
        return """FileEntry: {{name: {name}, id: {id}, type: {type}, size: {size}, offset: 0x{offset:x}}}""".format(**vars(self))


class Header:
    def __init__(self, file):
        self.marker = file.read(4).decode("utf-8")
        self.version = file.read(4).decode("utf-8")
        self.string_count = readu32(file)
        self.string_size = readu32(file)
        self.entry_count = readu32(file)
        self.string_offset = readu32(file)
        self.key_offset = readu32(file)
        self.ressources_offset = readu32(file)
        self.build = BuildDate(readu32(file), readu32(file))
        self.description = readu32(file)
        # reserved
        file.read(116)

    def __str__(self):
        return """{name}: {{magic: "{marker}{version}", string_count: {string_count}, string_size: {string_size}, entry_count: {entry_count}, string_offset: 0x{string_offset:x}, key_offset: 0x{key_offset:x}, ressources_offset: 0x{ressources_offset:x}, build: {build}, description: 0x{description:x}}}""".format(name=type(self).__name__, **vars(self))


def readErfDirectory(fileName):
    with open(fileName, "rb") as file:
        header = Header(file)
        if header.string_count > 0:
            print("error: localized string loading not yet supported")
            return
        file.seek(header.key_offset)
        entries = readlist(FileEntry, file, header.entry_count)

        file.seek(header.ressources_offset)
        for entry in entries:
            entry.read_size_offset(file)

        return ErfFile(header, entries)

def list_entries(parsed, erfFile):
    print ("{:>7} {:>7}".format('size', 'name'))
    for entry in erfFile.entries:
        print ("{:>7} {:>7}".format(size(entry.size), entry.filename))


def extract_entry(parsed, erfFile):
    entry = next((entry for entry in erfFile.entries if entry.filename == parsed.file), None)

    with open(parsed.input, "rb") as file:
        with open(entry.filename, "wb") as destination_file:
            for chunk in read_partial_stream(file, entry.offset, entry.size):
                destination_file.write(chunk)

    print ("extracted", entry.filename)


def not_yet_implemented(parsed, erfFile):
    print("not yet implemented")

def execute_action(parsed, erfFile):
    switcher= {
        "list" : list_entries,
        "extract" : extract_entry,
        "update" : not_yet_implemented,
        "delete" : not_yet_implemented
    }
    func = switcher.get(parsed.action, not_yet_implemented)
    func(parsed, erfFile)


def parse_command_line():
    parser = argparse.ArgumentParser(description='Process ERF files.')
    parser.add_argument('input', help='path to erf file')
    parser.add_argument('file', nargs="?", help='file to extract/delete/update')
    parser.add_argument('-l', action='store_const', dest='action', const='list', help='List contents of bif or key file')
    parser.add_argument('-x', action='store_const', dest='action', const='extract', help='Extract file <file> from erf file')
    parser.add_argument('-u', action='store_const', dest='action', const='update', help='Updates a file entry in erf file (not yet implemented)')
    parser.add_argument('-d', action='store_const', dest='action', const='delete', help='Delete file <file> from erf file  (not yet implemented)')
    parser.add_argument('--dir', action='store', dest='directory', help='Directory from where to read or where to write to. Defaults to current directory.  (not yet implemented)')

    parsed = parser.parse_args()

    erfFile = readErfDirectory(parsed.input)
    execute_action(parsed, erfFile)


def main():
    parse_command_line()

main()

