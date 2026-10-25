#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_err_fun(double *nom_x, double *delta_x, double *out_1176760182641486560);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_2893373232090748310);
void car_H_mod_fun(double *state, double *out_2729823001511069589);
void car_f_fun(double *state, double dt, double *out_3238847108558356862);
void car_F_fun(double *state, double dt, double *out_5580812693562028107);
void car_h_25(double *state, double *unused, double *out_2449360683753057772);
void car_H_25(double *state, double *unused, double *out_7633514826695734429);
void car_h_24(double *state, double *unused, double *out_2915476860142765873);
void car_H_24(double *state, double *unused, double *out_7236869522341874934);
void car_h_30(double *state, double *unused, double *out_4267442820011222133);
void car_H_30(double *state, double *unused, double *out_3896538905522200432);
void car_h_26(double *state, double *unused, double *out_1230656768566889448);
void car_H_26(double *state, double *unused, double *out_7508703277253016586);
void car_h_27(double *state, double *unused, double *out_5053766004561755423);
void car_H_27(double *state, double *unused, double *out_6071302217322625343);
void car_h_29(double *state, double *unused, double *out_5210952672912884568);
void car_H_29(double *state, double *unused, double *out_7784664944192176376);
void car_h_28(double *state, double *unused, double *out_5957834634719095380);
void car_H_28(double *state, double *unused, double *out_5579680112447844666);
void car_h_31(double *state, double *unused, double *out_8116110739202444659);
void car_H_31(double *state, double *unused, double *out_7664160788572694857);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}