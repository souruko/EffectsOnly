#!/usr/bin/env python3
"""Generate the fully transparent TGAs this skin maps its art assets to.

One blank per distinct native size found in `reference/assets.tsv`.  Sizes match
each asset's native dimensions: a 1x1 blank is documented to work (it is the
client's own size-probing trick) but oversizing is the one thing reported to
misbehave, so matching removes the variable entirely.

Every blank is fully transparent.  That is the whole point of this skin, and
`validate_skin.py` enforces it -- see T7.

    python3 tests/make_blanks.py

The TGA writer is inherited unchanged from the EffectsOnly skin, where it was
confirmed to load in-game.  Uncompressed 32-bit BGRA, bottom-left origin.
"""

import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def blank_name(w, h):
    return "blank_%dx%d.tga" % (w, h)


def write_tga(width, height, path, rgba=(0, 0, 0, 0)):
    """Uncompressed 32-bit BGRA. Defaults to fully transparent."""
    header = struct.pack(
        "<BBBHHBHHHHBB",
        0,        # id length
        0,        # colour map type
        2,        # uncompressed true-colour
        0, 0, 0,  # colour map spec
        0, 0,     # x/y origin
        width, height,
        32,       # bits per pixel
        0x08,     # 8 alpha bits, origin bottom-left
    )
    r, g, b, a = rgba
    pixel = bytes((b, g, r, a))          # TGA stores BGRA
    with open(path, "wb") as fh:
        fh.write(header)
        fh.write(pixel * width * height)


def load_sizes():
    path = os.path.join(HERE, "reference", "assets.tsv")
    sizes = {}
    with open(path) as fh:
        next(fh)
        for line in fh:
            if not line.strip():
                continue
            _asset, _stock, _panel, w, h, _size_src = line.rstrip("\n").split("\t")
            sizes.setdefault((int(w), int(h)), 0)
            sizes[(int(w), int(h))] += 1
    return sizes


def main():
    sizes = load_sizes()
    for (w, h), used_by in sorted(sizes.items()):
        name = blank_name(w, h)
        path = os.path.join(ROOT, name)
        write_tga(w, h, path)
        print("  %-22s %4d x %-4d %8d bytes   %3d assets"
              % (name, w, h, os.path.getsize(path), used_by))
    print("\n  %d blanks for %d assets" % (len(sizes), sum(sizes.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
