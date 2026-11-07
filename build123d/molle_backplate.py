from build123d import *
from ocp_vscode import *
from bd_buildabolt import BoltHole, NutcatchParallel, nut_data

fastener = "M3"

nut = nut_data(fastener)

molle_fit = 5
fit = 0.2

molle_w = 38
molle_plate_w = 20
molle_h = 25

def backplate(w, h, t = 4):
    w_mm = molle_plate_w * w
    h_mm = molle_h * (h) - molle_fit
    with BuildPart() as plate:
        with BuildSketch():
            Rectangle(w_mm, h_mm)
        extrude(amount=t)

        with BuildSketch(plate.faces().sort_by(Axis.Z)[-1]):
            with GridLocations(molle_w, molle_h * 2, w, h - 2):
                Rectangle(molle_plate_w, molle_h - molle_fit)
        extrude(amount=t)

        by_z = plate.edges().filter_by(GeomType.LINE).group_by(Axis.Z)
        fillet([by_z[-3], by_z[-2], by_z[-1]], radius=t / 3)
        chamfer(plate.faces().sort_by(Axis.Z)[0].edges(), length=t/3)

        with Locations(Plane(plate.faces().sort_by(Axis.Z)[0])):
            with GridLocations(molle_w, molle_h * 2, w, h - 2):
                BoltHole(fastener, depth=2 * t, clearance=fit)

        with Locations(Plane(plate.faces().sort_by(Axis.Z)[0])):
            with GridLocations(molle_w, molle_h * 2, w, h - 2):
                NutcatchParallel(nut, height_clearance=nut.thickness / 2)


    return plate

if __name__ == "__main__":
    backplate_ = backplate(1, 5)
    show(backplate_)
    export_step(backplate_.part, "molle-backplate-1-5.step")
