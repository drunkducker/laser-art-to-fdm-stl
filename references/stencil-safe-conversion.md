# Stencil-safe negative-space conversion

Use this reference when artwork contains cutouts, counters, pierced details, or positive islands that would become detached material after cutting or extrusion.

## Meaning of stencil-safe

Treat the retained material as the positive mask. A stencil is topology-safe when every positive region that must remain part of the finished piece is connected to the intended main body. Negative openings should remain open and recognizable. A bridge adds retained material across a negative opening; it must not be confused with closing or filling the entire opening.

Examples include the center of an A or O cut from a plate, pupils or facial details surrounded by cutouts, pumpkin segment islands, and decorative shapes floating inside a larger pierced region.

## Review gate

Do not silently add automatic bridges to approved artwork. Use this sequence:

1. Normalize the artwork into a black material mask on a white or transparent background.
2. Detect connected positive components and select the intended main body.
3. Distinguish meaningful islands from trace noise by area and visual inspection.
4. Propose the shortest reasonable bridge for each meaningful island.
5. Render an annotated preview showing islands and proposed bridges in contrasting colors, with bridge width and overall dimensions.
6. Let the user approve, move, disable, or add bridges.
7. Apply only approved bridges, then repeat connectivity and opening checks.

`scripts/stencil_safe.py analyze` creates a JSON bridge plan and review images. The plan is editable: set a proposal's `approved` field to `true`, change its endpoints, or disable it. `scripts/stencil_safe.py apply` refuses to apply unapproved proposals unless `--approve-all` is explicitly supplied.

## Bridge placement

Shortest-path placement is a starting point, not an aesthetic decision. Prefer locations that:

- follow existing ribs, folds, stems, shadows, or vertical pumpkin grooves;
- avoid eyes, mouth corners, lettering strokes, and other identity-defining details;
- are distributed symmetrically when symmetry matters;
- do not create a fragile notch beside the bridge;
- remain wide enough after slicing and material shrinkage.

Use multiple bridges when an island is large, flexible, load-bearing, or likely to rotate. A single bridge may be adequate for a small decorative island. Set width from the physical process and final scale; do not assume a universal value.

## Raster-assisted topology analysis

The helper rasterizes SVG input for connectivity analysis and retraces the approved mask to vector paths. Use a high analysis resolution for curved or detailed artwork. Inspect the retraced SVG against the original because raster-assisted conversion can move edges slightly. For precision-critical CAD, use the JSON bridge coordinates to recreate the bridges in the original vector or CAD source instead of accepting the retrace.

## Final checks

- Positive component count matches the intended printable-body count.
- Every approved bridge visibly reaches material at both ends.
- Required holes and expression-defining cutouts remain open.
- Bridge widths satisfy the chosen process at final scale.
- No dust components or accidental slivers remain.
- The bridged SVG and extruded mesh render consistently.

