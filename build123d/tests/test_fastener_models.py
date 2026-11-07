"""Headless regressions for the migrated designs.

Run from build123d/: uv run python -m unittest discover -s tests -v
Viewer calls are mocked; STEP/STL exports run in a temporary folder, and the
saved STEP geometry is read back for validation. The Picatinny design has a
known pre-existing fillet failure with the locked build123d/OCP versions.
"""

from contextlib import ExitStack, chdir
import math
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

import build123d as bd
import ocp_vscode
from bd_buildabolt import (
    BoltHole, NutcatchParallel, NutcatchSidecut,
    bolt_data, nut_data,
)


ROOT = Path(__file__).resolve().parents[1]


class FastenerPrimitivesTest(unittest.TestCase):
    def assertSameGeometry(self, actual, expected):
        self.assertTrue(actual.is_valid)
        self.assertTrue(expected.is_valid)
        self.assertAlmostEqual(actual.volume, expected.volume, delta=1e-6)
        self.assertLess(abs((actual - expected).volume), 1e-6)
        self.assertLess(abs((expected - actual).volume), 1e-6)

    def test_bolt_holes(self):
        for size, clearance, depth in (("M3", 0.2, 8), ("M3", 0.325, 31.7),
                                       ("M6", 0.2, 23.5)):
            with self.subTest(size=size, clearance=clearance):
                with bd.BuildPart() as legacy:
                    with bd.BuildSketch():
                        bd.Circle((bolt_data(size).diameter + clearance) / 2)
                    bd.extrude(amount=-depth)
                # Native Hole tools extend above the entry plane as well;
                # compare the material removed below it, not tool bounds.
                stock = bd.Pos(Z=-depth / 2) * bd.Box(20, 20, depth)
                hole = BoltHole(size, clearance=clearance, depth=depth)
                self.assertSameGeometry(stock - hole, stock - legacy.part)

    def test_parallel_nut_pockets(self):
        nut = nut_data("M3")
        for rotation, extra_depth in ((0, nut.thickness / 2), (30, 0)):
            with self.subTest(rotation=rotation):
                with bd.BuildPart() as legacy:
                    with bd.BuildSketch():
                        bd.RegularPolygon(nut.width / math.sqrt(3), 6, rotation=rotation)
                    bd.extrude(amount=-nut.thickness - extra_depth)
                pocket = bd.Rot(Z=rotation) * NutcatchParallel(nut, height_clearance=extra_depth)
                self.assertSameGeometry(pocket, legacy.part)

    def test_mf70_side_entry(self):
        nut = nut_data("M6", kind="hexagon_thin")
        radius = nut.width / math.sqrt(3)
        height = nut.width + 6
        # The old pocket starts at -4.8 mm and cuts toward -Z. The new
        # sidecut must start at its far end because it grows toward +Z.
        entry = -(20 - 12 - nut.thickness)
        with bd.BuildPart() as legacy:
            with bd.BuildSketch(bd.Plane.XY.offset(entry)):
                bd.RegularPolygon(radius, 6, rotation=90)
                with bd.Locations((0, radius)):
                    bd.Rectangle(nut.width, height)
            bd.extrude(amount=-nut.thickness - 0.2)
        pocket = bd.Pos(Z=-(20 - 12 + 0.2)) * NutcatchSidecut(
            nut, height_clearance=0.2, depth=radius + height / 2,
        )
        self.assertSameGeometry(pocket, legacy.part)

class FastenerModelsTest(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.directory = stack.enter_context(tempfile.TemporaryDirectory())
        stack.enter_context(chdir(self.directory))
        stack.enter_context(patch.object(sys, "path", [str(ROOT), *sys.path]))
        for name in ("show", "show_all", "set_port", "set_defaults"):
            stack.enter_context(patch.object(ocp_vscode, name))

    @unittest.expectedFailure
    def test_picatinny_full_export(self):
        # Both the original and migrated scripts fail at the first fillet,
        # radius 5.83333 mm, with build123d 0.13 / OCP 8.0.1.1.0.
        # Unexpected success flags this test for removal once it is repaired.
        runpy.run_path(str(ROOT / "picatinny-sling-point.py"), run_name="__main__")

    def test_picatinny_before_fillet(self):
        # Validate the fastener cuts even though the later, unrelated fillet
        # currently fails. Stop before that operation without changing geometry.
        class BeforeFillet(Exception):
            pass

        captured = []

        def stop_before_fillet(*args, **kwargs):
            captured.append(bd.BuildPart._get_context().part)
            raise BeforeFillet()

        with patch.object(bd, "fillet", side_effect=stop_before_fillet):
            with self.assertRaises(BeforeFillet):
                runpy.run_path(str(ROOT / "picatinny-sling-point.py"), run_name="__main__")
        self.assertEqual(len(captured), 1)
        self.assertTrue(captured[0].is_valid)
        self.assertEqual(len(captured[0].solids()), 1)
        self.assertAlmostEqual(captured[0].volume, 4752.890398905498, delta=1e-5)

    def test_default_models(self):
        models = {
            "mf70-indicator-holder.py": ["mf70-indicator-holder-32.5mm"],
            "molle_backplate.py": ["molle-backplate-1-5"],
            "molle_cylinder_elasticord_pouch.py": ["molle-cylinder-elastic-cord-pouch"],
        }
        # Volumes (mm^3) from the pre-primitive models with the same lockfile.
        # In particular, the pouch volume guards its 82-degree countersinks.
        volumes = {
            "mf70-indicator-holder-32.5mm": 6265.471078201506,
            "molle-backplate-1-5": 13640.376474618832,
            "molle-cylinder-elastic-cord-pouch": 65979.23480395174,
        }
        for script, outputs in models.items():
            with self.subTest(script=script):
                runpy.run_path(str(ROOT / script), run_name="__main__")
                for stem in outputs:
                    path = Path(self.directory) / f"{stem}.step"
                    self.assertTrue(path.is_file())
                    shape = bd.import_step(path)
                    self.assertTrue(shape.is_valid, stem)
                    self.assertEqual(len(shape.solids()), 1, stem)
                    self.assertAlmostEqual(shape.volume, volumes[stem], delta=1e-5)
                    if script != "molle_backplate.py":
                        self.assertGreater(path.with_suffix(".stl").stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
