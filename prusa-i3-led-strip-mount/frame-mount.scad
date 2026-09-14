use <catchnhole/catchnhole.scad>;
use <frame-holder/frame-holder.scad>;
include <parameters.scad>;

module frame_mount () {
  frame_holder(frame_holder_w, thickness = frame_holder_t);
  frame_holder_to_bottom(frame_holder_t) {
      translate([0, sin(-angle) * frame_holder_t, extruder_clearance]) {
        rotate([-angle, 0, 0]) {
          difference () {
            translate([-frame_holder_w / 2, 0])
              cube([frame_holder_w, frame_strip_mount_w, frame_holder_t]);

            translate([0, frame_strip_mount_w - nut_wall_d / 2, frame_holder_t]) {
              rotate([180, 0, 0]) {
                nutcatch_parallel(bolt);
                bolt(bolt, length=frame_holder_t);
              }
            }
          }
        }
      }
  }
}

frame_mount();
