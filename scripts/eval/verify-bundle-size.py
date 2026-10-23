#!/usr/bin/env python3
"""Verify initial JS gzip size <= 170 KB for all routes (Check P-3)."""

import glob
import gzip
import json
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
next_dir = os.path.join(base_dir, "frontend", ".next")
manifest_path = os.path.join(next_dir, "build-manifest.json")

if not os.path.exists(manifest_path):
    print(f"Error: {manifest_path} not found. Run 'npm run build' first.")
    sys.exit(1)


def get_gz_size(rel_path):
    full = os.path.join(next_dir, rel_path)
    if not os.path.exists(full):
        return 0
    with open(full, "rb") as f:
        return len(gzip.compress(f.read()))


with open(manifest_path) as f:
    bm = json.load(f)

root_files = bm.get("rootMainFiles", [])
root_gz = sum(get_gz_size(p) for p in root_files)
limit = 170 * 1024

failed = []
page_files = sorted(
    glob.glob(os.path.join(next_dir, "static/chunks/app/**/page-*.js"), recursive=True)
)

if not page_files:
    print("Error: No app page chunks found.")
    sys.exit(1)

for p in page_files:
    rel = os.path.relpath(p, next_dir)
    route_name = os.path.dirname(p).replace(os.path.join(next_dir, "static/chunks/app"), "") or "/"
    total_gz = root_gz + get_gz_size(rel)
    if total_gz > limit:
        failed.append((route_name, total_gz))

if failed:
    for route, sz in failed:
        print(f"FAILED: Route {route} initial JS {sz / 1024:.2f} KB exceeds 170 KB limit")
    sys.exit(1)

print(
    f"PASS: All {len(page_files)} routes have initial JS <= 170 KB gzip "
    f"(max: {root_gz / 1024:.2f} KB root + page chunks)."
)
sys.exit(0)
