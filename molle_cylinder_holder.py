from build123d import *
from ocp_vscode import *
import cq_queryabolt as queryabolt

import molle_backplate

fastener = "M3"

bolt = queryabolt.boltData(fastener)
nut = queryabolt.nutData(fastener)

fit = 0.2
loose_fit = 0.5
t = 4

molle_w = molle_backplate.molle_w
molle_h = molle_backplate.molle_h
molle_fit = molle_backplate.molle_fit
molle_plate_w = molle_backplate.molle_plate_w

cord_d = 6 + loose_fit
cord_od = cord_d + 1.5 * t

def holder():
    h_slots = 5
    w_mm = molle_plate_w + 2 * cord_od
    h_mm = h_slots * molle_h - molle_fit + t

    with BuildPart() as plate:
        y = cord_od /2 - (cord_od - cord_d) / 4

        with BuildSketch(Plane.XZ) as sk:
            Rectangle(w_mm, h_mm)

            with Locations((0, -t / 2)):
                with GridLocations(molle_w, molle_h * 2, 1, h_slots - 2):
                    Circle((bolt["diameter"] + fit) / 2, mode=Mode.SUBTRACT)
                with GridLocations(molle_w - t - cord_d, (h_mm  - t)/ 4, 2, 4):
                    Circle(cord_d / 2, mode=Mode.SUBTRACT)
        extrude(amount=t)

        with BuildSketch(Plane.XZ):
            with Locations((0, h_mm / 2 - t / 2)):
                Rectangle(w_mm, t)
        extrude(amount=4 * t)
        by_x_y = plate.edges(Select.LAST).filter_by(Axis.X).group_by(Axis.Y)
        fillet([by_x_y[1]], radius=t)
        fillet([by_x_y[0]], radius=t/3)

        by_y = plate.edges().group_by(Axis.Y)
        by_x = plate.edges().group_by(Axis.X)
        chamfer([by_y[-1].filter_by(GeomType.LINE), by_x[0], by_x[-1]], length=t / 3)

    return plate

holder_ = holder()
show(holder_)
export_step(holder_.part, "grenade-holder.step")
