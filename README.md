# kotor
Some Knights Of The Old Republic Tools for creating command line toolchains.

## key.py

Pack and unpack ressources from key/bif Files. 

```
usage: key.py [-h] [-l] [-u] [-x] [-d] [--dir DIRECTORY]
              keyFile [bifFile] [files [files ...]]

Process KEY and BIF files.

positional arguments:
  keyFile          path to key file (i.e. chitinkey)
  bifFile          bif file referenced from key file
  files            file to extract, delete or update (without extension)

optional arguments:
  -h, --help       show this help message and exit
  -l               List contents of bif or key file
  -x               Extract file <file> from bif file
  -u               Updates a file bif or key file (not yet implemented)
  -d               Delete file <file> from bif file (not yet implemented)
  --dir DIRECTORY  Directory from where to read or where to write to. Defaults
                   to current directory.
```


## 2da.py

Convert 2da files (tabular data) to excel/csv and vice versa.

```
usage: 2da.py [-h] [-x] [-c] [-f {csv,excel}] [--csvsep [CSVSEP]]
              input [output]

Process 2DA files.

positional arguments:
  input              input file
  output             output file (default: derive filename from input file and
                     format)

optional arguments:
  -h, --help         show this help message and exit
  -x                 extract 2da file
  -c                 create 2da file
  -f {csv,excel}     input format: csv or excel. (default: csv)
  --csvsep [CSVSEP]  set csv separator (default: comma ',')
```

## Alternatives

Have a look at xoreos (https://github.com/xoreos/xoreos).


## Resources

* https://github.com/KobaltBlu/KotOR - Source Files to help decompile the file formats found in Star Wars: Knights of the Old Republic
* https://github.com/sste9512/KotorTool - Decompilation of Kotor Tool 2
* https://github.com/Box65535/KotorModTools - Some Java stuff in very early stages
* https://github.com/KobaltBlu/KotOR-Modding-Suite - Some info about where to look for formats
* https://github.com/xoreos/xoreos - A reimplementation of BioWare's Aurora engine (and derivatives). Pre-pre-alpha :P
* https://github.com/xoreos/phaethon - A FLOSS resource explorer for BioWare's Aurora engine games https://xoreos.org/
* https://neverwintervault.org/project/nwn1/other/bioware-aurora-engine-file-format-specifications



