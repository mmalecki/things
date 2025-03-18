"""Cover for the Storz and Bickel Venty vaporizer, meant to be printed out of Varioshore TPU"""
from build123d import *
from ocp_vscode import *

chamfer_l = 4.0
fillet_r = 3.0

wall_t = 1.6
fit = -0.125

top_l = 48.6
top_w = 36.85

bottom_l = 43.6
bottom_w = 31.3

# Tolerances measured in.
screen_bottom_off = 42
screen_h = 20
screen_w = 30

usb_offset = 9
usb_clearance_w = 12
usb_clearance_l = 7

h = 85

def base_shape(l, w, offset, c = chamfer_l):
    return fillet(chamfer(Rectangle(l + offset, w + offset).vertices(), length = c).vertices(), radius=fillet_r)

def top_shape(l, w, offset, r = fillet_r):
    return fillet(Rectangle(l + offset, w + offset).vertices(), radius = r)

def cover():
    with BuildPart() as p:
        oc_r = (1 + (2 * wall_t / bottom_l))
        with BuildSketch() as base:
            base_shape(bottom_l, bottom_w, 2 * wall_t + fit, c = oc_r * chamfer_l)

        with BuildSketch(base.faces()[0].offset(h + wall_t)):
            top_shape(top_l, top_w, 2 * wall_t + fit, r = oc_r * fillet_r)

        loft()

        with BuildSketch(Plane.XY.offset(wall_t)) as base:
            base_shape(bottom_l, bottom_w, fit)

        with BuildSketch(base.faces()[0].offset(h + wall_t)):
            top_shape(top_l, top_w, fit)

        loft(mode=Mode.SUBTRACT)

        # Make a screen cut-out.
        # This is easier than trying to locate a non-planar workplane.
        with Locations((0, (top_w + bottom_w) / 4, screen_bottom_off + wall_t + screen_h / 2)):
            Box(screen_w, wall_t * 4, screen_h, mode=Mode.SUBTRACT)

        fillet(p.faces().sort_by(Axis.Z)[1].edges(), radius=fillet_r)
        chamfer(p.edges().sort_by(Axis.Z)[-1], length=wall_t / 4)
        chamfer(p.edges().sort_by(Axis.Z)[0], length=chamfer_l / 1.5)

        with BuildSketch(p.faces().sort_by(Axis.Z)[0]):
            with Locations((0, -usb_offset)):
                fillet(Rectangle(usb_clearance_w, usb_clearance_l).vertices(), radius=usb_clearance_l / 2)
        extrude(amount=-wall_t, mode=Mode.SUBTRACT)
        chamfer(p.edges(Select.LAST).sort_by(Axis.Z)[0], length = wall_t / 4)


    return p

c = cover()
export_step(c.part, "venty-cover.step")
export_stl(c.part, "venty-cover.stl")

show(c)
