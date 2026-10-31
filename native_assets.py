"""Copy-only NXPK candidate inspection and experimental patching.
No anti-cheat bypass, runtime injection or automatic game file changes.
Resource IDs are visual CANDIDATES, NOT verified combat crosshairs.
"""
from __future__ import annotations
import io
import mmap
from pathlib import Path
import struct
import lz4.block
from PIL import Image

RECORD = struct.Struct("<IIIIIIHBB")
HEADER_TABLE_OFFSET = 20
PNG_SIG = b"\x89PNG\r\n\x1a\n"
MAX_ASSET_BYTES = 24 * 1024 * 1024
CANDIDATES = {
    580: ("086c5799", "White ring (unverified)"),
    9045: ("89f33979", "Three arc ring (unverified)"),
    8182: ("7cde6fda", "Alternate ring (unverified)"),
    15336: ("e8b3e95d", "Multi-segment ring (unverified)"),
}

class ArchiveError(ValueError):
    pass

def archive_overview(archive):
    """Fast read-only archive verification without loading the 605 MB file."""
    archive = Path(archive)
    if not archive.is_file() or archive.suffix.lower() != ".npk":
        raise ArchiveError("Choose an extracted .npk file, not a .7z volume.")
    size = archive.stat().st_size
    if size < 28:
        raise ArchiveError("The NPK archive is incomplete.")
    with archive.open("rb") as stream:
        header = stream.read(28)
        if header[:4] != b"NXPK":
            raise ArchiveError("This is not an NXPK archive.")
        count = struct.unpack_from("<I", header, 4)[0]
        table = struct.unpack_from("<I", header, HEADER_TABLE_OFFSET)[0]
        if not 0 < count <= 100_000 or table < 28 or table + count * RECORD.size != size:
            raise ArchiveError("Invalid or incomplete NPK resource table.")
        matched = []
        for index, (expected_id, _) in CANDIDATES.items():
            if index >= count:
                continue
            stream.seek(table + index * RECORD.size)
            rid = struct.unpack("<I", stream.read(4))[0]
            if f"{rid:08x}" == expected_id:
                matched.append(index)
    return {
        "filename": archive.name,
        "size_bytes": size,
        "size_mb": size / (1024 * 1024),
        "resource_count": count,
        "matched_candidates": tuple(matched),
    }


def _index(mm):
    if len(mm) < 32 or mm[:4] != b"NXPK":
        raise ArchiveError("Not a supported NXPK archive.")
    count = struct.unpack_from("<I", mm, 4)[0]
    table = struct.unpack_from("<I", mm, HEADER_TABLE_OFFSET)[0]
    if not 0 < count <= 100_000 or table < 28 or table + count * RECORD.size != len(mm):
        raise ArchiveError("Unsupported NXPK index or incomplete archive.")
    return count, table

def _entry(mm, index):
    count, table = _index(mm)
    if not 0 <= index < count:
        raise ArchiveError(f"Resource index must be in 0..{count - 1}.")
    row = list(RECORD.unpack_from(mm, table + index * RECORD.size))
    rid, offset, packed, unpacked = row[:4]
    if not 0 < packed <= MAX_ASSET_BYTES or not 0 < unpacked <= MAX_ASSET_BYTES:
        raise ArchiveError("Asset exceeds safe size bounds.")
    if offset < 28 or offset + packed > table:
        raise ArchiveError("Asset offset is invalid.")
    return row

def _xor_prefix(data):
    result = bytearray(data)
    for i in range(min(128, len(result))):
        result[i] ^= (i + 254) & 255
    return bytes(result)

def _decode(mm, index):
    row = _entry(mm, index)
    offset, packed, unpacked = row[1:4]
    data = _xor_prefix(mm[offset:offset+packed])
    if packed != unpacked:
        try:
            data = lz4.block.decompress(data, uncompressed_size=unpacked)
        except Exception as exc:
            raise ArchiveError("Unable to decompress resource.") from exc
    if not data.startswith(PNG_SIG):
        raise ArchiveError("Selected resource is not a PNG.")
    return data, row

