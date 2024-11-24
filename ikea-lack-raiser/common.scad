use <catchnhole/catchnhole.scad>;
include <parameters.scad>;

module bolt_ (h) {
  bolt(
    screw,
    length = h,
    kind = "countersunk",
    countersink = 2,
    head_diameter_clearance = 0.2
  );
}

module bolt_set (h) {
  // The actual bolt:
  translate([leg_d / 2, leg_d / 2]) bolt_(h);
  // The filament-saving/alternate bolts:
  translate([leg_d * 1/4, leg_d * 1/4]) bolt_(h);
  translate([leg_d * 3/4, leg_d * 3/4]) bolt_(h);
  translate([leg_d * 1/4, leg_d * 3/4]) bolt_(h);
  translate([leg_d * 3/4, leg_d * 1/4]) bolt_(h);
}
