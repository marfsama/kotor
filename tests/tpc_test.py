import kotor.tpc as tpc
from .testutil import *
from kotor.tools import *
import io
import struct


def test_dx1_full_interpolate():
    c0 = 0xff5054a8
    c1 = 0xff882010
    c2 = 0xff624275
    c3 = 0xff753142
    input = struct.pack("=HH I", 0xAAAA, 0x1111 , 0xFEDCBA98) 
    # 00 10 01 10
    # 10 10 11 10
    # 00 11 01 11
    # 10 11 11 11
    texel = tpc.DX1Texel()
    texel.read(io.BytesIO(input))
    assert texel.get_pixel(0, 0) == c0
    assert texel.get_pixel(3, 3) == c3
    assert texel.get_pixel(1, 1) == c2
    assert texel.get_pixel(2, 2) == c1


def test_dx1_interpolate_with_zero():
    c0 = 0xff882010
    c1 = 0xff5054a8
    c2 = 0xff6c3a5c
    c3 = 0
    input = struct.pack("=HH I",0x1111, 0xAAAA, 0xFEDCBA98) 
    # 00 10 01 10
    # 10 10 11 10
    # 00 11 01 11
    # 10 11 11 11
    texel = tpc.DX1Texel()
    texel.read(io.BytesIO(input))
    assert texel.get_pixel(0, 0) == c0
    assert texel.get_pixel(3, 3) == c3
    assert texel.get_pixel(1, 1) == c2
    assert texel.get_pixel(2, 2) == c1





