import hashlib
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import ota_update
from ota_update import OTAError


def _response(status=200, json_data=None, content=b""):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = json_data
    r.content = content
    return r


def _sha(data):
    return hashlib.sha256(data).hexdigest()


class InTempDir(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def write(self, name, text):
        with open(name, "w") as f:
            f.write(text)

    def read(self, name):
        with open(name) as f:
            return f.read()


class VersionTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(ota_update.parse_version("1.2.3"), (1, 2, 3))
        self.assertGreater(ota_update.parse_version("1.10.0"), ota_update.parse_version("1.9.0"))

    def test_invalid(self):
        for bad in ("abc", "", None):
            with self.assertRaises(OTAError):
                ota_update.parse_version(bad)


class CheckTests(InTempDir):
    def manifest(self, version):
        return {"version": version, "files": {"main.py": {"checksum": "x"}}}

    def test_newer_returns_manifest(self):
        with patch.object(ota_update, "requests") as req:
            req.get.return_value = _response(json_data=self.manifest("2.0.0"))
            result = ota_update.check_for_updates("http://h/u", current="1.0.0")
        self.assertEqual(result["version"], "2.0.0")
        self.assertEqual(result["_base_url"], "http://h/u/")

    def test_same_version_returns_none(self):
        with patch.object(ota_update, "requests") as req:
            req.get.return_value = _response(json_data=self.manifest("1.0.0"))
            self.assertIsNone(ota_update.check_for_updates("http://h/u", current="1.0.0"))

    def test_http_error(self):
        with patch.object(ota_update, "requests") as req:
            req.get.return_value = _response(status=404)
            with self.assertRaises(OTAError):
                ota_update.check_for_updates("http://h/u", current="1.0.0")

    def test_network_error(self):
        with patch.object(ota_update, "requests") as req:
            req.get.side_effect = OSError("down")
            with self.assertRaises(OTAError):
                ota_update.check_for_updates("http://h/u", current="1.0.0")

    def test_installed_version_default_and_file(self):
        self.assertEqual(ota_update.installed_version(), "0.0.0")
        self.write("version.json", json.dumps({"version": "1.4.0"}))
        self.assertEqual(ota_update.installed_version(), "1.4.0")


class UpdateTests(InTempDir):
    def manifest(self, files, version="2.0.0"):
        return {
            "version": version,
            "_base_url": "http://h/u/",
            "files": {n: {"checksum": _sha(c), "url": "http://h/u/" + n} for n, c in files.items()},
        }

    def serve(self, contents):
        def get(url, timeout=None):
            name = url.rsplit("/", 1)[1]
            return _response(content=contents[name])

        return patch.object(ota_update, "requests", MagicMock(get=get))

    def test_success_replaces_files_and_cleans_up(self):
        self.write("main.py", "old")
        self.write("version.json", json.dumps({"version": "1.0.0"}))
        new = {"main.py": b"new main", "weather.py": b"new weather"}
        with self.serve(new):
            ota_update.perform_update(self.manifest(new))
        self.assertEqual(self.read("main.py"), "new main")
        self.assertEqual(self.read("weather.py"), "new weather")
        self.assertEqual(ota_update.installed_version(), "2.0.0")
        self.assertEqual(sorted(os.listdir(".")), ["main.py", "version.json", "weather.py"])

    def test_checksum_mismatch_touches_nothing(self):
        self.write("main.py", "old")
        m = self.manifest({"main.py": b"new"})
        m["files"]["main.py"]["checksum"] = "0" * 64
        with self.serve({"main.py": b"new"}):
            with self.assertRaises(OTAError):
                ota_update.perform_update(m)
        self.assertEqual(self.read("main.py"), "old")
        self.assertEqual(os.listdir("."), ["main.py"])

    def test_second_file_failure_leaves_no_partial_update(self):
        self.write("main.py", "old")
        good = {"main.py": b"new"}
        m = self.manifest({"main.py": b"new", "weather.py": b"w"})
        with self.serve(good):  # weather.py is missing -> KeyError -> OTAError
            with self.assertRaises(OTAError):
                ota_update.perform_update(m)
        self.assertEqual(self.read("main.py"), "old")
        self.assertEqual(os.listdir("."), ["main.py"])

    def test_commit_failure_rolls_back(self):
        self.write("main.py", "old main")
        self.write("weather.py", "old weather")
        new = {"main.py": b"new main", "weather.py": b"new weather"}
        real_rename = os.rename

        def flaky(src, dst):
            if src == "weather.py.new":
                raise OSError("disk error")
            real_rename(src, dst)

        with self.serve(new), patch.object(ota_update.os, "rename", flaky):
            with self.assertRaises(OTAError):
                ota_update.perform_update(self.manifest(new))
        self.assertEqual(self.read("main.py"), "old main")
        self.assertEqual(self.read("weather.py"), "old weather")

    def test_rejects_protected_files(self):
        for name in ("secrets.py", "config.py", "ota_config.py", "../x.py"):
            m = {"version": "2.0.0", "files": {name: {"checksum": "x"}}}
            with self.assertRaises(OTAError):
                ota_update.perform_update(m)

    def test_requires_checksum(self):
        m = {"version": "2.0.0", "_base_url": "http://h/", "files": {"main.py": {}}}
        with self.serve({"main.py": b"x"}):
            with self.assertRaises(OTAError):
                ota_update.perform_update(m)


class CheckAndUpdateTests(InTempDir):
    def test_failure_is_reported_not_raised(self):
        messages = []
        with patch.object(ota_update, "requests") as req, patch.object(ota_update.time, "sleep"):
            req.get.side_effect = OSError("down")
            self.assertFalse(ota_update.check_and_update("http://h/", status=messages.append))
        self.assertTrue(messages[-1].startswith("Update failed"))

    def test_no_update(self):
        with patch.object(ota_update, "check_for_updates", return_value=None):
            self.assertFalse(ota_update.check_and_update("http://h/", status=lambda m: None))

    def test_success_reboots(self):
        m = {"version": "2.0.0"}
        fake_machine = MagicMock()
        with patch.object(ota_update, "check_for_updates", return_value=m), \
                patch.object(ota_update, "perform_update"), \
                patch.object(ota_update, "machine", fake_machine), \
                patch.object(ota_update.time, "sleep"):
            self.assertTrue(ota_update.check_and_update("http://h/", status=lambda m: None))
        fake_machine.reset.assert_called_once()


if __name__ == "__main__":
    unittest.main()
