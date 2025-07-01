import cadquery as cq
import cq_queryabolt
from ocp_vscode import *
set_defaults(reset_camera=False)

psuBolt = "M4"
psuBoltD = cq_queryabolt.boltData(psuBolt)["diameter"] 

t = 2
fit = 0.2
looseFit = 0.5

# https://www.meanwell.com/productPdf.aspx?i=435
supplyH = 30
supplyW = 115
supplyMountS = 50
supplyMountSideBottomS = 12.8
supplyMountSideFrontS = 32.5
supplyTopClearance = 10
cableFrontClearance = 20

switchW = 22.5
switchH = 30.8

# https://eu.mouser.com/datasheet/2/4/iec_a_1_data_sheet-3396157.pdf
socketW = 27
socketH = 19.8
socketMountS = 40
socketClearance = 50

class Workplane(cq.Workplane, cq_queryabolt.WorkplaneMixin):
    pass

coverBoltWall = psuBoltD+ t * 2
socketCoverL = supplyMountSideFrontS+ coverBoltWall + t + looseFit + cableFrontClearance

coverBolt= "M3"
coverBoltHeatsetD = 4.0

def socketSide():
    w = supplyW + fit + socketClearance + 3 * t
    l = socketCoverL
    h = supplyH + fit + t

    # Extrude the whole thing, then make cut-outs for the PSU,
    # socket, etc.
    p = Workplane("XY").rect(w, l).extrude(h)

    # First, make the PSU cut-out. We're cutting this one out from the bottom, as
    # that's how the PSU will slide in.
    p = p.faces("<Z").workplane(centerOption="CenterOfBoundBox").tag("bottom").end()
    psuS = (w - supplyW - fit) / 2 - t
    p = p.workplaneFromTagged("bottom").move(psuS, -t / 2).rect(supplyW + fit, socketCoverL - t).cutBlind(-(h - t))

    # Make the socket cut-out from behind.
    p = p.faces(">Y").workplane(centerOption="CenterOfBoundBox").tag("back").end()
    p = p.workplaneFromTagged("back").center((w - socketClearance) / 2 - t, 0).tag("socket").rect(socketClearance, h - 2 * t).cutBlind(-(socketCoverL - t))
    p = p.workplaneFromTagged("socket").rect(socketW, socketH).cutThruAll()
    p = p.workplaneFromTagged("socket").rarray(socketMountS, 1, 2, 1).boltHole("M3", clearance = fit)

    # PSU bolt
    psuBoltS = l / 2 - coverBoltWall
    psuBoltH = (h - fit) /2 - t - supplyMountSideBottomS
    # Access hole:
    p = p.faces("<X").workplane(centerOption="CenterOfBoundBox").move(-psuBoltS - psuBoltD, psuBoltH).slot2D(coverBoltWall + 2 * psuBoltD, 2 * psuBoltD,).cutBlind(until="next")
    # The actual bolt:
    p = p.faces(">X").workplane(centerOption="CenterOfBoundBox").move(psuBoltS, psuBoltH).boltHole(psuBolt, clearance = fit)

    # Cable pass-through:
    p = p.faces("<X[2]").workplane(centerOption="CenterOfBoundBox").move(-socketCoverL / 2 + t / 2+ cableFrontClearance/ 2, 0).rect(cableFrontClearance, h - 4 * t).cutBlind(until="next")

    # Save some filament
    p = p.faces(">Z").workplane(centerOption="CenterOfBoundBox").move(psuS, l / 2).slot2D(supplyW * 4/5, 2 * (l - cableFrontClearance - t)).cutThruAll()

    p = (p.faces("<Z[1]").workplane().move((socketClearance + supplyW + t + fit - coverBoltWall)/ 2, (l - coverBoltWall) / 2 - t).rect(coverBoltWall, coverBoltWall).circle(coverBoltHeatsetD / 2).extrude(supplyH / 2))

    p = p.edges("not %Circle").chamfer(t / 5)

    return p

