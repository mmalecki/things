import cadquery as cq
import cq_queryabolt

mountBolt = "M5"
psuBolt = "M4"
psuBoltD = cq_queryabolt.boltData(psuBolt)["diameter"] 

t = 5
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

mountEdge = cq_queryabolt.boltData(mountBolt)["diameter"] + 2 * t
mountW =supplyW + looseFit + 2 * t + 2 * mountEdge

coverT = t/2
coverBoltWall = psuBoltD+ coverT 
coverL = supplyMountSideFrontS+ coverBoltWall + coverT + looseFit + cableFrontClearance

def mount():
    h = supplyH + looseFit + t + supplyTopClearance
    m = Workplane("XY").rect(mountW, mountEdge).extrude(h)
    m = m.faces(">Z").workplane().rect(supplyW + looseFit, mountEdge).cutBlind(-h + t)

    m = m.faces("<Z").workplane(centerOption="CenterOfBoundBox").tag("bottom").rarray(supplyW + looseFit + 2 * t + mountEdge, 1, 2, 1).cboreBoltHole(mountBolt, clearance = looseFit)

    m = m.faces(">X").workplane(centerOption="CenterOfBoundBox").move(0, -h/2 + t + supplyMountSideBottomS).boltHole(psuBolt)
    m = m.workplaneFromTagged("bottom").rarray(supplyW + looseFit + 2 * t + mountEdge, 1, 2, 1).rect(mountEdge, mountEdge).cutBlind(-h + t)

    m = m.workplaneFromTagged("bottom").rarray(supplyMountS, 1, 2, 1).boltHole(psuBolt, clearance = looseFit)

    # debug(m.faces(">Z").edges("|Y ").fillet(t/2))
    m = m.faces(">Z or <Z or >Z[1] or >Z[2]").edges("|Y and (not (>Z and (>>X or <<X)))").fillet(t / 2)
    m = m.faces(">Y or <Y").chamfer(t / 3)
    return m

def coverPanel():
    w = supplyW + looseFit + 2 * t + 2 * coverT
    l =coverL
    h = supplyH + looseFit + coverT

    p = Workplane("XY").rect(w,l).extrude(h)
    p = p.faces(">Y").workplane(centerOption="CenterOfBoundBox").move(0, -coverT / 2).rect(supplyW + looseFit + 2 * t, supplyH + looseFit).cutBlind(-l + coverT)
    p = p.faces(">X").workplane(centerOption="CenterOfBoundBox").move((l) / 2 - coverBoltWall / 2, -h/2 + supplyMountSideBottomS).boltHole(psuBolt)
    p = p.faces(">Z").workplane(centerOption="CenterOfBoundBox").move(0, l / 2).rect(w - 2 * coverT, mountEdge * 2).cutThruAll()

    # Extruding a wholly new thing here is easier than dealing with center
    # offsets throughout this entire part.
    panelW = switchW + socketClearance + 4 * coverT
    panelH = max(switchH, socketH) + 2 * coverT
    panelD = l * 1.5 # Leave space for cables, mounting to the side, etc.

    p.faces(">X").workplane(centerOption="CenterOfBoundBox").tag("panelSide").end()
    p = p.workplaneFromTagged("panelSide").move((panelD - l)/ 2, -(panelH - h)/ 2).rect(panelD, panelH).extrude(panelW + coverT)

    p = p.faces("<Z").workplane(centerOption="CenterOfBoundBox").move(-coverT / 2, 0).rect(panelW, panelD - 2 * coverT).cutBlind(-panelH + coverT)

    p = p.workplaneFromTagged("panelSide").move(0, -coverT / 2).circle(h / 2 - 2 * coverT).cutBlind(until="next")

    # Socket and switch cutouts
    p = p.faces("<Y").workplane(centerOption="CenterOfBoundBox").center((w -  coverT) / 2, -coverT / 2).tag("panelFront").end()

    # Socket
    p = p.workplaneFromTagged("panelFront").center(-switchW / 2 - coverT, 0).tag("socket").rect(socketW, socketH).cutBlind(until="next")
    p = p.workplaneFromTagged("socket").rarray(socketMountS, 1, 2, 1).boltHole("M3", clearance = fit, depth=coverT)
    # Switch
    p = p.workplaneFromTagged("panelFront").move(socketClearance / 2 + coverT, 0).rect(switchW, switchH).cutBlind(until="next")

    p = p.faces("<Y or >Y").edges(">X or <X").chamfer(coverT / 2)
    p = p.faces(">Z").chamfer(coverT / 3)

    return p

show_object(mount(), name="mount")
show_object(coverPanel().translate((0, -coverL / 2 + coverT / 2 + psuBoltD / 2, t)), name="coverPanel")
