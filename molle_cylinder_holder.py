import math
from build123d import *
from ocp_vscode import *
import cq_queryabolt as queryabolt

import molle_backplate

set_defaults(reset_camera=Camera.KEEP)

fastener = "M3"

bolt = queryabolt.boltData(fastener, kind="countersunk")
nut = queryabolt.nutData(fastener)

fit = 0.2
loose_fit = 0.5
t = 3.2

molle_w = molle_backplate.molle_w
molle_h = molle_backplate.molle_h
molle_plate_w = molle_backplate.molle_plate_w

# Primary control variables
cyl_d = 58 + 2 * loose_fit # Diameter of the cylinder we're holding
cyl_hold_angle = 120 # Angular angle we want to hold onto

bottom_lip = True # Whether to create a bottom lip

side_t = t / 2 # How thick the sides should be

# Secondary control variables
# Cord dimensions
cord_d = 6 + 2 * loose_fit

# Whether to create "speed holes" for material usage reduction/draining/...
speed_holes = True

def holder():
    h_slots = 5 # 5 horizontal Molle slots in total

    chord = cyl_d * math.sin(math.radians(cyl_hold_angle / 2))
    sagitta = (cyl_d / 2) * (1 - math.cos(math.radians(cyl_hold_angle / 2)))

    w_mm = 2 * side_t + chord # Total width
    h_mm = h_slots * molle_h + t # Total height
    t_mm = sagitta + t
    cord_od = cord_d + 1.5 * t

    with BuildPart() as plate:
        # Shape of the holder itself
        with BuildSketch(Plane.XY) as sk:
            with BuildLine() as ln:
                l1 = Line((-w_mm / 2, -t_mm), (w_mm / 2, -t_mm))
                l2 = Line(l1 @ 1, (w_mm / 2, 0))
                l3 = Line(l2 @ 1, (w_mm / 2 - side_t, 0))
                l4 = RadiusArc(l3 @ 1, (-w_mm / 2 + side_t, 0), cyl_d / 2)
                l5 = Line(l4 @ 1, (-w_mm / 2, 0))
                l6 = Line(l5 @ 1, l1 @ 0)
            make_face()
        extrude(amount=h_mm / 2, both=True)

        # Bottom lip
        if bottom_lip == True:
            with BuildSketch(Plane.XY.offset(-h_mm / 2)):
                with Locations((0, -t_mm / 2)):
                    Rectangle(w_mm, t_mm)
            extrude(amount=t)
            fillet(plate.edges(Select.LAST).filter_by(GeomType.CIRCLE).group_by(Axis.Y)[0], radius=t/4)

        # Cord holders
        with BuildSketch(Plane.XZ):
            with GridLocations(w_mm + cord_od, h_mm / 4, 2, 4):
                Rectangle(cord_od, cord_od)
                Circle(cord_d / 2, mode=Mode.SUBTRACT)
        extrude(amount=t_mm)

        # ...and their fillets
        last = plate.edges(Select.LAST)
        fillet(last.filter_by(Axis.Y), radius=cord_od / 3)
        fillet(last.filter_by(GeomType.CIRCLE).group_by(Axis.Y)[-1], radius=cord_od / 8)

        # Chamfer back
        chamfer(plate.edges().group_by(Axis.Y)[0], length=t/3)
        # Chamfer front
        chamfer(plate.edges().group_by(Axis.Y)[-1], length=t/8)

        # Mounting holes
        with Locations(Plane.XZ.rotated((0, 0, 180))):
            with Locations((0, t/2 , -t_mm + t)):
                with GridLocations(molle_w, molle_h * 2, 1, h_slots - 2):
                    CounterSinkHole((bolt["diameter"] + fit) / 2, counter_sink_radius=(bolt["head_diameter"] + fit) / 2)

        # Speed holes
        if speed_holes:
            with BuildSketch(Plane.XZ):
                with Locations((0, t/2, -t_mm + t)):
                    with GridLocations(w_mm / 2, molle_h * 2, 2, 2):
                        SlotCenterToCenter(h_mm / 5, cord_d, 90)
            extrude(amount=t_mm, mode=Mode.SUBTRACT)
            chamfer(plate.edges(Select.LAST), length=t/4)

            fillet(plate.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], radius=t/4)
            fillet(plate.edges().filter_by(GeomType.LINE).filter_by(Axis.Y), radius=t/4)

    return plate

holder_ = holder()
show(holder_)
export_step(holder_.part, "molle-cylinder-elastic-cord-holder.step")
export_stl(holder_.part, "molle-cylinder-elastic-cord-stl.step")
