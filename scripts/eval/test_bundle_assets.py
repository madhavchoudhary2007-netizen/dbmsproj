import json
import gzip
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from bundle_assets import route_gzip_sizes


class BundleAssetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "server/app").mkdir(parents=True)
        (self.root / "server/app-paths-manifest.json").write_text(json.dumps({"/page": "app/page.js", "/about/page": "app/about/page.js"}))
        (self.root / "server/app/about.html").write_text('<script src="/_next/static/chunks/root.js"></script>')
        (self.root / "static/chunks").mkdir(parents=True)
        for name, data in {"root.js": b"root", "layout.js": b"layout", "shared.js": b"shared", "page.js": b"page"}.items():
            (self.root / "static/chunks" / name).write_bytes(data)

    def tearDown(self):
        self.tmp.cleanup()

    def html(self, route, body):
        file = self.root / "server/app" / ("index.html" if route == "/page" else "about.html")
        file.write_text(body)

    def test_html_assets_include_layout_shared_and_count_once_per_route(self):
        body = '<script src="/_next/static/chunks/root.js"></script><script src="/_next/static/chunks/layout.js"></script><link rel="preload" as="script" href="/_next/static/chunks/shared.js"><script src="/_next/static/chunks/page.js"></script><script src="/_next/static/chunks/root.js"></script>'
        self.html("/page", body)
        self.html("/about/page", body)
        sizes = route_gzip_sizes(self.root)
        self.assertEqual(set(sizes), {"/page", "/about/page"})
        self.assertEqual(sizes["/page"], sum(len(__import__("gzip").compress(x)) for x in (b"root", b"layout", b"shared", b"page")))

    def test_nomodule_legacy_asset_is_excluded(self):
        self.html("/page", '<script src="/_next/static/chunks/root.js"></script><script nomodule src="/_next/static/chunks/legacy.js"></script>')
        self.assertEqual(route_gzip_sizes(self.root)["/page"], len(gzip.compress(b"root")))

    def test_missing_asset_and_route_html_fail(self):
        self.html("/page", '<script src="/_next/static/chunks/missing.js"></script>')
        with self.assertRaisesRegex(ValueError, "missing initial asset"):
            route_gzip_sizes(self.root)
        self.html("/page", "")
        with self.assertRaisesRegex(ValueError, "no initial modern scripts"):
            route_gzip_sizes(self.root)
        (self.root / "server/app/index.html").unlink()
        with self.assertRaisesRegex(ValueError, "missing route HTML"):
            route_gzip_sizes(self.root)

    def test_bad_or_empty_route_manifest_fails(self):
        path = self.root / "server/app-paths-manifest.json"
        for value in ("[]", "{}", "not json"):
            path.write_text(value)
            with self.assertRaises(ValueError):
                route_gzip_sizes(self.root)

    def test_external_and_traversal_sources_fail(self):
        for source in ("https://example.test/a.js", "/_next/static/../chunks/root.js"):
            self.html("/page", f'<script src="{source}"></script>')
            with self.assertRaises(ValueError): route_gzip_sizes(self.root)

    def test_large_real_size_is_reported(self):
        rng = random.Random(0)
        data = bytes(rng.getrandbits(8) for _ in range(200_000))
        asset = self.root / "static/chunks/root.js"
        asset.write_bytes(data)
        self.html("/page", '<script src="/_next/static/chunks/root.js"></script>')
        self.assertGreater(route_gzip_sizes(self.root)["/page"], 170 * 1024)

    def test_bundle_gate_checks_all_routes_and_rejects_missing_assets(self):
        script = Path(__file__).with_name("verify-bundle-size.py")
        command = [sys.executable, str(script), "--next-dir", str(self.root)]
        body = '<script src="/_next/static/chunks/root.js"></script>'
        self.html("/page", body)

        small = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(small.returncode, 0, small.stdout + small.stderr)
        self.assertIn("Checked 2 routes", small.stdout)
        self.assertIn("limit: 170 KB (174080 bytes)", small.stdout)

        rng = random.Random(0)
        (self.root / "static/chunks/root.js").write_bytes(
            bytes(rng.getrandbits(8) for _ in range(200_000))
        )
        large = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(large.returncode, 1, large.stdout + large.stderr)
        self.assertIn("170 KB (174080 bytes)", large.stdout)
        self.assertIn("Checked 2 routes", large.stdout)

        self.html("/page", '<script src="/_next/static/chunks/missing.js"></script>')
        missing = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
        self.assertIn("missing initial asset", missing.stdout)


if __name__ == "__main__":
    unittest.main()
