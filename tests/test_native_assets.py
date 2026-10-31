"""Read-only NPK candidate tools and explicit copy-only patch tests."""
import io
from pathlib import Path
import struct
import tempfile
import unittest

import lz4.block
from PIL import Image

from native_assets import RECORD, _xor_prefix, read_candidate, build_experimental_copy, export_preview


def make_archive(directory, compressed):
    image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    for x in range(4, 16):
        image.putpixel((x, 10), (255, 255, 255, 200))
    out = io.BytesIO()
    image.save(out, format="PNG")
    original = out.getvalue()
    packed = lz4.block.compress(original, store_size=False) if compressed else original
    record = RECORD.pack(0x12345678, 28, len(packed), len(original),
                         0, 0, 2 if compressed else 0, 1, 0)
    header = bytearray(28)
    header[:4] = b"NXPK"
    struct.pack_into("<I", header, 4, 1)
    struct.pack_into("<I", header, 20, 28+len(packed))
    path = Path(directory) / "test.npk"
    path.write_bytes(header+_xor_prefix(packed)+record)
    return path


class NativeAssetTests(unittest.TestCase):
    def test_archive_copy_round_trip_and_never_overwrite(self):
        for compressed in (False, True):
            with self.subTest(compressed=compressed), tempfile.TemporaryDirectory() as directory:
                parent = Path(directory)
                source = make_archive(directory, compressed)
                snapshot = source.read_bytes()
                original, _ = read_candidate(source, 0)
                result = parent / "experimental.npk"
                report = build_experimental_copy(source, 0, "#11FFAA", result)
                revised, _ = read_candidate(result, 0)
                self.assertEqual(source.read_bytes(), snapshot)
                self.assertNotEqual(original.tobytes(), revised.tobytes())
                self.assertEqual(report["index"], 0)
                self.assertIn("Unverified", report["warning"])
                export_preview(source, 0, "#FF22EE", parent / "preview.png")
                self.assertTrue((parent / "preview.png").is_file())
                with self.assertRaises(ValueError):
                    build_experimental_copy(source, 0, "#FFFFFF", source)
                with self.assertRaises(ValueError):
                    build_experimental_copy(source, 0, "#FFFFFF", result)


if __name__ == "__main__":
    unittest.main()