def switchSide():
    w = supplyW + fit + socketClearance + 3 * t
    l = supplyMountSideFrontS + coverBoltWall + t + looseFit 
    h = supplyH + fit + t

    # Extrude the whole thing, then make cut-outs for the PSU,
    # socket, etc.
    p = Workplane("XY").rect(w, l).extrude(h)

    # First, make the PSU cut-out. We're cutting this one out from the bottom, as
    # that's how the PSU will slide in.
    p = p.faces("<Z").workplane(centerOption="CenterOfBoundBox").tag("bottom").end()
    psuS = (w - supplyW - fit) / 2 - t
    p = p.workplaneFromTagged("bottom").move(psuS, t / 2).rect(supplyW + fit, l - t).cutBlind(-(h - t))

    # Make the switch cut-out from behind.
    p = p.faces("<Y").workplane(centerOption="CenterOfBoundBox").tag("back").end()
    p = p.workplaneFromTagged("back").center(-(w - socketClearance) / 2 + t, 0).tag("socket").rect(socketClearance, h - 2 * t).cutBlind(-l + t)
    p = p.workplaneFromTagged("socket").rect(switchH, switchW).cutThruAll()

    # PSU bolt
    psuBoltS = -l / 2 + coverBoltWall
    psuBoltH = (h - fit )/2- t - supplyMountSideBottomS
    # Access hole:
    p = p.faces("<X").workplane(centerOption="CenterOfBoundBox").move(-psuBoltS + psuBoltD, psuBoltH).slot2D(coverBoltWall + 2 * psuBoltD, 2 * psuBoltD,).cutBlind(until="next")
    # The actual bolt:
    p = p.faces(">X").workplane(centerOption="CenterOfBoundBox").move(psuBoltS, psuBoltH).boltHole(psuBolt, clearance = fit)

    # Save some filament
    p = p.faces(">Z").workplane(centerOption="CenterOfBoundBox").move(psuS, -l / 2 - t).slot2D(supplyW * 4/5, l * 7/4).cutThruAll()
    p = p.workplaneFromTagged("back").move(psuS, 0).slot2D(supplyW * 4/5, supplyH / 4).cutThruAll()

    p = p.edges("not %Circle").chamfer(t / 4)

    return p

def cover():
    supplyWallT = 2.4
    supplyTerminalL = 14
    cableClearanceW = 60
    cableClearanceL = cableFrontClearance * 3/4
    w = supplyW - fit
    l = cableFrontClearance + supplyTerminalL - fit
    c = Workplane("XY").rect(w, l).extrude(t)

    # The post
    c = c.faces(">Z").workplane().move(w / 2 - coverBoltWall / 2, -l / 2 + coverBoltWall / 2).rect(coverBoltWall, coverBoltWall).extrude(supplyH / 2 - t - fit)
    # Its bolt hole
    c = c.faces(">Z").workplane(centerOption="CenterOfBoundBox").boltHole(coverBolt, clearance=fit)

    # Supply wall clearance
    c = c.faces("<Z").workplane(centerOption="CenterOfBoundBox").center(0,-cableFrontClearance/ 2).rarray(w, 1, 2, 1).rect(supplyWallT * 2, l - cableFrontClearance + fit).cutThruAll()
    c = c.faces("<Z").workplane(centerOption="CenterOfBoundBox").move(0,l/ 2 - cableClearanceL/2).rect(cableClearanceW, cableClearanceL).cutThruAll()
    c = c.edges("not %Circle").chamfer(t / 3)
    return c

# show_object(mount(), name="mount")
socketSide_ = socketSide()
socketSide_.export("socket.step")
show_object(socketSide_, name="socketSide")

switchSide_ = switchSide()
switchSide_.export("switch.step")
show_object(switchSide_.translate((0, socketCoverL)), name="switchSide")

cover_ = cover()
cover_.export("cover.step")
show_object(cover_.translate(((socketClearance + t) / 2, 0, -supplyH/2)), name="cover")

