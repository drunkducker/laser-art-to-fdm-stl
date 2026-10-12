# Verification and packaging

Use this checklist before calling a version final.

## Geometry report

For every printable part, record:

- filename and purpose;
- width, depth, and height in millimeters;
- connected-body count;
- watertight/manifold result;
- minimum Z and intended bed face;
- any known minimum feature or wall requirement.

For assemblies, also record nominal joint clearance, interference result, assembly direction, and preserved-opening checks.

## Visual checks

Render the actual exported files from at least the views needed to catch likely errors. Inspect full-size previews rather than trusting thumbnails. Useful views include front, back, top, side, isometric, exploded assembly, joint close-up, and silhouette-only views.

Compare final renders with the last approved review image. If the geometry changed after approval, show the updated preview before representing it as approved.

## Package layout

Prefer a simple package:

```text
project-name-vN/
|-- README.txt
|-- previews/
|-- stl/
`-- 3mf/
```

Avoid including temporary scripts, caches, intermediate meshes, or superseded versions in the print package. If earlier versions must remain, place them under a clearly labeled design-history folder and state that they should not be printed.

## README contents

Include:

1. approved version and design purpose;
2. inventory of print files;
3. finished dimensions and units;
4. print orientation and support guidance;
5. assembly order;
6. joint clearance and fit-coupon advice when applicable;
7. validation results;
8. concise design history explaining material changes between versions.

Do not claim slicer compatibility or print success that was not actually tested. Distinguish mesh validation, slicer inspection, and physical test printing.

