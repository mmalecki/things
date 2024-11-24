use <common.scad>;
include <parameters.scad>;

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

raiser_pad();
