include <../parameters.scad>;
use <../frame-mount.scad>;
use <../strip-mount.scad>;
use <../frame-holder/frame-holder.scad>;

// Between MMU mounts:
frame_mount_s = 90;

module full_assembly () {
  for (side = [-1, 1]) {
    translate([side * frame_mount_s / 2, 0])
      frame_mount();
  }

  frame_holder_to_bottom(frame_holder_t) {
    translate([0, sin(-angle) * frame_holder_t, extruder_clearance]) {
      rotate([-angle, 0, 0]) {
        difference () {
          translate([0, frame_strip_mount_w - nut_wall_d / 2, 0]) {
            rotate([0, 180, 0]) strip_mount();
          }
        }
      }
    }
  }
}

full_assembly();
