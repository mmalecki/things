# Two-piece Picatinny riser

[`picatinny_riser.py`](picatinny_riser.py) builds a female lower clamp, a
wide-root tapered bridge neck, and a male upper rail as **two longitudinal
halves**. The pieces differ only at the fastener seats: socket-head counterbores
on the left, captive hex-nut pockets on the right. Fastener cutters and dimensions
come from the repository's pinned `bd-buildabolt` dependency; there is no second
fastener table.

## Build

From `build123d/`:

```sh
uv sync --locked
uv run python picatinny_riser.py

# Explicit defaults:
uv run python picatinny_riser.py --bottom-slots 5 --top-slots 7 \
  --bolt-slots 1 5 --bolt M3 --nut M3 --height 20

# Shorter, shifted top; three M4 fasteners:
uv run python picatinny_riser.py --bottom-slots 5 --top-slots 3 \
  --bolt-slots 1 3 5 --bolt M4 --height 22 --top-offset 5 \
  --output-dir /tmp/picatinny-riser-m4

# Print exports with a support wall under each lower jaw lip:
uv run python picatinny_riser.py --support --support-wall 1.2 --support-gap 0.2

# The same walls with a 5 mm brim on the bed (--support-brim implies --support):
uv run python picatinny_riser.py --support-brim --support-wall 1.2
```

