import cadquery as cq
import cq_queryabolt as queryabolt

class Workplane(queryabolt.WorkplaneMixin, cq.Workplane):
    pass
