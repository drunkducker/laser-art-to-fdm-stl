# Artwork conversion

Use this reference when the source is a flat image, tracing, SVG, DXF, PDF, or laser-cut layout.

## Source interpretation

Separate visual identity from fabrication artifacts. Preserve approved composition, recognizable silhouettes, negative spaces, and front/back relationships. Remove specks, duplicate contours, accidental self-intersections, ragged trace noise, and tiny gaps that are not intentional design features.

For a raster source, keep an untouched copy and generate a high-contrast working mask. Inspect the mask at full-design scale and at close range. A visually attractive render is not a substitute for clean contours.

## Dimensioned review

Show enough information for the user to judge both appearance and scale:

- overall width and height for every panel;
- intended thickness, labeled separately because it is not visible in a flat silhouette;
- a ruler, dimension arrows, or a compact dimension table;
- part names and front/back labels;
- provisional or inferred dimensions clearly marked as such.

If the design has several trees, letters, figures, or panels, preserve their original layout and approximate relative scale unless the user requests recomposition.

## Printability adjustments

Evaluate narrow features after the final scale is known. Compare them with the planned nozzle, line width, wall count, layer height, material, and load. Prefer local widening, fillets, overlaps, or hidden bridges over uniform thickening that changes the artwork's character.

Attached leaves, branch tips, pumpkin details, lettering counters, and similar small features must survive both polygon cleanup and extrusion. Inspect the final 3D mesh, not only the 2D source.

When a design uses cutout details, render them as true voids in the review preview. After extrusion, verify that each void passes completely through the intended depth.

## Geometry construction

Create clean closed 2D regions, resolve winding and self-intersections, then extrude. Unite intended touching solids and keep intended separate inlays distinct. Use enough curve resolution for smooth silhouettes without producing needlessly huge meshes.

Orient decorative panels on a broad flat face unless their function requires another orientation. Keep the front surface definition clear in filenames and previews.

