# Laser Art to FDM STL

A Codex skill for adapting laser-cut artwork, silhouettes, layered signs, and other flat designs into dimensioned, reviewable, FDM-printable models.

The workflow emphasizes:

- dimensioned approval previews before final geometry when requested;
- preservation of recognizable artwork and original openings;
- review-first stencil bridging for disconnected positive islands;
- FDM-safe feature thickness, connectivity, orientation, and bed contact;
- support-reducing splits, parameterized joints, and fit coupons;
- watertightness, connected-body, build-plane, fit, and interference checks;
- clearly versioned STL/3MF packages with print and assembly instructions.

## Install

Install the repository as a Codex skill from:

`https://github.com/drunkducker/laser-art-to-fdm-stl`

The required skill entrypoint is `SKILL.md`. `scripts/stencil_safe.py` analyzes stencil topology, proposes bridges, and exports approved bridged SVG geometry. `scripts/inspect_mesh.py` provides repeatable mesh inspection.

## Example request

> Use $laser-art-to-fdm-stl to adapt this two-panel laser-cut autumn scene for FDM printing. First show dimensioned front and back silhouettes for approval. Preserve the layout and pumpkin cutouts, strengthen the trees, and do not create STL files until I approve the previews.

## Scope

This skill guides design and verification. It does not replace slicer inspection or a physical test print, and it does not claim a model has been print-tested unless that testing actually occurred.

