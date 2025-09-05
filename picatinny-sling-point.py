import math
from build123d import *
from ocp_vscode import *
import cq_queryabolt as queryabolt
set_defaults(reset_camera=Camera.CENTER)


bolt_ = "M3"
bolt = queryabolt.boltData(bolt_)
nut = queryabolt.nutData(bolt_)

t = 5
fit = 0.25
bolt_fit = 0.325

pic_w0 = 21.2 + 2 *fit
pic_w1 = 15.67 + 2 *fit
pic_diff = pic_w0 - pic_w1
pic_h = 3 + fit

l = 15.25

w = pic_w0 + 2 * t

eye_d = 4

with BuildSketch(Plane.XY) as pic:
    with BuildLine() as pic_line:
        l0 = Line((-pic_w0 / 2, 0), (-pic_w1 / 2, pic_h))
        l1 = Line(l0 @ 1, (pic_w1 / 2, pic_h))
        l2 = Line(l1 @ 1, (pic_w0 / 2, 0))
        mirror(pic_line.line, about=Plane.XZ)
    make_face()

eye_l = eye_d + 2 * fit + t
eye_w = w - pic_diff / 2 - t
eye_h = 6.5
eye_t = 5

with BuildSketch(Plane.XY) as eye:
    with BuildLine():
            l0 = Line((-eye_w / 2, 0), (eye_w / 2, 0))
            l1 = Line(l0 @ 1, (eye_w / 2, eye_l))
            l2 = ThreePointArc(l1 @ 1, (0.0, eye_l * 1.5), (-eye_w / 2, eye_l))
            l3 = Line(l2 @ 1, l0 @ 0)
    make_face()

    with BuildLine():
            l0 = Line((-eye_w / 2 + eye_t, 0), (eye_w / 2 - eye_t, 0))
            l1 = Line(l0 @ 1, (eye_w / 2 - eye_t, eye_l- eye_t))
            l2 = ThreePointArc(l1 @ 1, (0.0, eye_l * 1.5 - eye_t), (-eye_w / 2 + eye_t, eye_l - eye_t))
            l3 = Line(l2 @ 1, l0 @ 0)
    make_face(mode=Mode.SUBTRACT)

with BuildPart() as base:
    with BuildSketch(Plane.XY):
        Rectangle(w, 2 * pic_h + t)
        with Locations((0, -t / 2)):
            add(pic, mode=Mode.SUBTRACT)
    extrude(amount=l)

    with BuildSketch(base.faces().sort_by(Axis.X)[0]):
        Circle((bolt["diameter"] + bolt_fit) / 2)
    extrude(amount=-w, mode=Mode.SUBTRACT)

    with BuildSketch(base.faces().sort_by(Axis.X)[-1]):
        RegularPolygon((nut["width"] / math.sqrt(3)), 6, rotation=360 / 6 / 2)
    extrude(amount=-nut["thickness"], mode=Mode.SUBTRACT)

    with BuildSketch(Plane.XY):
        with Locations(((w - eye_w) / 2, pic_h + t / 2)):
            add(eye)
    extrude(amount=eye_h)

    fillet(base.edges(Select.LAST).filter_by(Axis.X).group_by(Axis.Z)[-1], radius=(l - eye_h) / 1.5)
    edges = base.edges(Select.LAST).filter_by(Axis.Z).group_by(Axis.Y)[0].sort_by(Axis.X)
    fillet([edges[1], edges[2]], radius=eye_h/2)
    
    edges = base.edges().group_by(Axis.Z)[-1] + base.edges().group_by(Axis.Z)[0] + base.edges().group_by(Axis.Y)[0]
    chamfer(edges, length = t/4)
    fillet(base.edges().group_by(Axis.Y)[-1].sort_by(Axis.Z)[-1], radius = eye_t / 4)

    split(bisect_by=Plane.ZY.offset(pic_w0 / 2 - pic_diff / 2), keep=Keep.BOTH)

parts = base.solids()
clamp, base = parts[0], parts[1]
export_step(base, "picatinny-sling-base.step")
export_stl(base, "picatinny-sling-base.stl")
export_step(clamp, "picatinny-sling-clamp.step")
export_stl(clamp, "picatinny-sling-clamp.stl")
show_all()