Exports (ignored by Git, following this repository's artifact policy):

| File | Coordinates / purpose |
| --- | --- |
| `picatinny_riser.step` | Two labeled solids in their assembled positions |
| `picatinny_riser_left.step`, `.stl` | Socket half, split face down on Z=0; with `--support`, plus its support wall |
| `picatinny_riser_right.step`, `.stl` | Nut half, split face down on Z=0; with `--support`, plus its support wall |

Both printable files start at X=Y=Z=0 and must be arranged separately on the
slicer bed; they are **not** an already-spaced print plate. By default outputs
go beside the script, independent of the current directory. `--output-dir`
selects a different destination; reusing one overwrites that configuration.
No viewer is required; `--show` optionally sends the assembly to OCP Viewer.
`--help` lists the CLI options.

## Python API and parameters

Importing the module does not create geometry, write files, or contact a viewer.

```python
from bd_buildabolt import bolt_data, nut_data
from picatinny_riser import PrintSupport, make_riser, export_riser

riser = make_riser(
    bottom_slot_count=6,
    top_slot_count=4,
    bolt_slots=[1, 3, 6],
    bolt=bolt_data("M3", kind="socket_head"),
    nut=nut_data("M3", kind="hexagon_thin"),
    riser_height=18,
    top_offset=-5,
    bolt_fit=0.2,
)
left, right = riser.left, riser.right        # assembly coordinates
print_left, print_right = riser.print_parts()
supported_left, supported_right = riser.print_parts(PrintSupport(wall=1.2, gap=0.2, brim=5))
assembly = riser.assembly()
export_riser(riser, "/tmp/picatinny-riser-custom")
export_riser(riser, "/tmp/picatinny-riser-supported", support=PrintSupport())
```

All lengths are **millimetres**. Y follows the barrel/rail axis, X is transverse,
and Z is up. The lower host rail's top face is **Z=0**. `riser_height` is the
**top-face-to-top-face rise**, not the overall part bounding-box height.

| Factory parameter | Default | Meaning |
| --- | --- | --- |
| `bottom_slot_count` | `5` | Number of host-rail slot positions spanned by the lower clamp |
| `top_slot_count` | `7` | Number of actual transverse slots cut into the upper rail |
| `bolt_slots` | `None` | Iterable of **1-based** lower slot numbers; `None` selects first and last, only once for a one-slot clamp |
| `bolt` | `"M3"` | Socket-head size string or headed `bd_buildabolt.BoltData` |
| `nut` | `"M3"` | Hex nut size string or `bd_buildabolt.NutData` |
| `riser_height` | `20.0` | Upper rail top Z; must clear the fasteners, bridge, and upper mounting interface |
| `top_offset` | `0.0` | Upper pattern center shift along Y; lower center remains Y=0 |
| `bolt_fit` | `0.2` | Added shaft/head **diameter**, nut **across-flats width**, and head/nut pocket depth |
| `split_gap` | `0.4` | Material removed between X=-gap/2 and X=+gap/2 |
| `roof_clearance` | `0.2` | Relief above the lower rail top and clearance below the bolt bore at the host slot floor |
| `min_wall` | `2.0` | Minimum designed pocket backing/unchamfered floor, end land, bridge thickness, and adjacent-pocket ligament |
| `bottom_chamfer` | `1.0` | Equal-leg 45° chamfer on the two outer bottom edges along Y; `0` disables it; maximum `min_wall/2` |

Slot 1 is at the negative-Y end. Slot center `i` is
`(i - (count + 1)/2) * 10.0076`, plus `top_offset` for the top pattern. Top and
bottom patterns have independent datums, so odd/even counts and offsets do not
move the lower bolt axes. A half-pitch normally bounds each end; the lower end
lands grow when necessary to leave material around larger fastener pockets.
The default bottom length is about 50.612 mm and the top length is 70.0532 mm.
The bottom slot count describes its **footprint on the host rail**, not a second
set of male slots underneath the riser. Only requested bolt positions are drilled.

There is no fixed bolt-count limit: one, sparse, adjacent, and all-slot patterns
are supported where their head/nut pockets leave enough material. An empty
iterable (CLI: `--bolt-slots` with no values) creates an **unfastened mockup**.
Duplicates, invalid indices, nonfinite/nonpositive dimensions, mismatched size
strings, oversize shafts, crowded pockets, insufficient rise, and nonoverlapping
upper/lower footprints are rejected. With default hardware the minimum rise is
approximately 14.975 mm. The CLI defaults the nut to the selected bolt size; the
Python API has independent `bolt`/`nut` defaults, so pass both when changing size.
Custom data has no thread designation: matching thread diameter/pitch remains the
caller's responsibility. A headless `BoltData` is not accepted for a counterbore.

## Bridge neck

The bridge flares across X to the **full lower clamp width at its root**, then
narrows linearly to the upper rail's **15.6718 mm neck width**. This removes the
old narrow web's sharp, re-entrant shoulder on the clamp roof. The root width
follows the selected fasteners and wall thickness automatically; no extra
parameter is required. With default parameters it tapers from **31.609 mm** at
Z=3.6528 to **15.6718 mm** at Z=10.6782.

The taper ends 9.3218 mm below the upper rail top, keeping the upper mounting
clearance and rail profile unchanged. Its Y length and center interpolate
between the lower and upper footprints, including unequal slot counts and
`top_offset`. The 0.4 mm split and both fastener patterns are unchanged. The
wider root is intended to distribute load over more of the clamp; stress
reduction has not been quantified by analysis or physical testing.

## Outer bottom chamfers

Both outside fastener faces have a **1 mm × 45° bottom chamfer** running their
full length along Y. Only the two outside lower edges are beveled; no end
chamfers are added. Inner rail-contact lips, split faces and fastener seats stay
unchanged.
Use `bottom_chamfer=0.5` in Python or `--bottom-chamfer 0.5` on the CLI for a
smaller bevel; `0` restores the sharp edges.

The chamfer is limited to `min_wall/2`, retaining at least half the unchamfered
pocket-floor thickness locally at the outside lip (**1 mm** with the defaults).
Larger values are rejected rather than silently reduced; if decreasing
`min_wall`, also decrease `bottom_chamfer`. The remaining unchamfered floor and
all overall dimensions are unchanged.

## Print support

Split face down, each lower jaw lip prints as an island hanging about 7.7 mm
above the bed. Its lowest edge is the narrow neck land (0.22 mm with the
defaults, a knife edge when the jaw ends at the neck) followed by the 45° lower
flank. Slicers generally treat a region that thin as needing no support, so the
lip's first layers print into air. `--support` (Python: `PrintSupport`) adds
a detached, rectangular wall beneath each lip to the split-face-down STEP/STL
exports only; the assembly STEP and the fitted halves are unchanged.

| `PrintSupport` field | CLI option | Default | Meaning |
| --- | --- | --- | --- |
| `wall` | `--support-wall` | `1.0` | Wall thickness across the lip, centered under its lowest edge |
| `gap` | `--support-gap` | `0.2` | Empty separation between the wall top and the lip's lowest edge |
| `brim` | `--support-brim [MM]` | `0` (CLI flag alone: `5`) | Width of a rectangular brim around the wall on the bed; `0` disables it |
| `brim_height` | `--support-brim-height` | `0.2` | Brim thickness; must stay below the wall top |

The wall stands on the bed and runs the full saddle length, centered under the
middle of the neck land (or the knife edge). A wall wider than the land
therefore overhangs it equally: past the clamp bottom face on one side, under
the 45° flank on the other. Its top is flat, one gap below the lip's lowest
edge. A top following the 45° flank would sit only one gap away sideways in the
layers the flank prints in, and slicers fuse perimeters that close. Set `gap` to
your layer height for a single empty separation layer, then confirm that layer
in the slicer preview: the lip edge need not fall on a layer boundary. `wall`
must be positive and keep the wall's rail side under the lower jaw (at most
5.7551 mm with default hardware); `gap` must be positive and leave the wall
some height. Both files then contain two bodies:
keep them as one object on the bed and don't let the slicer generate support
there as well. Snap the wall off after printing.

