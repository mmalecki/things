use <raiser.scad>;
include <parameters.scad>;

e = 0;

raiser();
translate([0, 0, raiser_h + e])
  raiser_pad();
