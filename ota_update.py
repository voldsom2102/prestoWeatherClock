"""
Over-the-air (OTA) updates for Presto Weather Clock.

The device fetches ``version.json`` from your own web server, compares it to
the installed version and, if newer, downloads every listed file. Updating is
staged so a failure never leaves a half-updated clock:

1. every file is downloaded to ``<name>.new`` and its SHA-256 is verified;
2. only then are the files swapped in, keeping ``<name>.backup`` copies;
3. if anything goes wrong during the swap, the backups are restored.

Only the names in UPDATABLE_FILES can be written. ``config.py``,
``secrets.py`` and ``ota_config.py`` hold your own settings and are never
touched.
"""

import gc
import os
import time

try:
    import requests
except ImportError:  # plain CPython without requests installed
    requests = None

try:
    import ujson as json
except ImportError:
    import json

try:
    from binascii import hexlify
    import hashlib
except ImportError:
    hashlib = None

try:
    import machine
except ImportError:
    machine = None

UPDATABLE_FILES = (
    "main.py",
    "timeutil.py",
    "weather.py",
    "weather_icons.py",
    "display_ui.py",
    "ota_update.py",
)

VERSION_FILE = "version.json"
NEW_SUFFIX = ".new"
BACKUP_SUFFIX = ".backup"
_CHUNK = 1024


class OTAError(Exception):
    """Raised for any failed check or update. The old version stays in place."""


def _exists(path):
    # MicroPython has no os.path.
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _remove_quietly(path):
    try:
        os.remove(path)
    except OSError:
        pass


def parse_version(text):
    try:
        parts = tuple(int(p) for p in text.split("."))
    except (ValueError, AttributeError):
        raise OTAError("bad version string: {!r}".format(text))
    if not parts:
        raise OTAError("bad version string: {!r}".format(text))
    return parts


def sha256_hex(data):
    h = hashlib.sha256()
    h.update(data)
    return hexlify(h.digest()).decode()


def installed_version():
    try:
        with open(VERSION_FILE) as f:
            return json.load(f).get("version", "0.0.0")
    except (OSError, ValueError):
        return "0.0.0"


def _get(url, timeout):
    if requests is None:
        raise OTAError("the requests module is not available")
    try:
        response = requests.get(url, timeout=timeout)
    except Exception as err:  # noqa: BLE001 - network errors vary by port
        raise OTAError("request to {} failed: {}".format(url, err))
    if response.status_code != 200:
        status = response.status_code
        response.close()
        raise OTAError("{} returned HTTP {}".format(url, status))
    return response


def check_for_updates(base_url, current=None):
    """Return the server manifest if it is newer than ``current``, else None."""
    base_url = base_url.rstrip("/") + "/"
    response = _get(base_url + VERSION_FILE, 10)
    try:
        manifest = response.json()
    except Exception as err:  # noqa: BLE001
        raise OTAError("invalid manifest: {}".format(err))
    finally:
        response.close()

    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise OTAError("invalid manifest: missing 'files'")
    if parse_version(manifest.get("version")) <= parse_version(current or installed_version()):
        return None
    manifest["_base_url"] = base_url
    return manifest


def _download(name, info, base_url):
    """Download one file to <name>.new and verify its SHA-256."""
    checksum = info.get("checksum")
    if not checksum:
        raise OTAError("manifest has no checksum for {}".format(name))
    url = info.get("url") or name
    if not url.startswith("http"):
        url = base_url + url

    response = _get(url, 30)
    try:
        data = response.content
    finally:
        response.close()

    actual = sha256_hex(data)
    if actual != checksum.lower():
        raise OTAError("checksum mismatch for {}".format(name))

    temp = name + NEW_SUFFIX
    try:
        with open(temp, "wb") as f:
            f.write(data)
    except OSError as err:
        raise OTAError("could not write {}: {}".format(temp, err))


def _commit(names, new_version):
    """Swap staged files into place; undo everything if any step fails."""
    swapped = []  # (name, had_original)
    try:
        for name in names:
            had_original = _exists(name)
            if had_original:
                _remove_quietly(name + BACKUP_SUFFIX)
                os.rename(name, name + BACKUP_SUFFIX)
            swapped.append((name, had_original))
            os.rename(name + NEW_SUFFIX, name)

        version_backup = None
        if _exists(VERSION_FILE):
            version_backup = VERSION_FILE + BACKUP_SUFFIX
            _remove_quietly(version_backup)
            os.rename(VERSION_FILE, version_backup)
        try:
            with open(VERSION_FILE, "w") as f:
                json.dump({"version": new_version}, f)
        except OSError:
            _remove_quietly(VERSION_FILE)
            if version_backup:
                os.rename(version_backup, VERSION_FILE)
            raise
        if version_backup:
            _remove_quietly(version_backup)
    except Exception as err:  # noqa: BLE001
        for name, had_original in reversed(swapped):
            _remove_quietly(name)
            if had_original:
                try:
                    os.rename(name + BACKUP_SUFFIX, name)
                except OSError:
                    pass
        raise OTAError("update failed and was rolled back: {}".format(err))

    for name, had_original in swapped:
        if had_original:
            _remove_quietly(name + BACKUP_SUFFIX)


def perform_update(manifest):
    """Download, verify and install every file in ``manifest``."""
    files = manifest["files"]
    if not files:
        raise OTAError("manifest lists no files")
    for name in files:
        if name not in UPDATABLE_FILES:
            raise OTAError("{} is not allowed to be updated".format(name))
    if hashlib is None:
        raise OTAError("hashlib is not available")

    base_url = manifest.get("_base_url", "")
    names = sorted(files)
    try:
        for name in names:
            _download(name, files[name], base_url)
            gc.collect()
    except Exception:
        for name in names:
            _remove_quietly(name + NEW_SUFFIX)
        raise
    _commit(names, manifest["version"])


def check_and_update(base_url, status=print, reboot=True):
    """Check once and install if newer. Returns True if an update was installed.

    Never raises: failures are reported through ``status`` and the clock
    carries on with the version it already has.
    """
    try:
        status("Checking for updates...")
        manifest = check_for_updates(base_url)
        if manifest is None:
            return False
        status("Updating to {}...".format(manifest["version"]))
        perform_update(manifest)
    except Exception as err:  # noqa: BLE001 - never take the clock down
        status("Update failed:\n{}".format(err))
        time.sleep(2)
        return False

    status("Updated to {}\nRestarting...".format(manifest["version"]))
    time.sleep(2)
    if reboot and machine is not None:
        machine.reset()
    return True
