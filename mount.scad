$fn = 200;
t = 3.2;
// How far "out", away from the printer, the arm should reach.
out = 40;
// How far "up" the arm should reach.
up = 50;
extrusion = 30;
w = 35;

camera_bolt_offset = 7.2;
camera_mount_t = 6.21;
camera_mount_h = 25;
frame_bolt = "M3";
camera_bolt = "M4";

use <catchnhole/catchnhole.scad>;

support_t = 2 * t;
module arm () {
  w_base = t * 2 + camera_mount_t;

  difference () {
    linear_extrude (w) {
      square([t, extrusion]);
      translate([0, extrusion - t]) {
        square([out, t]);

        translate([t, 0])
          polygon([
            [0, 0],
            [0, -support_t],
            [support_t, 0]
          ]);

        translate([out - t, 0]) {
          translate([0, t])
            polygon([
              [0, 0],
              [0, support_t],
              [-support_t, 0]
            ]);

          difference () {
            hull () {
              square([t, up]);

              translate([0, up]) {
                translate([-t / 2 -camera_mount_t / 2, 0])
                  square([t, camera_mount_h]);

                translate([t / 2 + camera_mount_t / 2, 0])
                  square([t * 2, camera_mount_h]);
              }
            }
            translate([0, up]) 
              translate([-t / 2, 0])
                square([camera_mount_t, camera_mount_h]);
          }
        }
      }
    }

    for (spot = [1/4, 3/4]) {
      translate([0, extrusion / 2, w * spot]) {
        rotate([0, 90, 0])
          bolt(frame_bolt, length = 10);
      }
    }

    translate([out + (camera_mount_t + t) / 2 + t, up + extrusion + camera_bolt_offset - t, w / 2]) {
      rotate([0, 270, 0]) {
        nutcatch_parallel(camera_bolt);
        bolt(camera_bolt, length = 3 * t + camera_mount_t);
      }
    }
  }
}

arm();
