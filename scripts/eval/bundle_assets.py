"""Measure per-route initial JavaScript from emitted Next.js route HTML."""
import gzip
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


class _Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and "nomodule" not in attrs and attrs.get("src"):
            self.sources.add(attrs["src"])
        if tag == "link" and "preload" in attrs.get("rel", "").lower().split() and attrs.get("as", "").lower() == "script" and attrs.get("href"):
            self.sources.add(attrs["href"])


def _asset_path(source):
    url = urlsplit(source)
    path = unquote(url.path)
    if url.scheme or url.netloc or "\\" in path or not path.startswith("/_next/"):
        raise ValueError(f"unexpected initial script source: {source}")
    relative = path[len("/_next/"):]
    if any(part in ("", ".", "..") for part in PurePosixPath(relative).parts) or not relative.startswith("static/"):
        raise ValueError(f"unsafe initial script source: {source}")
    return relative


def _html_name(route):
    if not isinstance(route, str) or not route.startswith("/") or ".." in route.split("/"):
        raise ValueError(f"malformed app route: {route!r}")
    base = route[:-len("/page")] if route.endswith("/page") else None
    if base is None:
        raise ValueError(f"unexpected app route entry: {route!r}")
    return Path("index.html") if base in ("", "/") else Path(base.lstrip("/") + ".html")


def route_gzip_sizes(next_dir):
    """Return route -> gzip bytes, counting each emitted initial asset once."""
    root = Path(next_dir)
    manifest = root / "server" / "app-paths-manifest.json"
    try:
        routes = json.loads(manifest.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot read app route manifest {manifest}: {exc}") from exc
    if not isinstance(routes, dict):
        raise ValueError("app route manifest must be an object")
    pages = [route for route in routes if isinstance(route, str) and route.endswith("/page")]
    if not pages:
        raise ValueError("app route manifest has no /page routes")
    result = {}
    html_root = root / "server" / "app"
    for route in sorted(pages):
        html_file = html_root / _html_name(route)
        try:
            parser = _Scripts()
            parser.feed(html_file.read_text())
        except OSError as exc:
            raise ValueError(f"missing route HTML for {route}: {html_file}") from exc
        assets = set()
        for source in parser.sources:
            rel = _asset_path(source)
            asset = (root / rel).resolve()
            if not asset.is_relative_to(root.resolve()):
                raise ValueError(f"asset escapes build directory: {source}")
            if not asset.is_file():
                raise ValueError(f"missing initial asset for {route}: {source}")
            assets.add(asset)
        if not assets:
            raise ValueError(f"route has no initial modern scripts: {route}")
        result[route] = sum(len(gzip.compress(asset.read_bytes())) for asset in assets)
    return result
