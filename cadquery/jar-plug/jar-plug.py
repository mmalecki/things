import cadquery as cq

t = 3
id = 47.5
h = 17.5

handleW = id * 9 / 10

def plug():
    p = cq.Workplane("XY").circle(id / 2).extrude(t)
    p = p.faces(">Z").workplane().tag("top").rect(handleW, t).extrude(h)
    # Shorter rib
    srW = id * 3/4
    p = p.workplaneFromTagged("top").rect(t, id * 3/4).extrude(h / 2)

    p = p.faces(">Z").edges(">X or <X").chamfer(min(h / 2, id / 4))
    p = p.faces("<Z[1]").edges(">Y or <Y or |X").chamfer(min(h / 4, srW / 8))
    p = p.faces(">Z[1]").edges("%Circle").fillet(((id - handleW) / 5))

    try:
        p = p.edges("|Z").fillet(t / 4)
        p = (p.faces(">Z[1]").edges("(not %Circle) and (|X or |Y) and (((not >X[0]) or (not <Y[1])))").fillet((id - handleW) / 5))
    except:
        log("Cosmetic filleting failed, moving on")

    return p

show_object(plug(), name="plug")
