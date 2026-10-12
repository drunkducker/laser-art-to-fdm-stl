#!/usr/bin/env python3
"""Report basic manufacturing-relevant facts for STL/OBJ/PLY/3MF meshes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("meshes", nargs="+", type=Path, help="Mesh files to inspect")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    return parser.parse_args()


def inspect(path: Path) -> dict:
    try:
        import trimesh
    except ImportError as exc:
        raise RuntimeError("trimesh is required: python -m pip install trimesh") from exc

    # Processing welds the duplicated per-triangle vertices common in STL files.
    # Without it, connectivity and watertightness results are misleading.
    loaded = trimesh.load(path, force="scene", process=True)
    geometries = [g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)]
    if not geometries:
        raise ValueError("no triangle mesh geometry found")

    merged = trimesh.util.concatenate(geometries)
    merged.merge_vertices()
    bounds = merged.bounds
    extents = merged.extents
    components = merged.split(only_watertight=False)
    return {
        "file": str(path),
        "geometry_count": len(geometries),
        "connected_components": len(components),
        "vertices": int(len(merged.vertices)),
        "faces": int(len(merged.faces)),
        "watertight": bool(merged.is_watertight),
        "winding_consistent": bool(merged.is_winding_consistent),
        "bounds_mm": {
            "min": [round(float(v), 4) for v in bounds[0]],
            "max": [round(float(v), 4) for v in bounds[1]],
        },
        "size_mm": {
            "x": round(float(extents[0]), 4),
            "y": round(float(extents[1]), 4),
            "z": round(float(extents[2]), 4),
        },
        "minimum_z_mm": round(float(bounds[0][2]), 4),
        "volume_mm3": round(float(abs(merged.volume)), 4) if merged.is_volume else None,
    }


def main() -> int:
    args = parse_args()
    results = []
    failed = False
    for path in args.meshes:
        try:
            results.append(inspect(path))
        except Exception as exc:  # keep a batch report useful when one file fails
            failed = True
            results.append({"file": str(path), "error": str(exc)})

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(result["file"])
            if "error" in result:
                print(f"  ERROR: {result['error']}")
                continue
            size = result["size_mm"]
            print(f"  size mm: {size['x']} x {size['y']} x {size['z']}")
            print(f"  components: {result['connected_components']}")
            print(f"  watertight: {result['watertight']}")
            print(f"  winding consistent: {result['winding_consistent']}")
            print(f"  minimum Z mm: {result['minimum_z_mm']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

