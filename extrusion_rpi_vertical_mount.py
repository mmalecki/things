import cadquery as cq
from ocp_vscode import show_all, set_defaults, Camera
import cq_queryabolt as queryabolt
from workplane import Workplane

set_defaults(reset_camera=Camera.KEEP)

# Source: official Raspberry Pi 4 mechanical drawing
# (datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf).
pi_dims = (85.0, 56.0)            # mm, board edges (along x, along y)
pi_hole_spacing = (58.0, 49.0)    # mm, mounting hole spacing (along x, along y)
pi_hole_inset = (3.5, 3.5)        # mm, first hole offset from the board's (0,0) corner

wall_t = 3.2                      # mm, bracket backbone thickness
bolt = "M2.5"
bolt_spacing = pi_hole_spacing[1]
extrusion_bolt = "M4"

nut = queryabolt.nutData(bolt)
taper_h = 20
ext_d = 20
nut_wall_d = nut["width"] + wall_t
nut_hole_h = nut["thickness"] + wall_t 

fit = 0.1
bolt_fit = 0.2

def mount():
    top_w = bolt_spacing + nut_wall_d
    top_h = nut_wall_d
    bot_w = ext_d + 2 * wall_t + fit
    ext_plane_d = queryabolt.boltData(extrusion_bolt)["diameter"] + 2.5 * wall_t
    profile = (
        cq.Sketch()
        .segment((0, top_h + taper_h), (-top_w / 2, top_h + taper_h))
        .segment((-top_w / 2, taper_h))
        .segment((-bot_w / 2, 0))
        .segment((0, 0))
        .segment((bot_w / 2, 0))
        .segment((top_w / 2, taper_h))
        .segment((top_w / 2, top_h + taper_h))
        .close()
        .assemble()
    )
    m = Workplane("XZ").placeSketch(profile).extrude(wall_t)
    m = m.faces(">Y").workplane().tag("front").end()
    m = m.workplaneFromTagged("front").placeSketch(profile.copy().wires().offset(-top_h - wall_t / 4, mode='r')).cutThruAll()

    m = m.workplaneFromTagged("front").transformed(offset=(0, taper_h + top_h / 2)).rarray(top_w - nut_wall_d, 1, 2, 1).rect(nut_wall_d, top_h).extrude(max(0, nut_hole_h - wall_t))
    m = m.faces(">Y").workplane(centerOption="CenterOfBoundBox").rarray(bolt_spacing, 1, 2, 1).circle(2.5).extrude(wall_t)

    m = m.faces("<Y").workplane().tag("back").end()
    m = m.workplaneFromTagged("back").rarray(bolt_spacing, 1, 2, 1).nutcatchParallel(bolt)
    m = m.workplaneFromTagged("back").rarray(bolt_spacing, 1, 2, 1).boltHole(bolt, clearance=bolt_fit)

    m = m.workplaneFromTagged("front").move(0, wall_t / 2).rect(bot_w, wall_t).extrude(ext_plane_d)

    m = m.faces("<Z").workplane(centerOption="CenterOfBoundBox").tag("ext_mate").end()
    m = m.faces("<Z").workplane().move(0, -ext_plane_d / 2).boltHole(extrusion_bolt, clearance=bolt_fit)
    # Mount fingers
    m = m.faces("<Z").workplaneFromTagged("ext_mate").move((bot_w - wall_t) / 2, 0).rect(wall_t, ext_plane_d + wall_t).extrude(ext_plane_d + wall_t)
    m = m.faces("<Z").workplaneFromTagged("ext_mate").move(-(bot_w - wall_t) / 2, 0).rect(wall_t, ext_plane_d + wall_t).extrude(wall_t)

    m = m.faces("<X[4]").workplane(centerOption="CenterOfBoundBox").move(0, -wall_t * 1.25).boltHole(extrusion_bolt, clearance=bolt_fit)

    m = m.faces(">Y").fillet(wall_t / 2.5)
    m = m.faces(">Y[2]").edges().fillet(wall_t / 3)
    m = m.faces(">Y[3]").edges().fillet(wall_t / 6)
    m = m.faces("<Y").edges().chamfer(wall_t / 6)
    m = m.faces("(<Z or >Z[1])").edges("not <Y").fillet(wall_t / 3)
    return m

mount_ = mount()
show_all()

cq.exporters.export(mount_, "extrusion-rpi-vertical-mount.step")
cq.exporters.export(mount_, "extrusion-rpi-vertical-mount.stl", tolerance=0.01, angularTolerance=0.1)
