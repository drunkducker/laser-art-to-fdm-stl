#!/usr/bin/env python3
"""Analyze and bridge disconnected positive islands in stencil artwork.

The script uses a raster mask for topology analysis. It supports SVG and common
raster inputs, writes an editable JSON bridge plan, and can retrace the approved
mask as a path-only SVG.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass
class Canvas:
    image: Image.Image
    view_box: tuple[float, float, float, float]
    width_attr: str
    height_attr: str
    source_kind: str

    @property
    def sx(self) -> float:
        return self.view_box[2] / self.image.width

    @property
    def sy(self) -> float:
        return self.view_box[3] / self.image.height


def positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("input", type=Path)
    common.add_argument("--max-pixels", type=int, default=2400,
                        help="longest rasterized side; default 2400")
    common.add_argument("--foreground", choices=("auto", "dark", "light", "alpha"),
                        default="auto", help="how retained material is identified")
    common.add_argument("--threshold", type=int, default=128,
                        help="0-255 lightness/alpha threshold; default 128")

    analyze = sub.add_parser("analyze", parents=[common],
                             help="create an editable bridge plan and review preview")
    analyze.add_argument("--output-dir", type=Path, required=True)
    analyze.add_argument("--bridge-width", type=positive_float, default=2.0,
                         help="bridge width in SVG viewBox units or raster pixels")
    analyze.add_argument("--min-island-area", type=positive_float, default=4.0,
                         help="smallest proposed island area in source units squared")

    apply = sub.add_parser("apply", parents=[common],
                           help="apply approved bridges from an analysis plan")
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--output-dir", type=Path, required=True)
    apply.add_argument("--approve-all", action="store_true",
                       help="explicitly accept every proposed bridge")
    apply.add_argument("--simplify", type=float, default=0.65,
                       help="contour simplification in raster pixels; default 0.65")
    return parser


def parse_svg_length(text: str | None, fallback: float) -> tuple[float, str]:
    if not text:
        return fallback, f"{fallback:g}"
    stripped = text.strip()
    number = ""
    for char in stripped:
        if char in "+-.0123456789eE":
            number += char
        else:
            break
    try:
        return float(number), stripped
    except ValueError:
        return fallback, f"{fallback:g}"


def load_canvas(path: Path, max_pixels: int) -> Canvas:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".svg":
        root = ET.fromstring(path.read_bytes())
        view_text = root.attrib.get("viewBox") or root.attrib.get("viewbox")
        if view_text:
            values = [float(v) for v in view_text.replace(",", " ").split()]
            if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
                raise ValueError("SVG viewBox must contain four values with positive size")
            view_box = tuple(values)
        else:
            width_num, _ = parse_svg_length(root.attrib.get("width"), 1000.0)
            height_num, _ = parse_svg_length(root.attrib.get("height"), 1000.0)
            view_box = (0.0, 0.0, width_num, height_num)
        _, width_attr = parse_svg_length(root.attrib.get("width"), view_box[2])
        _, height_attr = parse_svg_length(root.attrib.get("height"), view_box[3])
        scale = max_pixels / max(view_box[2], view_box[3])
        out_w = max(1, round(view_box[2] * scale))
        out_h = max(1, round(view_box[3] * scale))
        try:
            import cairosvg
        except ImportError as exc:
            raise RuntimeError("SVG input requires cairosvg: pip install cairosvg") from exc
        png = cairosvg.svg2png(bytestring=path.read_bytes(), output_width=out_w,
                               output_height=out_h)
        from io import BytesIO
        image = Image.open(BytesIO(png)).convert("RGBA")
        return Canvas(image, view_box, width_attr, height_attr, "svg")

    image = Image.open(path).convert("RGBA")
    if max(image.size) > max_pixels:
        scale = max_pixels / max(image.size)
        image = image.resize((max(1, round(image.width * scale)),
                              max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
    view_box = (0.0, 0.0, float(image.width), float(image.height))
    return Canvas(image, view_box, str(image.width), str(image.height), "raster")


def material_mask(image: Image.Image, mode: str, threshold: int) -> tuple[np.ndarray, str]:
    rgba = np.asarray(image, dtype=np.uint8)
    rgb = rgba[:, :, :3].astype(np.float32)
    alpha = rgba[:, :, 3]
    luminance = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] +
                 0.0722 * rgb[:, :, 2])
    selected = mode
    if mode == "auto":
        transparent_fraction = float(np.mean(alpha < 245))
        if transparent_fraction > 0.01:
            selected = "alpha"
        else:
            border = np.concatenate((luminance[0], luminance[-1], luminance[:, 0],
                                     luminance[:, -1]))
            selected = "dark" if float(np.median(border)) >= 128 else "light"
    if selected == "alpha":
        mask = alpha >= threshold
    elif selected == "dark":
        mask = (luminance < threshold) & (alpha > 0)
    else:
        mask = (luminance >= threshold) & (alpha > 0)
    return mask.astype(np.uint8), selected


def source_point(canvas: Canvas, point: tuple[int, int]) -> list[float]:
    x, y = point
    vx, vy, _, _ = canvas.view_box
    return [round(vx + x * canvas.sx, 4), round(vy + y * canvas.sy, 4)]


def pixel_point(canvas: Canvas, point: list[float]) -> tuple[int, int]:
    vx, vy, _, _ = canvas.view_box
    x = round((point[0] - vx) / canvas.sx)
    y = round((point[1] - vy) / canvas.sy)
    return (int(np.clip(x, 0, canvas.image.width - 1)),
            int(np.clip(y, 0, canvas.image.height - 1)))


def connected(mask: np.ndarray) -> tuple[int, np.ndarray, np.ndarray, np.ndarray]:
    return cv2.connectedComponentsWithStats(mask, 8, cv2.CV_32S)


def nearest_bridge(current: np.ndarray, island: np.ndarray) -> tuple[tuple[int, int], tuple[int, int]]:
    distance = cv2.distanceTransform((1 - current).astype(np.uint8), cv2.DIST_L2, 5)
    ys, xs = np.nonzero(island)
    if len(xs) == 0:
        raise ValueError("empty island")
    index = int(np.argmin(distance[ys, xs]))
    island_xy = (int(xs[index]), int(ys[index]))
    main_y, main_x = np.nonzero(current)
    squared = ((main_x.astype(np.int64) - island_xy[0]) ** 2 +
               (main_y.astype(np.int64) - island_xy[1]) ** 2)
    nearest = int(np.argmin(squared))
    main_xy = (int(main_x[nearest]), int(main_y[nearest]))
    return island_xy, main_xy


def render_review(canvas: Canvas, mask: np.ndarray, islands: list[np.ndarray],
                  bridges: list[dict], output: Path) -> None:
    base = np.full((*mask.shape, 3), 250, dtype=np.uint8)
    base[mask > 0] = (35, 38, 42)
    overlay = Image.fromarray(base, "RGB")
    draw = ImageDraw.Draw(overlay)
    for island in islands:
        ys, xs = np.nonzero(island)
        if len(xs):
            draw.rectangle((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
                           outline=(235, 166, 35), width=2)
    for bridge in bridges:
        a = tuple(bridge["from_px"])
        b = tuple(bridge["to_px"])
        width = max(2, int(round(bridge["width_px"])))
        draw.line((a, b), fill=(220, 45, 55), width=width)
        draw.ellipse((a[0] - 3, a[1] - 3, a[0] + 3, a[1] + 3), fill=(255, 211, 60))
    legend_h = 66
    sheet = Image.new("RGB", (overlay.width, overlay.height + legend_h), "white")
    sheet.paste(overlay, (0, legend_h))
    size_label = f"{canvas.view_box[2]:g} x {canvas.view_box[3]:g} source units"
    label = (f"Stencil topology review | {size_label} | yellow: disconnected material | "
             f"red: proposed {bridges[0]['width_source'] if bridges else 0:g}-unit bridges")
    ImageDraw.Draw(sheet).text((12, 18), label, fill=(20, 20, 20),
                               font=ImageFont.load_default())
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def analyze(args: argparse.Namespace) -> int:
    canvas = load_canvas(args.input, args.max_pixels)
    mask, selected = material_mask(canvas.image, args.foreground, args.threshold)
    count, labels, stats, _ = connected(mask)
    components = list(range(1, count))
    if not components:
        raise ValueError("no retained material detected")
    base_label = max(components, key=lambda label: int(stats[label, cv2.CC_STAT_AREA]))
    current = (labels == base_label).astype(np.uint8)
    area_scale = canvas.sx * canvas.sy
    bridge_px = max(1.0, args.bridge_width / ((canvas.sx + canvas.sy) / 2.0))
    islands: list[np.ndarray] = []
    bridges: list[dict] = []
    ordered = sorted((label for label in components if label != base_label),
                     key=lambda label: int(stats[label, cv2.CC_STAT_AREA]), reverse=True)
    ignored = []
    for label in ordered:
        island = (labels == label).astype(np.uint8)
        area_source = float(stats[label, cv2.CC_STAT_AREA]) * area_scale
        if area_source < args.min_island_area:
            ignored.append({"component": label, "area_source": round(area_source, 4)})
            continue
        start, end = nearest_bridge(current, island)
        bridge = {
            "id": len(bridges) + 1,
            "component": label,
            "area_source": round(area_source, 4),
            "from_px": list(start),
            "to_px": list(end),
            "from_source": source_point(canvas, start),
            "to_source": source_point(canvas, end),
            "width_px": round(bridge_px, 4),
            "width_source": args.bridge_width,
            "approved": False,
        }
        bridges.append(bridge)
        islands.append(island)
        cv2.line(current, start, end, 1, max(1, round(bridge_px)), cv2.LINE_8)
        current[island > 0] = 1

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask * 255, "L").save(output / "material-mask.png")
    render_review(canvas, mask, islands, bridges, output / "bridge-review.png")
    plan = {
        "schema": 1,
        "source": str(args.input.resolve()),
        "source_kind": canvas.source_kind,
        "raster_size": [canvas.image.width, canvas.image.height],
        "view_box": list(canvas.view_box),
        "width_attr": canvas.width_attr,
        "height_attr": canvas.height_attr,
        "foreground_requested": args.foreground,
        "foreground_selected": selected,
        "threshold": args.threshold,
        "positive_components_before": count - 1,
        "main_component": base_label,
        "proposals": bridges,
        "ignored_small_components": ignored,
        "warning": "Review bridge locations visually before approval. Raster-assisted retracing can move edges slightly.",
    }
    (output / "bridge-plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(json.dumps({
        "positive_components": count - 1,
        "bridge_proposals": len(bridges),
        "ignored_small_components": len(ignored),
        "plan": str(output / "bridge-plan.json"),
        "preview": str(output / "bridge-review.png"),
    }, indent=2))
    return 0


def mask_to_svg(mask: np.ndarray, canvas: Canvas, simplify: float, output: Path) -> None:
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    commands = []
    vx, vy, _, _ = canvas.view_box
    for contour in contours:
        approx = cv2.approxPolyDP(contour, simplify, True)
        if len(approx) < 3:
            continue
        points = approx[:, 0, :]
        coords = [(vx + float(x) * canvas.sx, vy + float(y) * canvas.sy)
                  for x, y in points]
        commands.append("M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in coords) + " Z")
    view = " ".join(f"{value:g}" for value in canvas.view_box)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas.width_attr}" '
           f'height="{canvas.height_attr}" viewBox="{view}">\n'
           f'  <path d="{" ".join(commands)}" fill="#000000" fill-rule="evenodd"/>\n'
           f'</svg>\n')
    output.write_text(svg, encoding="utf-8")


def apply_plan(args: argparse.Namespace) -> int:
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    canvas = load_canvas(args.input, args.max_pixels)
    expected = plan.get("raster_size")
    if expected != [canvas.image.width, canvas.image.height]:
        raise ValueError("plan raster size differs from current input; reuse the same --max-pixels")
    mask, selected = material_mask(canvas.image, args.foreground, args.threshold)
    accepted = []
    for proposal in plan.get("proposals", []):
        if not (args.approve_all or proposal.get("approved") is True):
            continue
        start = pixel_point(canvas, proposal["from_source"])
        end = pixel_point(canvas, proposal["to_source"])
        width_source = positive_float(str(proposal["width_source"]))
        width_px = max(1, round(width_source / ((canvas.sx + canvas.sy) / 2.0)))
        cv2.line(mask, start, end, 1, width_px, cv2.LINE_8)
        accepted.append({**proposal, "from_px_applied": list(start), "to_px_applied": list(end)})
    if plan.get("proposals") and not accepted:
        raise ValueError("no bridges are approved; edit the plan or pass --approve-all explicitly")
    count, _, stats, _ = connected(mask)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask * 255, "L").save(output / "stencilized-mask.png")
    mask_to_svg(mask, canvas, args.simplify, output / "stencilized.svg")
    report = {
        "source": str(args.input.resolve()),
        "foreground_selected": selected,
        "bridges_applied": len(accepted),
        "positive_components_after": count - 1,
        "component_areas_px": [int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, count)],
        "output_svg": str(output / "stencilized.svg"),
    }
    (output / "application-report.json").write_text(json.dumps(report, indent=2),
                                                     encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        return analyze(args) if args.command == "analyze" else apply_plan(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

