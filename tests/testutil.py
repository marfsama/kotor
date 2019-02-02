#!/usr/bin/env python3

import io

class SeekLoggingBytesIO(io.BytesIO):
    def __init__(self,  data):
        super(SeekLoggingBytesIO,  self).__init__(data)
        self.seeks = []

    def seek(self,  value):
        self.seeks.append(value)
        
    def tell(self):
        return super(SeekLoggingBytesIO,  self).tell()
