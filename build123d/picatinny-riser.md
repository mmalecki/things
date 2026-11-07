# Two-piece Picatinny riser

[`picatinny_riser.py`](picatinny_riser.py) builds a female lower clamp, a tapered
bridge, and a male upper rail as **two longitudinal halves**. The pieces differ
only at the fastener seats: socket-head counterbores on the left, captive
hex-nut pockets on the right. Fastener cutters and dimensions come from the
repository's pinned `bd-buildabolt` dependency; there is no second fastener table.

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
```

Exports (ignored by Git, following this repository's artifact policy):

| File | Coordinates / purpose |
| --- | --- |
| `picatinny_riser.step` | Two labeled solids in their assembled positions |
| `picatinny_riser_left.step`, `.stl` | Socket half, split face down on Z=0 |
| `picatinny_riser_right.step`, `.stl` | Nut half, split face down on Z=0 |

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
from picatinny_riser import make_riser, export_riser

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
assembly = riser.assembly()
export_riser(riser, "/tmp/picatinny-riser-custom")
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
| `min_wall` | `2.0` | Minimum designed pocket backing/floor, end land, bridge thickness, and adjacent-pocket ligament |

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
Edge breaks, manufacturing tolerances and full GD&T are not reproduced. The
female dovetail is not deliberately enlarged laterally; its split gap provides
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
put the large flat split faces on the bed. Inspect the lower-clamp overhang in
your slicer and add support where required by your process. Compensate for
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
Print-orientation checks compare the actual split-face area with the face on
Z=0. Geometric comparisons use 1e-6 mm and 1e-5 mm³ tolerances. These are numerical
check thresholds, not achievable manufacturing tolerances.
