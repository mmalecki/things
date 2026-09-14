use <catchnhole/catchnhole.scad>;
use <frame-holder/frame-holder.scad>;
include <parameters.scad>;

module bolt_clearance () {
  hull () {
    for (side = [-1, 1]) {
      translate([side * (strip_l - bolt_wall_d) / 2, 0]) {
        bolt(bolt, length = bolt_wall_h_min);
      }
    }
  }
  translate([0, 0, bolt_wall_h_min])
    hull () {
      for (side = [-1, 1]) {
        translate([side * (strip_l - bolt_wall_d) / 2, 0]) {
          bolt_head(bolt, kind = "socket_head");
        }
      }
    }
}

module strip_mount () {
  h = bolt_head_length(bolt, kind = "socket_head") + bolt_wall_h_min;

  difference () {
    hull () {
      linear_extrude (h) {
        for (side = [-1, 1]) {
          translate([side * strip_l / 2 , 0]) {
            circle(d = strip_mount_w);
          }
        }
      }
    }

    bolt_clearance();
  }
}

strip_mount();
