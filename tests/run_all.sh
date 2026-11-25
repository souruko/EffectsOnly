#!/bin/sh
# Validate every skin in ../ before loading any of it in the client.
#
# The client reports nothing: a malformed file vanishes from the in-game
# dropdown, a bad ArtAssetID is silently ignored, and a missing replacement
# draws an opaque checkerboard. Each of those costs a full restart to find.
#
#   sh tests/run_all.sh

set -e
here=$(cd "$(dirname "$0")" && pwd)
skin=$(dirname "$here")
skins=$(dirname "$skin")
status=0

echo "=== regenerating from reference/assets.tsv ==="
python3 "$here/make_blanks.py"
python3 "$here/build_skin.py"
echo

echo "=== $(basename "$skin") ==="
python3 "$here/validate_skin.py" "$skin" || status=1
echo

for dir in "$skins"/*/; do
    name=$(basename "$dir")
    [ "$name" = "$(basename "$skin")" ] && continue
    [ -f "$dir/SkinDefinition.xml" ] || continue
    echo "=== $name ==="
    case "$name" in
        ZZ*) python3 "$here/validate_skin.py" "$dir" --probe || status=1 ;;
        *)   python3 "$here/validate_skin.py" "$dir" || status=1 ;;
    esac
    echo
done

echo "=== validator selftest ==="
python3 "$here/selftest.py" || status=1
echo

if [ "$status" -eq 0 ]; then
    echo "all green"
else
    echo "FAILURES -- do not load in the client"
fi
exit "$status"
