"""Aluminum extrusion table for a LumenPnP v4

3030 V-slot legs and top frame, 2020 V-slot lower stretchers, all mocked as
extruded rectangles, plus a mock table top. The table is centered on the XY
origin, floor at Z=0, X is width and Y is depth.
"""
import os
from build123d import *
from ocp_vscode import *

set_port(int(os.environ.get("OCP_PORT", 3939)))

# LumenPnP v4 envelope, per the Opulo v4 brochure: 765 x 710 x 270 mm
machine_w = 765
machine_d = 710

margin = 20  # Per side, around the machine envelope
top_w = machine_w + 2 * margin
top_d = machine_d + 2 * margin
height = 750  # Floor to the table top surface

top_t = 10  # Table top thickness
leg = 30  # 3030 profile, legs and top frame
stretcher = 20  # 2020 profile, lower stretchers

frame_h = height - top_t  # Floor to the top of the frame
stretcher_z = 150  # Floor to the bottom of the lower stretchers


def extrusion(size, length, direction):
    """A square profile of `size`, `length` long, starting at the origin and
    running along `direction` ("X", "Y" or "Z"), centered on that axis."""
    plane = {"X": Plane.YZ, "Y": Plane.XZ.reverse(), "Z": Plane.XY}[direction]
    return extrude(plane * Rectangle(size, size), amount=length)


def ring(size, z, name):
    """Four `size` profile members between the legs, bottoms at `z`, outer
    faces flush with the legs' outer faces."""
    x_len = top_w - 2 * leg
    y_len = top_d - 2 * leg
    zc = z + size / 2
    members = []
    for side, sy in (("front", -1), ("back", 1)):
        m = Pos(-x_len / 2, sy * (top_d / 2 - size / 2), zc) * extrusion(size, x_len, "X")
        m.label = f"{name}_x:{side}"
        members.append(m)
    for side, sx in (("left", -1), ("right", 1)):
        m = Pos(sx * (top_w / 2 - size / 2), -y_len / 2, zc) * extrusion(size, y_len, "Y")
        m.label = f"{name}_y:{side}"
        members.append(m)
    return members


def table():
    parts = []

    for name, sx, sy in (
        ("front_left", -1, -1),
        ("front_right", 1, -1),
        ("back_left", -1, 1),
        ("back_right", 1, 1),
    ):
        l = Pos(sx * (top_w / 2 - leg / 2), sy * (top_d / 2 - leg / 2), 0) * extrusion(leg, frame_h, "Z")
        l.label = f"leg:{name}"
        parts.append(l)

    parts += ring(leg, frame_h - leg, "top")
    parts += ring(stretcher, stretcher_z, "stretcher")

    top = Pos(0, 0, frame_h + top_t / 2) * Box(top_w, top_d, top_t)
    top.label = "top"
    parts.append(top)

    return Compound(children=parts, label="lumenpnp_table")


table_ = table()
export_step(table_, "lumenpnp-table.step")

show(table_)
