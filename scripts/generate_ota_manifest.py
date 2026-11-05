"""Build the files to host on your OTA update server.

Usage (from the repository root):
    python scripts/generate_ota_manifest.py 1.0.1 https://example.com/clock/

Copies every updatable file into ./updates/ and writes updates/version.json
with each file's URL and SHA-256. Upload the contents of updates/ to the URL
you gave. See updates.example/ for the resulting layout.
"""

import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ota_update import UPDATABLE_FILES, parse_version  # noqa: E402


def build(version, base_url, out_dir):
    parse_version(version)
    base_url = base_url.rstrip("/") + "/"
    os.makedirs(out_dir, exist_ok=True)

    files = {}
    for name in UPDATABLE_FILES:
        src = os.path.join(ROOT, name)
        shutil.copyfile(src, os.path.join(out_dir, name))
        with open(src, "rb") as f:
            data = f.read()
        files[name] = {
            "url": base_url + name,
            "checksum": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }

    manifest = {"version": version, "files": files}
    with open(os.path.join(out_dir, "version.json"), "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return manifest


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 1
    manifest = build(argv[1], argv[2], os.path.join(ROOT, "updates"))
    print("Wrote updates/ for version {} ({} files)".format(manifest["version"], len(manifest["files"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
