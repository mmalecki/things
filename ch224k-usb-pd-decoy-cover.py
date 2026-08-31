# Note: this is for my own, very custom version of the PCB
# (with a XT30 output). It likely won't work for the stock PCB.
# Original designs can easily be measured and plugged in:
# https://oshwlab.com/wagiminator/ch224k-usb-pd-decoy (set `offset = 0`!)
import cadquery as cq
import cq_queryabolt as queryabolt
from ocp_vscode import Camera, set_defaults, show_all

from workplane import Workplane

set_defaults(reset_camera=Camera.KEEP)

l = 31.75
w = 20.32
m_w = 15.24
m_l = 25.4

mount_inset = 7.5
offset= -1.35

fit = 0.2

wall_t = 1.6
bolt = "M2"

# UCB connector (input)
usb_w = 9.5
usb_h = 3.65

# Power connector (output)
pwr_w = 10.5
pwr_h = 5

# PCB
pcb_t = 1.6
pcb_h = pwr_h # Max component height

s = cq.Sketch().rect(w + 2*wall_t, l+2 * wall_t).vertices().fillet(wall_t / 2)

def bottom():
    c = Workplane("XY").placeSketch(s).extrude(wall_t * 2)
    c = c.faces(">Z").workplane().move(0, mount_inset/2).rect(w + fit, l + fit -mount_inset).cutBlind(-wall_t)
    c = c.faces(">Z").workplane().placeSketch(s.copy()).extrude(pcb_t)
    c = c.faces(">Z").workplane().rect(w + fit, l + fit).cutBlind(-pcb_t)
    c = c.faces(">Z").workplane().center(0, offset).rarray(m_w, m_l, 2, 2).boltHole(bolt, clearance=-fit)
    return c

def top():
    c = Workplane("XY").placeSketch(s).extrude(2 * wall_t)

    c = c.faces("<Z").workplane().placeSketch(s.copy()).extrude(pcb_h)
    c = c.faces("<Z").workplane().rect(w + fit, l + fit).cutBlind(-pcb_h)
    c = c.faces("<Z").workplane().move(0, l / 2 + wall_t / 2).rect(usb_w, wall_t).cutBlind(-usb_h)
    c = c.faces("<Z").workplane().move(0, -(l / 2 + wall_t / 2)).rect(pwr_w, wall_t).cutBlind(-pwr_h)
    c = c.faces(">Z[1]").edges(">X or <X").fillet(wall_t / 2)
    c = c.faces(">Z[2]").edges("|Y").edges("(>X or <X) or (>>X[1] or <<X[1])").fillet(wall_t / 2)
    c = c.faces(">Z").workplane().center(0, offset).rarray(m_w, m_l, 2, 2).cboreBoltHole(bolt, clearance=fit)
    return c

bottom_ = bottom()
top_ = top().translate((0, 0, 20))
show_all()

cq.exporters.export(bottom_, "ch224k-usb-pd-decoy-bottom.step")
cq.exporters.export(top_, "ch224k-usb-pd-decoy-top.step")
