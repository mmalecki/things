use <catchnhole/catchnhole.scad>;

$fn = 100;

press_fit = 0;
loose_fit = 0.5;

bolt_wall_d_min = 3.6;
bolt_wall_h_min = 1.6;

bolt = "M2";
nut_wall_d = nut_width_across_corners(bolt) + bolt_wall_d_min;
bolt_wall_d = bolt_data(bolt).diameter + bolt_wall_d_min;
nut_h = nut_height(bolt);

frame_holder_w = nut_wall_d;
frame_holder_t = 4;
angle = 27.5;

strip_mount_w = 10;
frame_clearance = 5;
extruder_clearance = 3.5;
frame_strip_mount_w = strip_mount_w + frame_clearance;
strip_l = 200;
