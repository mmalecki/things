import math
import cadquery as cq
from ocp_vscode import *
import cq_queryabolt as queryabolt
from workplane import Workplane
set_defaults(reset_camera=Camera.CENTER)


fit = 0.2

bolt = "M3"

h = 25
t = 4
mag_t = 21.5
middle_t = 2 * t

def coupler():
    c = Workplane("XY")
    c = (c
               .move(0, -3 * t)
               .line(-middle_t / 2, 0)
               .line(0, 3 * t)
               .line(-mag_t, 0)
               .line(0, -t * 1.25)
               .line(-t, 2.25 * t)
               .line(t + mag_t, 0)
               .line(0, t / 2)
               .line(middle_t / 2, 0)
               # .close())
               .mirrorY())
    c = c.extrude(h).edges(">X or <X").fillet(t / 2)
    c = c.edges("|Z").edges("(>>X[2] or <<X[2]) or (>>X[3] or <<X[3])").edges(">>Y[1] or >>Y[2]").fillet(t / 8)
    c = c.edges("|Z").edges(">>Y").fillet(t / 4)
    c = c.edges("|Z").edges("<<Y[2]").fillet(t / 3)
    c = c.edges("|Z").edges("<<Y").fillet(t / 4)
    c = c.faces(">Z or <Z").edges().chamfer(t / 8)
    return c

def coupler_bolts():
    c = coupler()
    c = c.faces(">Y").workplane(centerOption="CenterOfBoundBox").rarray(1, h / 3, 1, 3).cboreBoltHole(bolt, clearance=fit)
    return c

def coupler_nuts():
    c = coupler()
    c = c.faces(">Y").workplane(centerOption="CenterOfBoundBox").tag("work").rarray(1, h / 3, 1, 3).nutcatchParallel(bolt)
    c = c.workplaneFromTagged("work").rarray(1, h / 3, 1, 3).boltHole(bolt, clearance=fit)
    return c


bolts = coupler_bolts()
nuts = coupler_nuts().translate((0, 10 * t, 0))
bolts.export("p90-magazine-coupler-bolts.step")
bolts.export("p90-magazine-coupler-bolts.stl")
nuts.export("p90-magazine-coupler-nuts.step")
nuts.export("p90-magazine-coupler-nuts.stl")
show_all()
