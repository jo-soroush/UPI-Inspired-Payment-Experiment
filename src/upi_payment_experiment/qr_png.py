"""Dependency-free PNG encoding for the grayscale image produced by C05."""

from binascii import crc32
import struct
import zlib


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class PngEncodingError(ValueError):
    """The supplied C05 image cannot be represented by this bounded encoder."""


def encode_grayscale_png(image: object) -> bytes:
    """Encode one contiguous 8-bit two-dimensional image as browser-ready PNG."""

    try:
        view = memoryview(image)
    except TypeError as error:
        raise PngEncodingError("QR image does not expose a byte buffer") from error

    if view.ndim != 2 or view.itemsize != 1 or view.format != "B":
        raise PngEncodingError("QR image must be a two-dimensional 8-bit buffer")

    height, width = view.shape
    if width <= 0 or height <= 0:
        raise PngEncodingError("QR image dimensions must be positive")

    pixels = view.tobytes()
    if len(pixels) != width * height:
        raise PngEncodingError("QR image buffer size does not match its dimensions")

    scanlines = b"".join(
        b"\x00" + pixels[row_start : row_start + width]
        for row_start in range(0, len(pixels), width)
    )
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return b"".join(
        (
            PNG_SIGNATURE,
            _chunk(b"IHDR", header),
            _chunk(b"IDAT", zlib.compress(scanlines, level=9)),
            _chunk(b"IEND", b""),
        )
    )


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", checksum)
