"""Parametric, longitudinally split Picatinny accessory riser (millimetres).

Y is the rail/barrel axis, X is transverse, Z is up. The host rail top is
Z=0; the new rail top is Z=riser_height. See picatinny-riser.md for datums,
fit assumptions and examples. Importing this module does not build or export.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import math
from pathlib import Path
from typing import Iterable

import build123d as bd
from bd_buildabolt import (
    BoltSpec, NutSpec, CounterBoreBoltHole, NutcatchParallel, bolt_data, nut_data,
)

# MIL-STD-1913 nominal drawing dimensions, converted from inches once.
INCH = 25.4
SLOT_PITCH = 0.394 * INCH
SLOT_WIDTH = 0.206 * INCH
SLOT_DEPTH = 0.118 * INCH
RAIL_WIDTH = 0.835 * INCH
NECK_WIDTH = 0.617 * INCH
CONTACT_WIDTH = 0.748 * INCH
CONTACT_SPACING = 0.108 * INCH
LOWER_CONTACT_DEPTH = 0.164 * INCH
RAIL_BASE_DEPTH = 0.367 * INCH
UPPER_CONTACT_DEPTH = LOWER_CONTACT_DEPTH - CONTACT_SPACING
TOP_WIDTH = CONTACT_WIDTH - 2 * UPPER_CONTACT_DEPTH
UPPER_CORNER_DEPTH = UPPER_CONTACT_DEPTH + (RAIL_WIDTH - CONTACT_WIDTH) / 2
LOWER_CORNER_DEPTH = LOWER_CONTACT_DEPTH - (RAIL_WIDTH - CONTACT_WIDTH) / 2
NECK_DEPTH = LOWER_CONTACT_DEPTH + (CONTACT_WIDTH - NECK_WIDTH) / 2


# Bed spacing between a support brim and its half, so slicers don't merge them.
SUPPORT_BRIM_CLEARANCE = 1.0


@dataclass(frozen=True)
class PrintSupport:
    """Detached wall under each lower jaw lip of the split-face-down halves.

    The lip starts as a sub-millimetre island in that orientation, which
    slicers don't support. wall is the thickness from the clamp bottom face
    toward the rail; gap is the empty separation under the lip, normally one
    layer height. brim > 0 adds a brim_height thick rectangle that wide around
    the wall on the bed; on the rail side it stops SUPPORT_BRIM_CLEARANCE short
    of the half.
    """

    wall: float = 1.0
    gap: float = 0.2
    brim: float = 0.0
    brim_height: float = 0.2


@dataclass(frozen=True)
class Riser:
    """Printable halves in assembly coordinates, plus manufacturing datums."""

    left: bd.Shape
    right: bd.Shape
    bottom_slots: tuple[float, ...]
    top_slots: tuple[float, ...]
    bolt_slots: tuple[int, ...]
    bolt_z: float
    bottom_z: float
    bottom_length: float
    top_length: float
    body_width: float
    riser_height: float
    split_gap: float
    roof_clearance: float
    minimum_bolt_length: float

    def assembly(self) -> bd.Compound:
        # Compound assigns parents; don't attach the factory's reusable halves.
        return bd.Compound(children=[part.moved(bd.Location()) for part in (self.left, self.right)],
                           label="picatinny_riser")

    def print_parts(self, support: PrintSupport | None = None) -> tuple[bd.Shape, bd.Shape]:
        """Lay each flat split face on Z=0 without changing the fitted geometry.

        With support, each half becomes a compound of the half and its wall,
        moved together so a brim also starts at the origin.
        """
        if support is not None:
            for name, value in (("support wall", support.wall), ("support gap", support.gap),
                                ("support brim", support.brim),
                                ("support brim height", support.brim_height)):
                _finite(value, name)
            # Past the lower jaw the wall would run toward the bed-touching roof.
            if not 0 < support.wall <= -LOWER_CORNER_DEPTH - self.bottom_z:
                raise ValueError("support wall must be positive and stay under the lower jaw")
            if not 0 < support.gap < (NECK_WIDTH - self.split_gap) / 2:
                raise ValueError("support gap must be positive and below the lower jaw lip")
            wall_height = (NECK_WIDTH - self.split_gap) / 2 - support.gap
            if support.brim and not 0 < support.brim_height < wall_height:
                raise ValueError("support brim height must be positive and below the wall top")
        parts = []
        for part, angle, side in ((self.left, 90, -1), (self.right, -90, 1)):
            pieces = [part] if support is None else [part, self._support(side, support)]
            pieces = [piece.rotate(bd.Axis.Y, angle) for piece in pieces]
            offset = -bd.Compound(pieces).bounding_box().min
            placed, *wall = [piece.translate(offset) for piece in pieces]
            placed.label = part.label
            if wall:
                wall[0].label = f"{part.label}_support"
                wall[0].color = bd.Color(0.9, 0.55, 0.2)
                placed = bd.Compound(children=[placed, *wall], label=part.label)
            parts.append(placed)
        return tuple(parts)

    def _support(self, side: int, support: PrintSupport) -> bd.Shape:
        """One half's support wall, plus any brim, in assembly coordinates."""
        # The lip's lowest points are on the neck plane; a flat top keeps
        # the wall out of every layer the 45-degree flank prints in.
        inner, outer = self.split_gap / 2, NECK_WIDTH / 2 - support.gap
        wall = bd.Pos(side * (inner + outer) / 2, 0, 0) * _box(
            outer - inner, self.bottom_length, self.bottom_z, self.bottom_z + support.wall)
        if support.brim:
            # The half meets the bed at the roof, above its host-rail relief.
            low = self.bottom_z - support.brim
            high = min(self.bottom_z + support.wall + support.brim,
                       self.roof_clearance - SUPPORT_BRIM_CLEARANCE)
            wall += bd.Pos(side * (inner + support.brim_height / 2), 0, 0) * _box(
                support.brim_height, self.bottom_length + 2 * support.brim, low, high)
        return wall


