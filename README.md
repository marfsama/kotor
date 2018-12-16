# kotor
Some Knights Of The Old Republic Tools for creating command line toolchains.

## key.py

```
usage: key.py [-h] [-l] [-u] [-x] [-d] keyFile [bifFile] [file [file ...]]

Process KEY and BIF files.

positional arguments:
  keyFile     path to key file (i.e. chitinkey)
  bifFile     bif file referenced from key file
  file        file to extract, delete or update (without extension)

optional arguments:
  -h, --help  show this help message and exit
  -l          List contents of bif or key file
  -u          updates a file bif or key file (not yet implemented)
  -x          Extract file <file> from bif file (not yet implemented)
  -d          Delete file <file> from bif file (not yet implemented)
```

## Resources

* https://github.com/KobaltBlu/KotOR - Source Files to help decompile the file formats found in Star Wars: Knights of the Old Republic
* https://github.com/sste9512/KotorTool - Decompilation of Kotor Tool 2
* https://github.com/Box65535/KotorModTools - Some Java stuff in very early stages
* https://github.com/KobaltBlu/KotOR-Modding-Suite - Some info about where to look for formats
* https://github.com/xoreos/xoreos - A reimplementation of BioWare's Aurora engine (and derivatives). Pre-pre-alpha :P
* https://github.com/xoreos/phaethon - A FLOSS resource explorer for BioWare's Aurora engine games https://xoreos.org/
* https://neverwintervault.org/project/nwn1/other/bioware-aurora-engine-file-format-specifications



