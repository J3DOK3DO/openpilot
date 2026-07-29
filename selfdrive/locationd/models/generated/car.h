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
void car_err_fun(double *nom_x, double *delta_x, double *out_6104712207101523759);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_4901417542031613009);
void car_H_mod_fun(double *state, double *out_4051006717071082906);
void car_f_fun(double *state, double dt, double *out_3418974710290228612);
void car_F_fun(double *state, double dt, double *out_3699468657963228141);
void car_h_25(double *state, double *unused, double *out_7881868868211418241);
void car_H_25(double *state, double *unused, double *out_7573987367060574583);
void car_h_24(double *state, double *unused, double *out_6965493433416690101);
void car_H_24(double *state, double *unused, double *out_7314831107846653897);
void car_h_30(double *state, double *unused, double *out_5527754398725254445);
void car_H_30(double *state, double *unused, double *out_8354423748141728406);
void car_h_26(double *state, double *unused, double *out_4047826294150907485);
void car_H_26(double *state, double *unused, double *out_3832484048186518359);
void car_h_27(double *state, double *unused, double *out_7960469884689435724);
void car_H_27(double *state, double *unused, double *out_6130829676957785189);
void car_h_29(double *state, double *unused, double *out_4330826993179455763);
void car_H_29(double *state, double *unused, double *out_7844192403827336222);
void car_h_28(double *state, double *unused, double *out_8563785769365913241);
void car_H_28(double *state, double *unused, double *out_5520152652812684820);
void car_h_31(double *state, double *unused, double *out_6703191729069631723);
void car_H_31(double *state, double *unused, double *out_7604633328937535011);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}