def _count(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _finite(value: float, name: str, minimum: float = 0.0) -> None:
    if isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum:g}")


def _bolt_slot_selection(bolt_slots: Iterable[int] | None, count: int) -> tuple[int, ...]:
    """Ascending 1-based bottom slot numbers; None selects the end slots."""
    if bolt_slots is None:
        return tuple(sorted({1, count}))
    selected = tuple(bolt_slots)
    if any(isinstance(i, bool) or not isinstance(i, int) or not 1 <= i <= count
           for i in selected):
        raise ValueError("bolt_slots must contain 1-based bottom slot numbers")
    if len(set(selected)) != len(selected):
        raise ValueError("bolt_slots must not contain duplicates")
    return tuple(sorted(selected))


def slot_centers(count: int, offset: float = 0.0) -> tuple[float, ...]:
    """Centers from -Y to +Y; callers number them 1 through count."""
    _count(count, "slot count")
    _finite(offset, "offset", -math.inf)
    return tuple(offset + (i - (count - 1) / 2) * SLOT_PITCH for i in range(count))


def rail_profile(top_z: float = 0.0, base_z: float | None = None) -> list[tuple[float, float]]:
    """Nominal 45-degree X/Z outline, including the short outer vertical lands.

    Unlike a six-point diamond, this preserves the .748/.108 contact datum.
    base_z extends the narrow neck, e.g. through a bottom clamp cutting tool.
    """
    if base_z is None:
        base_z = top_z - RAIL_BASE_DEPTH
    right = [
        (TOP_WIDTH / 2, top_z),
        (RAIL_WIDTH / 2, top_z - UPPER_CORNER_DEPTH),
        (RAIL_WIDTH / 2, top_z - LOWER_CORNER_DEPTH),
        (NECK_WIDTH / 2, top_z - NECK_DEPTH),
        (NECK_WIDTH / 2, base_z),
    ]
    return right + [(-x, z) for x, z in reversed(right)]


def _along_y(points: list[tuple[float, float]], length: float, y: float = 0) -> bd.Solid:
    face = bd.Face(bd.Wire.make_polygon([(x, y - length / 2, z) for x, z in points], close=True))
    return bd.Solid.extrude(face, (0, length, 0))


def _box(width: float, length: float, low: float, high: float, y: float = 0) -> bd.Shape:
    return bd.Pos(0, y, (low + high) / 2) * bd.Box(width, length, high - low)


def _rect(width: float, length: float, y: float, z: float) -> bd.Wire:
    # Every section shares this corner order, so ruled lofts don't twist.
    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    return bd.Wire.make_polygon([(sx * width / 2, y + sy * length / 2, z) for sx, sy in corners],
                                close=True)


