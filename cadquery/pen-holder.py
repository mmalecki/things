"""Parameteric magnetic pen holder/generic bin for fridges, whiteboards, etc."""
import math
import cadquery as cq
from ocp_vscode import *
set_port(3939)
set_defaults(reset_camera=False)


wallT = 2      # Wall thickness
d = 20         # Depth - this should cover all but the biggest markers
h = 75         # Height

fit = 0.1   # Magnet fit
magnetH = 5 # Magnet height
magnetD = 5 # Magnet diameter

def holder(width):
    dt = d + 2 * wallT
    hold = cq.Workplane("XY").rect(width + 2 * wallT, dt).extrude(h + wallT)

    # This fillets the front of the shape. If you want a more generic "bin" shape,
    # you can comment it out.
    hold = hold.edges(">Y and |Z").fillet(d / 2)

    hold = hold.faces("+Z").shell(-wallT)

    hold = hold.faces("<Y").workplane(centerOption="CenterOfBoundBox").rect(width + 2 * wallT, h + wallT).extrude(magnetH)

    m2 = (magnetD + fit) * 2 
    hold = hold.faces("<Y").workplane(centerOption="CenterOfBoundBox").rarray(m2, m2, math.ceil(width / m2) - 1, math.ceil(h / m2) - 1).hole(magnetD + fit, magnetH)

    hold = hold.faces("<Z[1]").fillet(wallT)
    hold = hold.faces(">Z").chamfer(wallT / 4)
    hold = hold.faces("<Z").chamfer(wallT / 2)

    hold = hold.edges("<Y and %Circle").chamfer(magnetD / 8)

    return hold

hold = holder(90) # 90 mm opening for 4 pens, 94 mm wide in total
hold.export("pen-holder-4-pens.step")
hold.export("pen-holder-4-pens.stl")

hold = holder(67.5) # 3 pens
hold.export("pen-holder-3-pens.step")
hold.export("pen-holder-3-pens.stl")

show(hold)
