use <common.scad>;
include <parameters.scad>;

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

raiser();