def make_riser(
    bottom_slot_count: int = 5,
    top_slot_count: int = 7,
    bolt_slots: Iterable[int] | None = None,
    bolt: BoltSpec = "M3",
    nut: NutSpec = "M3",
    riser_height: float = 20.0,
    *,
    top_offset: float = 0.0,
    bolt_fit: float = 0.2,
    split_gap: float = 0.1,
    roof_clearance: float = 0.2,
    min_wall: float = 2.0,
    bottom_chamfer: float = 1.0,
) -> Riser:
    """Build two similar clamp halves with independent top/bottom slot datums.

    bolt is a socket-head size or headed BoltData; nut is a size or NutData.
    bolt_fit is DIAMETRAL shaft/head clearance, across-flats nut clearance,
    and extra recess depth. No lateral fit is added to the lower dovetail:
    split_gap supplies jaw take-up without deliberately oversizing the rail.
    bolt_slots=None selects the first and last bottom slots (once if count=1).
    Empty bolt_slots is allowed for an unfastened mockup. Invalid/duplicate
    slot numbers and geometrically impossible fastener/height choices raise.
    bottom_chamfer is the equal-leg, 45-degree bevel on the two outside bottom
    Y edges; zero disables it. Limit it to min_wall/2 to retain pocket edge lips.
    """
    _count(bottom_slot_count, "bottom_slot_count")
    _count(top_slot_count, "top_slot_count")
    for name, value in (("riser_height", riser_height), ("bolt_fit", bolt_fit),
                        ("roof_clearance", roof_clearance), ("min_wall", min_wall),
                        ("split_gap", split_gap), ("bottom_chamfer", bottom_chamfer)):
        _finite(value, name)
    _finite(top_offset, "top_offset", -math.inf)
    if min_wall <= 0:
        raise ValueError("min_wall must be positive")
    if not 0 < split_gap < NECK_WIDTH - 2 * min_wall:
        raise ValueError("split_gap must be positive and leave min_wall in both neck halves")
    if bottom_chamfer > min_wall / 2:
        raise ValueError("bottom_chamfer must be <= min_wall/2 to retain the pocket edge lips")
    selected = _bolt_slot_selection(bolt_slots, bottom_slot_count)
    if isinstance(bolt, str) and isinstance(nut, str) and bolt != nut:
        raise ValueError("bolt and nut sizes must match")
    screw = bolt_data(bolt, kind="socket_head")
    hex_nut = nut_data(nut)
    for name, value in (("bolt diameter", screw.diameter),
                        ("head diameter", screw.head_diameter),
                        ("head length", screw.head_length),
                        ("nut width", hex_nut.width), ("nut thickness", hex_nut.thickness)):
        if value is None or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive (use a socket-head bolt)")
    hole_diameter = screw.diameter + bolt_fit
    if screw.head_diameter <= hole_diameter or hex_nut.width <= hole_diameter:
        raise ValueError("head and nut must be wider than the clearance hole")
    if hole_diameter >= SLOT_WIDTH:
        raise ValueError("bolt clearance diameter must fit inside a Picatinny slot")

    head_depth = screw.head_length + bolt_fit
    nut_depth = hex_nut.thickness + bolt_fit
    head_radius = (screw.head_diameter + bolt_fit) / 2
    fitted_nut = replace(hex_nut, width=hex_nut.width + bolt_fit)
    # The nut pocket's corners point along Y and its flats face Z.
    pocket_half_length = max(head_radius, fitted_nut.width / math.sqrt(3))
    pocket_half_height = max(head_radius, fitted_nut.width / 2)
    if any((b - a) * SLOT_PITCH < 2 * pocket_half_length + min_wall
           for a, b in zip(selected, selected[1:])):
        raise ValueError("selected bolt pockets leave less than min_wall between them")

    bottom_slots = slot_centers(bottom_slot_count)
    top_slots = slot_centers(top_slot_count, top_offset)
    # A half-pitch at either end normally suffices; larger heads grow end lands.
    end_margin = max(SLOT_PITCH / 2, pocket_half_length + min_wall)
    bottom_length = (bottom_slot_count - 1) * SLOT_PITCH + 2 * end_margin
    top_length = top_slot_count * SLOT_PITCH
    footprint_low = min(-bottom_length / 2, top_offset - top_length / 2)
    footprint_high = max(bottom_length / 2, top_offset + top_length / 2)
    # Two intervals overlap by their summed lengths minus their combined span.
    if bottom_length + top_length - (footprint_high - footprint_low) < min_wall:
        raise ValueError("top and bottom footprints must overlap by at least min_wall")
    # Through-cutters overrun both footprints by min_wall at each end.
    cut_length = footprint_high - footprint_low + 2 * min_wall
    cut_y = (footprint_low + footprint_high) / 2

    # Shaft bottom clears the host slot floor; it may project above Z=0.
    bolt_z = -SLOT_DEPTH + hole_diameter / 2 + roof_clearance
    roof_z = max(roof_clearance, bolt_z + pocket_half_height) + min_wall
    bottom_z = min(-NECK_DEPTH, bolt_z - pocket_half_height - min_wall)
    top_base_z = riser_height - RAIL_BASE_DEPTH
    minimum_height = roof_z + min_wall + RAIL_BASE_DEPTH
    if riser_height < minimum_height:
        raise ValueError(f"riser_height must be >= {minimum_height:.4f} mm for these fasteners")
    if bottom_z < -RAIL_BASE_DEPTH:
        raise ValueError("fastener pockets extend below the host rail mounting clearance")
    width = RAIL_WIDTH + 2 * (max(head_depth, nut_depth) + min_wall)

    # The bridge flares from the full saddle width at its root to the standard
    # neck below the upper mounting clearance, interpolating the Y footprints.
    saddle = _box(width, bottom_length, bottom_z, roof_z)
    bridge = bd.Solid.make_loft([_rect(width, bottom_length, 0, roof_z),
                                 _rect(NECK_WIDTH, top_length, top_offset, top_base_z)],
                                ruled=True)
    top = _along_y(rail_profile(riser_height), top_length, top_offset)
    body = saddle + bridge + top
    host_tool = _along_y(rail_profile(base_z=bottom_z - min_wall), cut_length, cut_y)
    # Relief above host top face, not a scaled/oversized dovetail.
    if roof_clearance:
        host_tool += _box(TOP_WIDTH, cut_length, -roof_clearance, roof_clearance, cut_y)
    body -= host_tool
    for y in top_slots:
        body -= _box(RAIL_WIDTH + 2 * min_wall, SLOT_WIDTH,
                     riser_height - SLOT_DEPTH, riser_height + min_wall, y)

    # bd-buildabolt primitives cut along each entry plane's local -Z, so each
    # side's plane faces outward: socket heads enter at -X, nuts at +X.
    socket = CounterBoreBoltHole(screw, depth=width, clearance=bolt_fit, head_clearance=0,
                                 counter_bore_depth=head_depth)
    nut_pocket = NutcatchParallel(fitted_nut, height_clearance=bolt_fit)
    for number in selected:
        y = bottom_slots[number - 1]
        for side, cutter in ((-1, socket), (1, nut_pocket)):
            entry = bd.Plane(origin=(side * width / 2, y, bolt_z),
                             x_dir=(0, 1, 0), z_dir=(side, 0, 0))
            body -= entry * cutter

    # Only bevel the longitudinal bottom edges of the outside fastener faces.
    # Select from the current solid by datums, not topology indices. No end
    # bevels; the inner dovetail lips, split faces, and fastener seats stay intact.
    if bottom_chamfer:
        outer_bottom_edges = [
            edge for edge in body.edges().filter_by(bd.Axis.Y)
            if abs(abs(edge.center().X) - width / 2) < 1e-6
            and abs(edge.center().Z - bottom_z) < 1e-6
        ]
        if len(outer_bottom_edges) != 2:
            raise ValueError("expected two outside bottom Y edges for the chamfer")
        body = bd.chamfer(outer_bottom_edges, length=bottom_chamfer)

    # Remove a real gap rather than coincident faces: bolts can tighten the jaws.
    body -= _box(split_gap, cut_length, bottom_z - min_wall, riser_height + min_wall, cut_y)
    solids = sorted(body.solids(), key=lambda solid: solid.center().X)
    if len(solids) != 2 or any(not solid.is_valid or solid.volume <= 0 for solid in solids):
        raise ValueError("parameters did not produce two connected, valid clamp halves")
    left, right = solids
    left.label, right.label = "left_socket_half", "right_nut_half"
    left.color, right.color = bd.Color(0.35, 0.45, 0.55), bd.Color(0.6, 0.65, 0.7)
    return Riser(
        left=left, right=right, bottom_slots=bottom_slots, top_slots=top_slots,
        bolt_slots=selected, bolt_z=bolt_z, bottom_z=bottom_z, bottom_length=bottom_length,
        top_length=top_length, body_width=width, riser_height=riser_height,
        split_gap=split_gap, roof_clearance=roof_clearance,
        # The nut seats on its pocket floor, bolt_fit inside the outer face.
        minimum_bolt_length=width - head_depth - bolt_fit,
    )


