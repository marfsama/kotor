#!/usr/bin/env python3

import argparse
import os
import io
import itertools

from openpyxl import Workbook
from tools import *
from collections import OrderedDict

class Header:
    def __init__(self, file):
        self.marker = file.read(4).decode("utf-8")
        self.version = file.read(4).decode("utf-8")

    def __str__(self):
        return """{name}: {{magic: "{marker}{version}"}}""".format(name=type(self).__name__, **vars(self))

class TabularDataFile:
    def __init__(self, column_names, rows):
        self.column_names = column_names
        self.rows = rows

    def __str__(self):
        return """{name}: {{columns: {column_names}, rows: {rows}}}""".format(name=type(self).__name__, **vars(self))

def execute_action(parsed, keyFile):
    switcher= {
        "list" : list_entries,
        "update" : update_entry,
        "extract" : extract_entry,
        "delete" : delete_entry
    }
    func = switcher.get(parsed.action, lambda: print("You need to specify one of -l, -u, -x, -d"))
    func(parsed, keyFile)

def read_byte_by_byte(file):
    """
        returns the file as a byte by byte iterator
    """
    while True:
        yield file.read(1)

def read_tokens(file):
    """
        returns tokens separated by \x00 or tab
    """
    current_column = ""
    for byte in read_byte_by_byte(file):
        if byte in [b"\x00", b"\t"]:
            yield current_column
            current_column = ""
        else:
            current_column = current_column + byte.decode("utf-8")

def read_token_list(file):
    """
        reads tokens until an empty token is encountered
    """
    for token in read_tokens(file):
        if not token:
            break
        yield token


def read_file(file_name):
    with open(file_name, "rb") as file:
        header = Header(file)
        if header.version != "V2.b":
            print ("wrong version. supported is V2.b, version is", header.version)
            return
        # skip new line
        file.read(1)
        # read column names. column names are separated by tab (0x9), a null (0x0) column name signifies the end of the names list
        column_names = list(read_token_list(file))
        # read row count and row indices
        num_rows = read32(file)
        row_indices = list(itertools.islice(read_tokens(file), num_rows))

        # read cell offsets
        cell_offsets = readlist(read16, file, num_rows * len(column_names))

        # read string data into inmemory buffer
        data_size = read16(file)
        data = file.read(data_size)
        data_stream = io.BytesIO(data)

        # parse cell contents from string data
        cell_offset_index = 0
        rows = OrderedDict() # note: use OrderedDict to keep entries and iterations in insertion order
        for row_index in row_indices:
            row = []
            for column_name in column_names:
                data_stream.seek(cell_offsets[cell_offset_index])
                token = next(read_tokens(data_stream))
                row.append(token)
                cell_offset_index = cell_offset_index+1
            rows[row_index] = row

        return TabularDataFile(column_names, rows)

def get_output_filename(parsed):
    if parsed.output_filename:
        return parsed.output_filename
    basename = os.path.splitext(parsed.file)[0]
    format_extensions = {
        "excel" : "xlsx",
        "csv" : "csv"
    }
    return basename + '.' + format_extensions[parsed.format]

def extract_csv(parsed, tabular_data_file):
    output_filename = get_output_filename(parsed)
    csv_delimiter = parsed.csvdelim

    print('extract csv to', output_filename)
    with open(output_filename, 'w') as output:
        output.write('index'+csv_delimiter)
        output.write(csv_delimiter.join(tabular_data_file.column_names))
        output.write('\n')
        for row, values in tabular_data_file.rows.items():
            output.write(row+ csv_delimiter)
            output.write(csv_delimiter.join(values))
            output.write('\n')


def extract_excel(parsed, tabular_data_file):
    output_filename = get_output_filename(parsed)
    print('extract excel to', output_filename)
    wb = Workbook()
    # grab the active worksheet
    ws = wb.active
    # Rows can also be appended
    ws.append(['index']+ tabular_data_file.column_names)

    for row, values in tabular_data_file.rows.items():
        ws.append([row]+values)

    # Save the file
    wb.save(output_filename)
    pass

def create_file(parsed, tabular_data_file):
    pass

def error(parsed, tabular_data_file):
    print("You need to specify one of -x, -c")

def execute_action(parsed, tabular_data_file):
    function = parsed.action+"_"+parsed.format
    switcher= {
        "extract_csv" : extract_csv,
        "extract_excel" : extract_excel,
        "create_csv" : create_file,
        "create_excel" : create_file
    }
    func = switcher.get(function, error)
    func(parsed, tabular_data_file)


def parse_command_line():
    parser = argparse.ArgumentParser(description='Process 2DA files.')
    parser.add_argument('file', metavar='2dafile', help='path to 2da file')
    parser.add_argument('-x', action='store_const', dest='action', const='extract', help='extract 2da file')
    parser.add_argument('-c', action='store_const', dest='action', const='create', help='create 2da file (Not Yet Implemented)')
    parser.add_argument('-o', dest='output_filename', help='output filename. (default: derive filename from input file and format)')
    parser.add_argument('-f', choices=['csv', 'excel'], dest='format', default='csv', help='input format: csv or excel. (default: csv)')
    parser.add_argument('--csvdelim', nargs='?', const=',', default=',', help="set csv delimiter (default: comma ',')")

    parsed = parser.parse_args()

    tabular_data_file = read_file(parsed.file)
    execute_action(parsed, tabular_data_file)


def main():
    parse_command_line()

main()

