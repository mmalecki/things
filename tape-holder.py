"""Parameteric magnetic tape holder/generic hook for fridges, whiteboards, etc."""
import math
import cadquery as cq
from ocp_vscode import *
set_port(3939)
set_defaults(reset_camera=False)


wallT = 2 # Wall thickness

fit = 0.1   # Magnet fit
magnetH = 5 # Magnet height
magnetD = 5 # Magnet diameter

hookW = 12.5 # Width of the hook
hookL = 40 # Length of the hook

stopH = 2 * wallT # Height of the stopper at the end

def holder():
    m2 = (magnetD + fit) * 2 
    holderH = 4 * m2
    h = magnetH + wallT
    hold = cq.Workplane("XY").rect(hookW, holderH).extrude(h)

    m2 = (magnetD + fit) * 2 
    hold = hold.faces("<Z").workplane(centerOption="CenterOfBoundBox").rarray(m2, m2, math.ceil(hookW / m2) - 1, math.ceil(holderH / m2) - 1).hole(magnetD + fit, magnetH)

    hold = hold.faces(">Z").edges("<Y").workplane(centerOption="CenterOfBoundBox").move(0, wallT / 2).rect(hookW, wallT).extrude(hookL + wallT)
    hold = hold.faces("<Y[1]").workplane(centerOption="CenterOfBoundBox").move(0, hookL / 2).rect(hookW, wallT).extrude(stopH)

    hold = hold.faces("<Z").edges("<Y or >Y").fillet(h / 3)
    hold = hold.faces(">Z").edges("<Y").fillet(h / 3)
    hold = hold.faces(">Z[3]").edges("<Y").fillet(h / 3)
    hold = hold.faces(">Z[2]").edges("<Y or >Y").fillet(h / 3)
    hold = hold.faces(">X or <X").chamfer(wallT / 4)
    hold = hold.edges("<Z and %Circle").chamfer(magnetD / 8)


    return hold

hold = holder()
hold.export("tape-holder.step")
hold.export("tape-holder.stl")
show(hold)
