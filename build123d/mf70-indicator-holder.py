"""Proxxon MF70 mount for Noga FA1410 dial indicator clamp"""
import os
import math
from build123d import *
import cq_queryabolt as queryabolt
from ocp_vscode import *

bolt = "M6"

bolt_ = queryabolt.boltData(bolt)
bolt_d = bolt_["diameter"]
nut = queryabolt.nutData(bolt, kind="hexagon_thin")
nut_w = nut["width"]
nut_r = 2 * nut["width"] * math.sqrt(3) / 6
nut_t = nut["thickness"]
bolt_fit = 0.2

set_port(int(os.environ.get("OCP_PORT", 3939)))
set_defaults(reset_camera=False)

wall_t = 3 # Wall thickness

spindle_fit = 0.125
spindle_d = 8
spindle_top_d = 20

compliance = 1

def holder(spindle_clearance):
    id = spindle_d + spindle_fit
    od = spindle_d + 2 * wall_t
    a = 180
    h = nut_w + 2 * wall_t

    with BuildPart() as hold:
        # Build the basic outline, including clearance for the spindle
        with BuildSketch():
            with BuildLine():
                arc = CenterArc(
                    (0, 0),
                    od / 2,
                    (360 - a) / 2 - 270, a
                )
                l2 = Line(arc @ 0, arc @ 0 + (0, spindle_clearance + spindle_d / 2))
                l3 = Line(l2 @ 1, arc @ 1 + (0, spindle_clearance + spindle_d / 2))
                l4 = Line(l3 @ 1, arc @ 1)
            make_face()
            Circle(id / 2, mode=Mode.SUBTRACT)

        extrude(amount = h)

        # Create clearance for the spindle top
        with BuildSketch():
            Circle((spindle_top_d + spindle_fit) / 2)
        extrude(amount= h / 2, mode=Mode.SUBTRACT)
        fillet(hold.edges(Select.LAST), radius=wall_t / 4)

        # Create mounting features
        mount_plane = Plane(hold.faces().sort_by(Axis.Y)[-1])

        bolt_l = 20
        clamp_l = 12
        with BuildSketch(mount_plane.offset(-(bolt_l - clamp_l - nut_t))):
            RegularPolygon(nut_r, 6, rotation=90)
            with Locations((0, nut_r)):
                Rectangle(nut_w, h)
        extrude(amount=-nut["thickness"] - bolt_fit, mode=Mode.SUBTRACT)

        with BuildSketch(mount_plane):
            Circle((bolt_d + bolt_fit) / 2)
        extrude(amount=-spindle_clearance + spindle_top_d / 2 - spindle_d / 2 + wall_t, mode=Mode.SUBTRACT)

        chamfer(hold.faces().sort_by(Axis.Z)[-1].edges(), wall_t / 4)
        chamfer(hold.faces().sort_by(Axis.Y)[-1].edges().filter_by(Axis.Z), wall_t / 6)

    return hold

hold_32_5 = holder(32.5)
export_step(hold_32_5.part, "mf70-indicator-holder-32.5mm.step")
export_stl(hold_32_5.part, "mf70-indicator-holder-32.5mm.stl")

show(hold_32_5)