def export_riser(riser: Riser, directory: str | Path,
                 support: PrintSupport | None = None) -> tuple[Path, ...]:
    """Export assembly STEP and separate, split-face-down STEP/STL halves.

    support adds each half's print support wall to its STEP/STL only.
    """
    directory = Path(directory)
    print_parts = riser.print_parts(support)
    directory.mkdir(parents=True, exist_ok=True)
    assembly_path = directory / "picatinny_riser.step"
    bd.export_step(riser.assembly(), assembly_path)
    paths = [assembly_path]
    for name, part in zip(("left", "right"), print_parts):
        for extension, exporter in (("step", bd.export_step), ("stl", bd.export_stl)):
            path = directory / f"picatinny_riser_{name}.{extension}"
            exporter(part, path)
            paths.append(path)
    return tuple(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bottom-slots", type=int, default=5)
    parser.add_argument("--top-slots", type=int, default=7)
    parser.add_argument("--bolt-slots", type=int, nargs="*", default=None,
                        help="1-based bottom slots; default: first and last; empty: no bolts")
    parser.add_argument("--bolt", default="M3", help="socket-head size")
    parser.add_argument("--nut", default=None, help="hex nut size; default: bolt size")
    parser.add_argument("--height", type=float, default=20.0, help="rail top-to-top rise in mm")
    parser.add_argument("--top-offset", type=float, default=0.0, help="top center shift along Y, mm")
    parser.add_argument("--bolt-fit", type=float, default=0.2)
    parser.add_argument("--split-gap", type=float, default=0.1)
    parser.add_argument("--bottom-chamfer", type=float, default=1.0,
                        help="45-degree outside bottom Y-edge chamfer, mm; 0 disables")
    parser.add_argument("--support", action="store_true",
                        help="add a detached support wall under each half's lower jaw lip "
                             "to the print exports")
    parser.add_argument("--support-wall", type=float, default=PrintSupport.wall,
                        help="support thickness from the clamp bottom face toward the rail, mm")
    parser.add_argument("--support-gap", type=float, default=PrintSupport.gap,
                        help="empty separation under the lip, mm; use one layer height")
    parser.add_argument("--support-brim", type=float, nargs="?", const=5.0,
                        default=PrintSupport.brim, metavar="MM",
                        help="brim width around each support wall on the bed, mm "
                             "(5 without a value); implies --support")
    parser.add_argument("--support-brim-height", type=float, default=PrintSupport.brim_height,
                        help="support brim thickness, mm")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--show", action="store_true", help="also open in OCP Viewer")
    args = parser.parse_args()
    support = (PrintSupport(args.support_wall, args.support_gap, args.support_brim,
                            args.support_brim_height)
               if args.support or args.support_brim else None)
    try:
        riser = make_riser(args.bottom_slots, args.top_slots, args.bolt_slots, args.bolt,
                           args.nut or args.bolt, args.height,
                           top_offset=args.top_offset, bolt_fit=args.bolt_fit,
                           split_gap=args.split_gap, bottom_chamfer=args.bottom_chamfer)
        paths = export_riser(riser, args.output_dir, support)
    except (ValueError, KeyError) as error:
        parser.error(str(error))
    for path in paths:
        print(path)
    print(f"Minimum under-head bolt length for full nut engagement: "
          f"{riser.minimum_bolt_length:.2f} mm (verify protrusion after tightening)")
    if args.show:
        from ocp_vscode import show
        show(riser.assembly())


if __name__ == "__main__":
    main()
