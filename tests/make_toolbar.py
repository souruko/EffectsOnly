#!/usr/bin/env python3
"""Rebuild the toolbar backing art for the split toolbar (2.3.1-2.4.2).

EffectsOnly no longer uses this (2.5.0 dropped the toolbar); its constants
are still imported by validate_skin.py, which checks Barefoot's copy of the
art.  Running it writes into EffectsOnly/, so do not, unless reviving it.

The toolbar's backing is ONE 1024x90 texture, `letterbox_bottom` (and its
monster-play twin `letterbox_bottom_mc`), drawn by `ToolbarFieldMain`.  It has
the main quickslot bar's 12-cell recess painted into its middle, so once the
bar is lifted out and the two halves of the strip close up, the stock art can
no longer line up.  This composes a replacement from the stock art itself:

  * the strip, minus the recess (src x 318..745, 427 px): the left part moves
    right by SH_L, the right part left by SH_R, so the two ornamental curls that
    flanked the recess now meet beside the auto-attack ring;
  * the XP trough (src rows 77..89) rebuilt around its centre plate, which
    stays where it is because the LevelMeter mid caps do;
  * optionally (BAR_FRAME, off) the recess itself, lifted above the strip as
    the quickslot bar's frame.  Its right end is drawn as stock; the left end
    is the right end mirrored, because in the stock art the left curl is fused
    into the auto-attack ring.

The texture is exactly the size of the ToolbarFieldMain override build_skin.py
writes (1024 x ELEMENT_H at y=ELEMENT_Y), since the client does not stretch.
build_skin.py imports the offsets below, so the elements and the art cannot
drift apart.

Inputs: reference/art/letterbox_bottom*.tga, from the U50.2 UI skin art pack
(lotrointerface download 1204).  Outputs: ../toolbar_bottom.tga and
../toolbar_bottom_mc.tga.  Needs Pillow.

    python3 tests/make_toolbar.py
"""

import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# --- shared with build_skin.py --------------------------------------------
SH_L, SH_R = 210, 217            # left half moves right, right half moves left
QS_X, QS_Y = 298, 62             # Toolbar_Quickslot, ToolbarField-local
STOCK_QS = (320, 147)            # its stock position
FIELD_Y = 110                    # ToolbarFieldMain's stock Y in ToolbarField

# --- art geometry, in stock-texture pixels ----------------------------------
CUT_L, CUT_R = 318, 745          # recess removed from the strip
SPLIT = 77                       # rows >= SPLIT are the XP trough band
P0, P1 = 395, 625                # trough centre plate, kept in place
RC_T = 21                        # top of the recess ornament
RC_IN_L, RC_R = 328, 760         # recess interior start, right curl end
END = 25                         # right end piece: recess border + curl
BORDER = 10                      # recess border sits this far into END

# Draw the lifted recess as a frame around the quickslot bar?  Off since
# 2.3.2 -- the bar floats bare above the strip, by request.  With it off,
# ToolbarFieldMain keeps its stock place and size and the texture is native.
BAR_FRAME = False

if BAR_FRAME:
    ELEMENT_Y = RC_T + (QS_Y - (STOCK_QS[1] - FIELD_Y))   # grows up to the frame
else:
    ELEMENT_Y = FIELD_Y
ELEMENT_H = 200 - ELEMENT_Y
ELEMENT_W = 1024

ART = {"letterbox_bottom": "toolbar_bottom.tga",
       "letterbox_bottom_mc": "toolbar_bottom_mc.tga"}


def compose(src):
    from PIL import Image
    src = src.convert("RGBA")
    assert src.size == (1024, 90), "stock art changed size: %s" % (src.size,)
    out = Image.new("RGBA", (ELEMENT_W, ELEMENT_H), (0, 0, 0, 0))
    sy = FIELD_Y - ELEMENT_Y                       # strip origin row
    out.alpha_composite(src.crop((0, 0, CUT_L, SPLIT)), (SH_L, sy))
    out.alpha_composite(src.crop((CUT_R, 0, 1024, SPLIT)), (CUT_R - SH_R, sy))
    out.alpha_composite(src.crop((0, SPLIT, P0 - SH_L, 90)), (SH_L, sy + SPLIT))
    out.alpha_composite(src.crop((P0, SPLIT, P1, 90)), (P0, sy + SPLIT))
    out.alpha_composite(src.crop((P1 + SH_R, SPLIT, 1024, 90)), (P1, sy + SPLIT))
    if not BAR_FRAME:
        return out
    dx = QS_X - STOCK_QS[0]
    ry = RC_T + (QS_Y - (STOCK_QS[1] - FIELD_Y)) - ELEMENT_Y
    right = src.crop((RC_R - END, RC_T, RC_R, SPLIT))
    out.alpha_composite(src.crop((RC_IN_L, RC_T, RC_R - END, SPLIT)), (RC_IN_L + dx, ry))
    out.alpha_composite(right, (RC_R - END + dx, ry))
    out.alpha_composite(right.transpose(Image.FLIP_LEFT_RIGHT),
                        (CUT_L - (END - BORDER) + dx, ry))
    return out


def write_tga(img, path):
    """Uncompressed 32-bit BGRA, bottom-left origin -- the blanks' format."""
    w, h = img.size
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, w, h, 32, 0x08)
    px = img.tobytes("raw", "BGRA")
    rows = [px[y * w * 4:(y + 1) * w * 4] for y in range(h)]
    with open(path, "wb") as fh:
        fh.write(header)
        fh.write(b"".join(reversed(rows)))


def main():
    from PIL import Image
    for asset, out in ART.items():
        src = Image.open(os.path.join(HERE, "reference", "art", asset + ".tga"))
        write_tga(compose(src), os.path.join(ROOT, out))
        print("  %-22s %dx%d  (ToolbarFieldMain at y=%d)" % (out, ELEMENT_W, ELEMENT_H, ELEMENT_Y))


if __name__ == "__main__":
    main()
