# Assembly, fit, and support reduction

Use this reference for oversized parts, split models, slide joints, dovetails, mounting spines, alignment pins, or support-heavy source models.

## Diagnose before redesigning

Inspect the source mesh and, when supplied, the 3MF or G-code. Quantify the issue where possible: model bounds, bed contact, support height, support material, overhang location, part count, and print orientation. Use those measurements to choose a split rather than assuming the visible shape tells the whole story.

## Select the split and assembly order

Design the assembly sequence before finalizing joints. Confirm that each part can physically enter along the intended direction and that later parts do not block earlier motion. Provide an exploded or numbered assembly preview.

Place splits to create broad, stable print faces and reduce supports while protecting important visible contours. A third mounting spine or locking piece may be better than forcing two decorative panels to carry every function.

## Mating geometry

Treat clearance as a named parameter, not an accidental result. A 0.30 mm nominal profile clearance was successful in the referenced Version 4 workflow, but it is an example rather than a universal default. Account for printer calibration, material, joint length, orientation, and whether the joint should slide, snap, or press.

When fit matters, create a short, inexpensive coupon using the actual mating profile. Recommend printing it before the full parts. Adjust the profile or slicer dimensional compensation based on the result; do not scale complete mating parts independently.

Keep joint features centered and fully fused into their parent bodies with controlled overlap. Avoid detached rails, paper-thin walls, trapped cavities, and joint additions that block existing openings.

## Assembly verification

Verify individual parts and the assembled arrangement:

- each printable piece is one connected watertight body unless intentionally multipart;
- mating surfaces have the specified gap;
- interference volume is zero except for explicitly designed press or snap engagement;
- the assembly order is possible along the stated motion axes;
- added joint material does not obstruct original holes or cutouts;
- all parts retain a deliberate print orientation and adequate bed contact.

Record the nominal clearance and any coupon result in the final README.

