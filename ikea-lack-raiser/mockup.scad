use <raiser.scad>;
use <raiser-pad.scad>;
include <parameters.scad>;

e = 1;

raiser();
translate([0, 0, raiser_h + e])
  raiser_pad();
