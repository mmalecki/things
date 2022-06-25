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

module raiser () {
  difference () {
    union () {
      cube([leg_d, leg_d, raiser_h]);

      translate([(leg_d - catch_w + catch_fit) / 2, 0, raiser_h])
        cube([catch_w - catch_fit, leg_d, catch_h - catch_fit]);

      translate([0, (leg_d - catch_w + catch_fit) / 2, raiser_h])
        cube([leg_d, catch_w - catch_fit, catch_h - catch_fit]);
    }
    translate([0, 0, -screw_length + raiser_h + pad_h])
      bolt_set(screw_length);
  }
}

module raiser_pad () {
  difference () {
    cube([leg_d, leg_d, pad_h]);

    translate([0, 0, -screw_length + pad_h])
      bolt_set(screw_length);

    translate([(leg_d - catch_w) / 2, 0, 0])
      cube([catch_w, leg_d, catch_h]);

    translate([0, (leg_d - catch_w) / 2, 0])
      cube([leg_d, catch_w, catch_h]);
  }
}