A tall, 1 mm wall standing alone on the bed can peel or tip, so `brim` adds a
flat rectangle around its base, part of the same support body. It extends the
full width outward and past both saddle ends. On the rail side the half itself
meets the bed, so the brim stops `SUPPORT_BRIM_CLEARANCE` (1 mm) short of it so
slicers don't merge the two. With default hardware and wall that allows up to
4.6383 mm there; wider brims are clipped on that side only. Since a wall wider
than the land or a brim reaches past the half, each half and its support are
moved together so the file still starts at X=Y=Z=0. `--support-brim` on its own
enables the support with a 5 mm brim.

## Rail profile and fit

The existing `picatinny-sling-point.py` informed the clamp and fastener workflow.
This model uses the nominal drawing's 45-degree flanks **and short vertical
outer lands**, rather than the sling model's simplified diamond:

- Outside width: 0.835 in = **21.209 mm**.
- Neck width: 0.617 in = **15.6718 mm**.
- Opposing contact datum width: 0.748 in; vertical contact spacing: 0.108 in.
- Lower contact depth below top: 0.164 in; upper depth: 0.056 in.
- Upper rail mounting clearance to the wide lower body: at least 0.367 in.
- Slots: **5.2324 mm wide**, **10.0076 mm pitch**, **2.9972 mm deep**.

Sources:

- [MIL-STD-1913 drawing, Figures 1 and 2](https://imlive.s3.amazonaws.com/Federal%20Government/ID290146323786724032196446312686336282340/Attachment_D_-_MIL_STD_1913.pdf)
- [Cross-section drawing reproduction](https://commons.wikimedia.org/wiki/File:M1913A_Rail_CrossSection.svg)
- [Contact datum interpretation](https://www.thomasmechanicaldesign.com/the-mitch-blog/picatinny-and-nato-rails-gdt)
- [Slot dimensions](https://en.wikipedia.org/wiki/Picatinny_rail#Design_and_construction)

These are **nominal modeling dimensions**, not a claim of standard certification.
Standard rail edge breaks, manufacturing tolerances and full GD&T are not
reproduced. The female dovetail is not deliberately enlarged laterally; its split gap provides
clamping travel without starting with an oversize interface. Tightening moves
both halves, so it also changes the upper rail width. Verify the fit on both the
actual host rail and the accessory; a large clamp correction is not acceptable
merely because the bolts can close the gap. The model does not simulate elastic
deflection or tolerance stacks.

## Hardware, printing and assembly

Default hardware: **two M3 socket-head screws and two M3 hex nuts**. The default
model's calculated minimum under-head length for full nut engagement is
**28.209 mm**; **M3×30** is the next common nominal length. Check actual nut
thickness, thread engagement and screw protrusion after clamping. Nuts enter
from the outside, so no printed internal threads or inserts are required. The
assembly STEP contains the two printed pieces, not cosmetic hardware models.

The split-face-down exports keep the fastener axes vertical for printing and
put the large flat split faces on the bed. The lower jaw lip then overhangs;
export with `--support` (see [Print support](#print-support)) or support it
in your slicer. Compensate for
printer calibration/elephant's foot rather than assuming a universal material,
shrink factor, support setting, or torque. This is an **unload-tested prototype**:
physical fit, creep, clamp force, retention under vibration/recoil, and strength
have not been validated. Do not treat a successful geometry test as a load rating.

## Checks

```sh
uv run python -m unittest discover -s tests -p 'test_picatinny_riser.py' -v
uv run python -m unittest discover -s tests -v
```

The riser checks cover valid positive-volume single-solid halves, the 0.4 mm
separation, nominal host-rail fit, the selected transverse bore axes and unselected
solid positions, socket/nut recess dimensions, slot pitch/width/depth, height,
unequal/even/odd counts, offsets of both signs, zero/one/many fasteners, M4 and
custom hardware, invalid inputs, headless CLI execution, and STEP round trips.
Bridge sections verify the full-width root, linear narrowing, independently
interpolated Y ends, absence of the old roof ledge, and unchanged upper neck
clearance, including checks on the reimported assembly STEP. Chamfer checks
measure the two 45° faces, equal legs, full Y length, removed triangular-prism
volumes and remaining pocket lip thickness, including CLI and STEP round trips.
Print-orientation checks compare the actual split-face area with the face on
Z=0. Support checks confirm the halves land as without support (shifted only to
keep each file at the origin) and measure each wall's volume, bed contact,
saddle length, and exact gap to the lip, which it sits directly beneath. They
find the lip's lowest edges independently and check the wall is centered on
them, for both a land and a knife-edge lip. Brim checks measure its footprint
on every side, its exact 1 mm clearance to the half where clipped, and its
thickness through the volume. They cover CLI and STEP round trips and rejected
values. Geometric comparisons use 1e-6 mm and 1e-5 mm³ tolerances. These are
numerical check thresholds, not achievable manufacturing tolerances.
