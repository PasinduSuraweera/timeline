"""A minimal indexed-colour PNG encoder.

The band is a dot matrix built from at most a couple of hundred colours, so an
8-bit palette image is both exact and small. Writing it by hand keeps Pillow and
numpy out of the deployment.
"""

import struct
import zlib


def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def encode_indexed(rows, palette, width, height, transparent_index=None):
    """`rows` is a sequence of bytearrays of palette indices, one per scanline."""
    if len(palette) > 256:
        raise ValueError("an indexed PNG holds at most 256 palette entries")
    raw = bytearray()
    for row in rows:
        raw.append(0)          # filter type 0, none
        raw.extend(row)
    out = [b"\x89PNG\r\n\x1a\n"]
    out.append(_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0)))
    out.append(_chunk(b"PLTE", b"".join(bytes(c) for c in palette)))
    if transparent_index is not None:
        alpha = bytearray(255 for _ in palette)
        alpha[transparent_index] = 0
        out.append(_chunk(b"tRNS", bytes(alpha)))
    out.append(_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    out.append(_chunk(b"IEND", b""))
    return b"".join(out)
