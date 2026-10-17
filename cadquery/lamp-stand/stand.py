import cadquery as cq

tightFit = 0.1
fit = 0.2
looseFit = 0.5

deskMountD = 7.5
lampMountD = 12.5

wallT = 5.0

padW = 45

mountL = 35
mountW = lampMountD + 2 * wallT
mountH = 3 * wallT + lampMountD + deskMountD
mountD = 3

padL = mountL + wallT + deskMountD
padW = mountW + 4 * wallT

def stand():
    stand = cq.Workplane("front").rect(padL, padW).extrude(wallT)
    stand = stand.edges("|Z").chamfer(padW / 8)
    stand = stand.edges("|Z").fillet(padW / 16)

    stand = stand.faces(">Z").workplane().tag("padTop")

    stand = stand.workplaneFromTagged("padTop").rarray(padL, 1, 2, 1).hole(deskMountD + fit)
    stand = stand.workplaneFromTagged("padTop").rect(mountL, mountW).extrude(mountH)
    stand = stand.workplaneFromTagged("padTop").rect(wallT, padW).extrude(mountH / 2)
    stand = (stand.faces(">Z[2]").edges(">Y or <Y").chamfer((padW - mountW) / 2 - 0.1))

    stand = stand.faces(">X[1]").workplane(centerOption="CenterOfBoundBox").tag("mount")
    stand = stand.workplaneFromTagged("mount").move(0, -mountH / 2 + deskMountD / 2 + wallT).hole(deskMountD)
    stand = stand.workplaneFromTagged("mount").move(0, mountH / 2 - lampMountD / 2 - wallT).hole(lampMountD)
    stand = stand.faces(">X[1] or <X[1]").edges("%Circle").fillet(wallT * 0.25)

    stand = stand.faces(">Z").workplane(centerOption="CenterOfBoundBox").tag("top")
    stand = stand.workplaneFromTagged("top").circle(lampMountD / 2).cutBlind(until="next")
    stand = stand.workplaneFromTagged("top").circle(mountW / 2).circle(lampMountD / 2).extrude(wallT)

    stand = (stand.edges(">Z[3]")).fillet(mountW / 8)
    stand = (stand.faces("<Z[1]").edges("%Circle").fillet(mountW * 0.1))
    stand = (stand.faces(">Z").edges(cq.selectors.RadiusNthSelector(1)).fillet(mountW * 0.1))
    stand = (stand.faces(">Z").edges(cq.selectors.RadiusNthSelector(0)).fillet(lampMountD * 0.1))
    stand = (stand.edges(">Z[1] or >>Z[4] or >>Z[6]").fillet(wallT * 0.25))
    stand = (stand.edges(">>Z[2]").fillet(wallT * 0.2))

    stand = stand.workplaneFromTagged("padTop").rect(padL - 4 * wallT, padW - 2 * wallT, forConstruction=True).vertices().hole(mountD)

    return stand

def padBase(t = wallT):
    pad = cq.Workplane("front").rect(padL, padW).extrude(t)
    pad = pad.edges("|Z").chamfer(padW / 8)
    pad = pad.edges("|Z").fillet(padW / 16)
    pad = pad.faces(">Z").workplane().tag("padTop")
    pad = pad.workplaneFromTagged("padTop").rarray(padL, 1, 2, 1).hole(deskMountD + fit)
    return pad

def pad():
    pad = padBase(wallT / 2)
    pad = pad.workplaneFromTagged("padTop").rect(padL - 4 * wallT, padW - 2 * wallT, forConstruction=True).vertices().hole(mountD)
    return pad


if 'show_object' in globals():
    stand_ = stand()
    pad_ = pad()
    show_object(stand_, name="stand")
    show_object(pad_.translate((0, 0, -2 * wallT)), name="pad")