def read_candidate(archive, index):
    with Path(archive).open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        data, row = _decode(mm, index)
    if index in CANDIDATES and f"{row[0]:08x}" != CANDIDATES[index][0]:
        raise ArchiveError("This NPK has different resource IDs from the inspected archive.")
    image = Image.open(io.BytesIO(data))
    image.load()
    return image.convert("RGBA"), {
        "index": index, "id": f"{row[0]:08x}", "packed": row[2],
        "unpacked": row[3], "dimensions": image.size
    }

def recolor_white(image, hex_color):
    if not isinstance(hex_color, str) or len(hex_color) != 7 or not hex_color.startswith("#"):
        raise ArchiveError("Color must have format #RRGGBB.")
    try:
        desired = bytes.fromhex(hex_color[1:])
    except ValueError as exc:
        raise ArchiveError("Color must have format #RRGGBB.") from exc
    result = image.convert("RGBA")
    pixels = result.load()
    for y in range(result.height):
        for x in range(result.width):
            r,g,b,a = pixels[x,y]
            if a and max(r,g,b)-min(r,g,b) <= 55 and max(r,g,b) >= 115:
                shade = max(0.25, max(r,g,b)/255)
                pixels[x,y] = tuple(round(c*shade) for c in desired)+(a,)
    return result

def export_preview(archive, index, hex_color, output):
    image, info = read_candidate(archive, index)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    recolor_white(image, hex_color).save(output, format="PNG")
    return info

def build_experimental_copy(archive, index, hex_color, output):
    """Create a separate NPK with one changed PNG; never overwrite original.
    Unknown hash fields are preserved. The game may reject this archive.
    """
    archive, output = Path(archive), Path(output)
    if archive.resolve() == output.resolve():
        raise ArchiveError("Original archive will never be overwritten.")
    if output.exists():
        raise ArchiveError("Destination already exists. Choose a new filename.")
    with archive.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        image, info = read_candidate(archive, index)
        data_io = io.BytesIO()
        recolor_white(image, hex_color).save(data_io, format="PNG")
        decoded = data_io.getvalue()
        _, row = _decode(mm, index)
        compressed = row[6] == 2 and row[2] != row[3]
        payload = lz4.block.compress(decoded, store_size=False) if compressed else decoded
        encoded = _xor_prefix(payload)
        count, table = _index(mm)
        entries = bytearray(mm[table:table+count*RECORD.size])
        updated = list(row)
        updated[1], updated[2], updated[3] = table, len(encoded), len(decoded)
        RECORD.pack_into(entries, index*RECORD.size, *updated)
        new_table_offset = table+len(encoded)
        if new_table_offset+len(entries) > 0xFFFFFFFF:
            raise ArchiveError("Archive exceeds 32-bit index format.")
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_name(output.name+".incomplete")
        if temp.exists():
            raise ArchiveError("An incomplete patch file already exists. Remove it manually.")
        try:
            with temp.open("xb") as out:
                for start in range(0, table, 8*1024*1024):
                    out.write(mm[start:min(start+8*1024*1024, table)])
                out.write(encoded)
                out.write(entries)
                out.seek(HEADER_TABLE_OFFSET)
                out.write(struct.pack("<I", new_table_offset))
            with temp.open("rb") as verify, mmap.mmap(verify.fileno(),0,access=mmap.ACCESS_READ) as mm2:
                result, updated_row = _decode(mm2,index)
                if result != decoded or updated_row[0] != row[0] or _index(mm2)[0] != count:
                    raise ArchiveError("Verification failed; no patch was saved.")
            temp.rename(output)
        except Exception:
            if temp.exists():
                temp.unlink()
            raise
    return {
        "output": str(output), "index": index, "id": info["id"],
        "size": output.stat().st_size,
        "warning": "Unverified game compatibility and crosshair resource ID."
    }
