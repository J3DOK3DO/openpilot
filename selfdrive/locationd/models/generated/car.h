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
void car_err_fun(double *nom_x, double *delta_x, double *out_9081917749595232587);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1988639049671275534);
void car_H_mod_fun(double *state, double *out_7384273333574390060);
void car_f_fun(double *state, double dt, double *out_853161238105894931);
void car_F_fun(double *state, double dt, double *out_6707016052586639669);
void car_h_25(double *state, double *unused, double *out_2381998967459310187);
void car_H_25(double *state, double *unused, double *out_758660054421155);
void car_h_24(double *state, double *unused, double *out_8300475326001007063);
void car_H_24(double *state, double *unused, double *out_3981564491343346743);
void car_h_30(double *state, double *unused, double *out_8301479849429568988);
void car_H_30(double *state, double *unused, double *out_6917449001546037910);
void car_h_26(double *state, double *unused, double *out_2889120507186530919);
void car_H_26(double *state, double *unused, double *out_3305284629815221756);
void car_h_27(double *state, double *unused, double *out_8629601671821540616);
void car_H_27(double *state, double *unused, double *out_4742685689745612999);
void car_h_29(double *state, double *unused, double *out_8904795734106046505);
void car_H_29(double *state, double *unused, double *out_3029322962876061966);
void car_h_28(double *state, double *unused, double *out_6025196351012842965);
void car_H_28(double *state, double *unused, double *out_2053076054193468608);
void car_h_31(double *state, double *unused, double *out_4388836258891040749);
void car_H_31(double *state, double *unused, double *out_7077433910566238408);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}