"""Geometry and export regressions; run with unittest discover from build123d/."""
from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import build123d as bd
from bd_buildabolt import bolt_data, nut_data

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import picatinny_riser as pr


# Geometric tolerances, mm and mm^3 (not printing/fit tolerances).
LINEAR_TOL = 1e-6
VOLUME_TOL = 1e-5


def volume(shape):
    return sum(solid.volume for solid in shape.solids()) if shape is not None else 0.0


def overlap(a, b):
    return volume(a.intersect(b))


def x_cylinder(radius, start, length, y, z):
    return bd.Solid.make_cylinder(radius, length,
                                 bd.Plane(origin=(start, y, z), z_dir=(1, 0, 0)))


def host_rail(length):
    # Independent nominal cross-section gauge; don't reuse the model's outline.
    # These are the .748/.108 contact-datum 45-degree profile vertices in mm.
    outline = [(8.0772, 0), (10.6045, -2.5273), (10.6045, -3.0607),
               (7.8359, -5.8293), (7.8359, -10), (-7.8359, -10),
               (-7.8359, -5.8293), (-10.6045, -3.0607),
               (-10.6045, -2.5273), (-8.0772, 0)]
    face = bd.Face(bd.Wire.make_polygon([(x, -length / 2, z) for x, z in outline]))
    return bd.Solid.extrude(face, (0, length, 0))


class RiserGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default = pr.make_riser()

    def assertTwoHalves(self, riser):
        for part in (riser.left, riser.right):
            self.assertTrue(part.is_valid)
            self.assertEqual(len(part.solids()), 1)
            self.assertGreater(part.volume, 0)
        self.assertLess(overlap(riser.left, riser.right), VOLUME_TOL)
        self.assertAlmostEqual(riser.left.bounding_box().max.X, -riser.split_gap / 2,
                               delta=LINEAR_TOL)
        self.assertAlmostEqual(riser.right.bounding_box().min.X, riser.split_gap / 2,
                               delta=LINEAR_TOL)
        self.assertAlmostEqual(riser.left.distance_to(riser.right), riser.split_gap,
                               delta=LINEAR_TOL)

    def assertSlotGeometry(self, shapes, centers, top_z):
        # Each half contributes one planar floor per slot. Read actual saved/native
        # geometry, not just the metadata generated alongside the part.
        floors = [face for part in shapes for face in part.faces()
                  if face.geom_type == bd.GeomType.PLANE
                  and abs(face.normal_at().Z - 1) < LINEAR_TOL
                  and abs(face.center().Z - (top_z - 2.9972)) < LINEAR_TOL]
        self.assertEqual(len(floors), 2 * len(centers))
        measured_centers = sorted(face.center().Y for face in floors)
        for actual, expected in zip(measured_centers, sorted(list(centers) * 2)):
            self.assertAlmostEqual(actual, expected, delta=LINEAR_TOL)
        for face in floors:
            self.assertAlmostEqual(face.bounding_box().size.Y, 5.2324, delta=LINEAR_TOL)
        for part in shapes:
            top_faces = [f for f in part.faces()
                         if abs(f.center().Z - top_z) < LINEAR_TOL
                         and abs(f.normal_at().Z - 1) < LINEAR_TOL]
            self.assertEqual(len(top_faces), len(centers) + 1)

    def assertTaperedNeck(self, shapes, riser, root_z):
        top_z = riser.riser_height - 9.3218
        top_center = sum(riser.top_slots) / len(riser.top_slots)
        shapes = sorted(shapes, key=lambda part: part.center().X)
        for fraction in (0, 0.1, 0.5, 0.9, 1):
            z = root_z + fraction * (top_z - root_z)
            width = riser.body_width + fraction * (15.6718 - riser.body_width)
            length = riser.bottom_length + fraction * (riser.top_length - riser.bottom_length)
            center_y = fraction * top_center
            for side, part in zip((-1, 1), shapes):
                section = bd.section(part, section_by=bd.Plane.XY.offset(z))
                self.assertEqual(len(section.faces()), 1)
                bounds = section.bounding_box()
                self.assertAlmostEqual(bounds.min.X, -width / 2 if side < 0 else riser.split_gap / 2,
                                       delta=LINEAR_TOL)
                self.assertAlmostEqual(bounds.max.X, -riser.split_gap / 2 if side < 0 else width / 2,
                                       delta=LINEAR_TOL)
                self.assertAlmostEqual(bounds.min.Y, center_y - length / 2, delta=LINEAR_TOL)
                self.assertAlmostEqual(bounds.max.Y, center_y + length / 2, delta=LINEAR_TOL)
                self.assertAlmostEqual(section.area, (width - riser.split_gap) / 2 * length,
                                       delta=VOLUME_TOL)
        for part in shapes:
            # Above the taper, the standard narrow neck must remain unobstructed.
            neck = bd.section(part, section_by=bd.Plane.XY.offset(top_z + 0.25))
            self.assertAlmostEqual(neck.bounding_box().size.X, (15.6718 - riser.split_gap) / 2,
                                   delta=LINEAR_TOL)
            # No horizontal ledge at the old narrow web's root.
            ledges = [f for f in part.faces() if abs(f.center().Z - root_z) < LINEAR_TOL
                      and abs(f.normal_at().Z - 1) < LINEAR_TOL]
            self.assertEqual(len(ledges), 0)

    def assertBottomChamfers(self, shapes, riser, chamfer):
        bevels = []
        for side, part in zip((-1, 1), sorted(shapes, key=lambda p: p.center().X)):
            faces = [f for f in part.faces() if f.geom_type == bd.GeomType.PLANE
                     and abs(f.normal_at().X - side / math.sqrt(2)) < LINEAR_TOL
                     and abs(f.normal_at().Z + 1 / math.sqrt(2)) < LINEAR_TOL
                     and abs(f.center().X - side * (riser.body_width / 2 - chamfer / 2)) < LINEAR_TOL]
            self.assertEqual(len(faces), 1)
            face = faces[0]
            bounds = face.bounding_box()
            self.assertAlmostEqual(bounds.size.X, chamfer, delta=LINEAR_TOL)
            self.assertAlmostEqual(bounds.size.Z, chamfer, delta=LINEAR_TOL)
            self.assertAlmostEqual(bounds.min.Z, part.bounding_box().min.Z, delta=LINEAR_TOL)
            self.assertAlmostEqual(bounds.min.Y, -riser.bottom_length / 2, delta=LINEAR_TOL)
            self.assertAlmostEqual(bounds.max.Y, riser.bottom_length / 2, delta=LINEAR_TOL)
            self.assertAlmostEqual(face.area, math.sqrt(2) * chamfer * riser.bottom_length,
                                   delta=VOLUME_TOL)
            bevels.append(face)
        return bevels

    def test_outer_bottom_chamfers(self):
        for chamfer, kwargs in ((1.0, {}), (0.5, dict(bolt="M4", nut="M4", top_offset=3))):
            with self.subTest(chamfer=chamfer, **kwargs):
                r = pr.make_riser(bottom_chamfer=chamfer, **kwargs)
                sharp = pr.make_riser(bottom_chamfer=0, **kwargs)
                self.assertTwoHalves(r)
                self.assertBottomChamfers((r.left, r.right), r, chamfer)
                for before, after in ((sharp.left, r.left), (sharp.right, r.right)):
                    # Exactly one triangular prism removed per half; nothing added.
                    removed = before - after
                    self.assertEqual(len(removed.solids()), 1)
                    self.assertAlmostEqual(volume(removed), chamfer ** 2 * r.bottom_length / 2,
                                           delta=VOLUME_TOL)
                    self.assertLess(volume(after - before), VOLUME_TOL)
                    bounds = removed.bounding_box()
                    self.assertAlmostEqual(bounds.size.X, chamfer, delta=LINEAR_TOL)
                    self.assertAlmostEqual(bounds.size.Z, chamfer, delta=LINEAR_TOL)
                    self.assertAlmostEqual(bounds.size.Y, r.bottom_length, delta=LINEAR_TOL)

    def test_flared_bridge_neck(self):
        cases = [
            (self.default, 3.6528),
            (pr.make_riser(bottom_slot_count=5, top_slot_count=3, top_offset=5), 3.6528),
            (pr.make_riser(bottom_slot_count=1, top_slot_count=1, riser_height=15), 3.6528),
            (pr.make_riser(bolt="M4", nut="M4", top_offset=-4, riser_height=25), 4.9028),
        ]
        for riser, root_z in cases:
            with self.subTest(height=riser.riser_height, top_slots=riser.top_slots):
                self.assertTwoHalves(riser)
                self.assertTaperedNeck((riser.left, riser.right), riser, root_z)

    def test_default_geometry_and_nominal_host_fit(self):
        r = self.default
        self.assertTwoHalves(r)
        self.assertSlotGeometry((r.left, r.right), r.top_slots, 20)
        self.assertAlmostEqual(sum(r.top_slots), 0)
        self.assertAlmostEqual(sum(r.bottom_slots), 0)
        for centers in (r.top_slots, r.bottom_slots):
            for a, b in zip(centers, centers[1:]):
                self.assertAlmostEqual(b - a, 10.0076)
        host = host_rail(120)
        for part in (r.left, r.right):
            self.assertLess(overlap(part, host), VOLUME_TOL)
            self.assertLess(part.distance_to(host), LINEAR_TOL)
        self.assertAlmostEqual(r.left.bounding_box().max.Z, 20, delta=LINEAR_TOL)
        self.assertAlmostEqual(r.body_width, 31.609)
        self.assertAlmostEqual(r.minimum_bolt_length, 28.209)

    def test_bolt_axes_clearances_and_unselected_slots(self):
        r = self.default
        for index, y in enumerate(r.bottom_slots, 1):
            gauge = x_cylinder(1.6, -r.body_width / 2, r.body_width, y, r.bolt_z)
            larger = x_cylinder(1.65, -r.body_width / 2, r.body_width, y, r.bolt_z)
            for part in (r.left, r.right):
                if index in r.bolt_slots:
                    self.assertLess(overlap(part, gauge), VOLUME_TOL)
                    self.assertGreater(overlap(part, larger), 0.01)
                else:
                    self.assertGreater(overlap(part, gauge), 1)
            # A physical M3 shaft clears a standard slot, including its floor.
            if index in r.bolt_slots:
                slotted_host = host_rail(120) - bd.Pos(0, y, -1.4986) * bd.Box(30, 5.2324, 2.9972)
                shaft = x_cylinder(1.5, -r.body_width / 2, r.body_width, y, r.bolt_z)
                self.assertLess(overlap(slotted_host, shaft), VOLUME_TOL)
        self.assertAlmostEqual(r.bolt_z - 1.6 - (-2.9972), 0.2)

    def test_head_and_nut_recess_dimensions(self):
        r = self.default
        left_bevel, right_bevel = self.assertBottomChamfers((r.left, r.right), r, 1.0)
        for index in r.bolt_slots:
            y = r.bottom_slots[index - 1]
            # M3 socket head + fit: diameter 5.7, depth 3.2.
            head = x_cylinder(2.85, -r.body_width / 2, 3.2, y, r.bolt_z)
            self.assertLess(overlap(r.left, head), VOLUME_TOL)
            self.assertGreaterEqual(head.distance_to(left_bevel), 1.0 - LINEAR_TOL)
            too_deep = x_cylinder(2.85, -r.body_width / 2, 3.25, y, r.bolt_z)
            self.assertGreater(overlap(r.left, too_deep), 0.1)
            self.assertGreaterEqual(r.bolt_z - 2.85 - r.left.bounding_box().min.Z, 2 - LINEAR_TOL)
            # Construct the hex independently: across flats 5.7, depth 2.6.
            entry = bd.Plane(origin=(r.body_width / 2, y, r.bolt_z),
                             x_dir=(0, 1, 0), z_dir=(1, 0, 0))
            hex_face = bd.RegularPolygon(5.7 / math.sqrt(3), 6)
            pocket = entry * bd.extrude(hex_face, amount=-2.6)
            self.assertLess(overlap(r.right, pocket), VOLUME_TOL)
            self.assertGreaterEqual(pocket.distance_to(right_bevel), 1.0 - LINEAR_TOL)
            self.assertGreater(overlap(r.right, entry * bd.extrude(hex_face, amount=-2.65)), 0.1)

    def test_parameter_matrix(self):
        cases = [
            dict(bottom_slot_count=1, top_slot_count=1, bolt_slots=(1,), riser_height=15),
            dict(bottom_slot_count=4, top_slot_count=2, bolt_slots=(2,), top_offset=-3),
            dict(bottom_slot_count=3, top_slot_count=6, bolt_slots=(3, 1, 2), top_offset=4.5),
            dict(bottom_slot_count=8, top_slot_count=5, bolt_slots=range(1, 9), riser_height=25),
            dict(bottom_slot_count=2, top_slot_count=3, bolt_slots=(), top_offset=6),
            dict(bottom_slot_count=3, top_slot_count=4, bolt_slots=(1, 3), bolt="M4", nut="M4"),
        ]
        for kwargs in cases:
            with self.subTest(**kwargs):
                r = pr.make_riser(**kwargs)
                self.assertTwoHalves(r)
                self.assertSlotGeometry((r.left, r.right), r.top_slots, r.riser_height)
                self.assertBottomChamfers((r.left, r.right), r, 1.0)
                self.assertAlmostEqual(sum(r.bottom_slots), 0)
                self.assertAlmostEqual(sum(r.top_slots) / len(r.top_slots), kwargs.get("top_offset", 0))
                for part in (r.left, r.right):
                    self.assertLess(overlap(part, host_rail(200)), VOLUME_TOL)

    def test_default_selection_and_mirrored_blank(self):
        one = pr.make_riser(bottom_slot_count=1, top_slot_count=1)
        self.assertEqual(one.bolt_slots, (1,))
        blank = pr.make_riser(bolt_slots=())
        mirror = blank.right.mirror(bd.Plane.YZ)
        self.assertLess(volume(blank.left - mirror), VOLUME_TOL)
        self.assertLess(volume(mirror - blank.left), VOLUME_TOL)

    def test_custom_fastener_data(self):
        screw = replace(bolt_data("M3", "socket_head"), head_length=3.4)
        nut = nut_data("M3", "hexagon_thin")
        r = pr.make_riser(bolt=screw, nut=nut, bolt_slots=(2, 4))
        self.assertTwoHalves(r)
        self.assertAlmostEqual(r.body_width, pr.RAIL_WIDTH + 2 * (3.6 + 2))
        self.assertEqual(r.bolt_slots, (2, 4))

    def test_export_and_print_orientation(self):
        r = self.default
        with tempfile.TemporaryDirectory() as directory:
            paths = pr.export_riser(r, directory)
            self.assertEqual(len(paths), 5)
            for path in paths:
                self.assertGreater(path.stat().st_size, 100)
            assembly = bd.import_step(paths[0])
            self.assertEqual(len(assembly.solids()), 2)
            self.assertTrue(assembly.is_valid)
            self.assertAlmostEqual(assembly.volume, r.left.volume + r.right.volume, delta=VOLUME_TOL)
            self.assertSlotGeometry(assembly.solids(), r.top_slots, 20)
            self.assertTaperedNeck(assembly.solids(), r, 3.6528)
            self.assertBottomChamfers(assembly.solids(), r, 1.0)
            for original, path in zip((r.left, r.right), (paths[1], paths[3])):
                saved = bd.import_step(path)
                self.assertTrue(saved.is_valid)
                self.assertEqual(len(saved.solids()), 1)
                self.assertAlmostEqual(saved.volume, original.volume, delta=VOLUME_TOL)
                self.assertAlmostEqual(saved.bounding_box().min.Z, 0, delta=LINEAR_TOL)
                # The large central split face, not the outside jaw, is on the bed.
                original_split = [f for f in original.faces()
                                  if abs(abs(f.center().X) - r.split_gap / 2) < LINEAR_TOL
                                  and abs(abs(f.normal_at().X) - 1) < LINEAR_TOL]
                bed = [f for f in saved.faces() if abs(f.center().Z) < LINEAR_TOL
                       and abs(f.normal_at().Z + 1) < LINEAR_TOL]
                self.assertAlmostEqual(sum(f.area for f in bed), sum(f.area for f in original_split),
                                       delta=VOLUME_TOL)
            # Exports must not attach/mutate the factory halves via anytree parents.
            self.assertIsNone(r.left.parent)
            self.assertIsNone(r.right.parent)
            pr.export_riser(r, directory)

    def assertPrintSupports(self, parts, riser, support):
        unsupported = riser.print_parts()
        for side, part, bare in zip((-1, 1), parts, unsupported):
            self.assertEqual(len(part.solids()), 2)
            # The wall is the smaller solid; the half lands exactly as unsupported.
            wall, half = sorted(part.solids(), key=lambda solid: solid.volume)
            self.assertLess(volume(half - bare), VOLUME_TOL)
            self.assertLess(volume(bare - half), VOLUME_TOL)
            # Height from the bed to one gap below the 15.6718 mm neck plane.
            height = (15.6718 - riser.split_gap) / 2 - support.gap
            self.assertAlmostEqual(wall.volume, support.wall * height * riser.bottom_length,
                                   delta=VOLUME_TOL)
            bounds, half_bounds = wall.bounding_box(), half.bounding_box()
            self.assertAlmostEqual(bounds.min.Z, 0, delta=LINEAR_TOL)
            self.assertAlmostEqual(bounds.size.Z, height, delta=LINEAR_TOL)
            self.assertAlmostEqual(bounds.size.X, support.wall, delta=LINEAR_TOL)
            # Flush with the clamp bottom face and spanning the saddle along Y.
            bottom = [f for f in half.faces() if abs(f.normal_at().X - side) < LINEAR_TOL
                      and abs(f.center().X - (half_bounds.min.X if side < 0 else half_bounds.max.X))
                      < LINEAR_TOL]
            self.assertEqual(len(bottom), 1)
            face_bounds = bottom[0].bounding_box()
            self.assertAlmostEqual(bounds.min.X if side < 0 else bounds.max.X,
                                   face_bounds.min.X, delta=LINEAR_TOL)
            self.assertAlmostEqual(bounds.min.Y, face_bounds.min.Y, delta=LINEAR_TOL)
            self.assertAlmostEqual(bounds.max.Y, face_bounds.max.Y, delta=LINEAR_TOL)
            # Exactly one gap clear of the half, and under the lip rather than beside it.
            self.assertAlmostEqual(wall.distance_to(half), support.gap, delta=LINEAR_TOL)
            raised = wall.translate((0, 0, support.gap + 0.05))
            self.assertGreater(overlap(half, raised), 0.01)

    def test_print_support(self):
        cases = [
            (self.default, pr.PrintSupport()),
            (self.default, pr.PrintSupport(wall=2.5, gap=0.12)),
            (pr.make_riser(bolt="M4", nut="M4", top_offset=-4, riser_height=25, split_gap=0.4),
             pr.PrintSupport(wall=0.8, gap=0.3)),
        ]
        for riser, support in cases:
            with self.subTest(support=support, split_gap=riser.split_gap):
                parts = riser.print_parts(support)
                self.assertPrintSupports(parts, riser, support)
                self.assertEqual([part.label for part in parts],
                                 ["left_socket_half", "right_nut_half"])
        self.assertIsNone(self.default.left.parent)
        for part in self.default.print_parts():
            self.assertEqual(len(part.solids()), 1)

    def test_print_support_export(self):
        r = self.default
        support = pr.PrintSupport(wall=1.2, gap=0.16)
        with tempfile.TemporaryDirectory() as bare, tempfile.TemporaryDirectory() as directory:
            plain = pr.export_riser(r, bare)
            paths = pr.export_riser(r, directory, support)
            assembly = bd.import_step(paths[0])
            self.assertEqual(len(assembly.solids()), 2)
            self.assertAlmostEqual(assembly.volume, r.left.volume + r.right.volume, delta=VOLUME_TOL)
            saved = [bd.import_step(paths[i]) for i in (1, 3)]
            self.assertPrintSupports(saved, r, support)
            for i in (2, 4):
                self.assertGreater(paths[i].stat().st_size, plain[i].stat().st_size)

    def test_cli_print_support(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, str(ROOT / "picatinny_riser.py"), "--bottom-slots", "2",
                       "--top-slots", "3", "--output-dir", directory]
            result = subprocess.run(command + ["--support", "--support-wall", "0.8",
                                               "--support-gap", "0.15"],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = pr.make_riser(bottom_slot_count=2, top_slot_count=3)
            saved = [bd.import_step(Path(directory) / f"picatinny_riser_{name}.step")
                     for name in ("left", "right")]
            self.assertPrintSupports(saved, expected, pr.PrintSupport(wall=0.8, gap=0.15))
            # Without the switch, the wall settings don't add a support.
            result = subprocess.run(command + ["--support-wall", "0.8"],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            saved = bd.import_step(Path(directory) / "picatinny_riser_left.step")
            self.assertEqual(len(saved.solids()), 1)
            # Bad support values are usage errors, before anything is written.
            empty = Path(directory) / "rejected"
            result = subprocess.run(command[:-1] + [str(empty), "--support", "--support-gap", "0"],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("support gap", result.stderr)
            self.assertFalse(empty.exists())

    def test_invalid_print_support(self):
        r = self.default
        # The default lower jaw is 6.0472 - 3.0607 = 2.9865 mm deep along the wall.
        cases = [
            dict(wall=0), dict(wall=-1), dict(wall=math.nan), dict(wall=math.inf), dict(wall=True),
            dict(wall=2.99), dict(gap=0), dict(gap=-0.1), dict(gap=math.nan), dict(gap=True),
            dict(gap=(15.6718 - r.split_gap) / 2),
        ]
        for kwargs in cases:
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                r.print_parts(pr.PrintSupport(**kwargs))
            with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                pr.export_riser(r, Path(directory) / "out", pr.PrintSupport(**kwargs))

    def test_cli_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "picatinny_riser.py"), "--bottom-slots", "1",
                 "--top-slots", "2", "--height", "16", "--bottom-chamfer", "0.5",
                 "--output-dir", directory],
                cwd=directory, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(directory) / "picatinny_riser_right.stl").is_file())
            saved = bd.import_step(Path(directory) / "picatinny_riser.step")
            expected = pr.make_riser(bottom_slot_count=1, top_slot_count=2, riser_height=16,
                                     bottom_chamfer=0.5)
            self.assertBottomChamfers(saved.solids(), expected, 0.5)

    def test_invalid_parameters(self):
        cases = [
            dict(bottom_slot_count=0), dict(top_slot_count=-1), dict(top_slot_count=2.5),
            dict(bottom_slot_count=True), dict(bolt_slots=(0,)), dict(bolt_slots=(6,)),
            dict(bolt_slots=(1, 1)), dict(bolt_slots=(1.0,)), dict(bolt_slots=(True,)),
            dict(bolt="M3", nut="M4"), dict(bolt="M6", nut="M6"),
            dict(bolt=bolt_data("M3")), dict(riser_height=5), dict(riser_height=math.nan),
            dict(top_offset=math.inf), dict(top_offset=1000), dict(bolt_fit=-0.1),
            dict(split_gap=0), dict(split_gap=20), dict(min_wall=0), dict(roof_clearance=-1),
            dict(bottom_chamfer=-0.1), dict(bottom_chamfer=math.nan), dict(bottom_chamfer=math.inf),
            dict(bottom_chamfer=True), dict(bottom_chamfer=1.01),
            dict(bolt=replace(bolt_data("M3", "socket_head"), head_diameter=12), bolt_slots=(1, 2)),
            dict(bolt=replace(bolt_data("M3", "socket_head"), head_diameter=20),
                 bolt_slots=(3,), riser_height=40),
        ]
        for kwargs in cases:
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                pr.make_riser(**kwargs)


if __name__ == "__main__":
    unittest.main()
