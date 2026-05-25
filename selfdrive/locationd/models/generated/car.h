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
void car_err_fun(double *nom_x, double *delta_x, double *out_1751486852151240052);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1850991408901040443);
void car_H_mod_fun(double *state, double *out_4081979560919394148);
void car_f_fun(double *state, double dt, double *out_436561100979424394);
void car_F_fun(double *state, double dt, double *out_212313505569631284);
void car_h_25(double *state, double *unused, double *out_6165914736993252692);
void car_H_25(double *state, double *unused, double *out_5111208664992843089);
void car_h_24(double *state, double *unused, double *out_168543763410584641);
void car_H_24(double *state, double *unused, double *out_7283858263998342655);
void car_h_30(double *state, double *unused, double *out_5509994110365947988);
void car_H_30(double *state, double *unused, double *out_1805481676498773666);
void car_h_26(double *state, double *unused, double *out_508320842705102343);
void car_H_26(double *state, double *unused, double *out_8852711983866899313);
void car_h_27(double *state, double *unused, double *out_7856362571728933652);
void car_H_27(double *state, double *unused, double *out_369281635301651245);
void car_h_29(double *state, double *unused, double *out_4218913043474911302);
void car_H_29(double *state, double *unused, double *out_2082644362171202278);
void car_h_28(double *state, double *unused, double *out_2657398259586607853);
void car_H_28(double *state, double *unused, double *out_7165043379240732852);
void car_h_31(double *state, double *unused, double *out_1727024757891270667);
void car_H_31(double *state, double *unused, double *out_5080562703115882661);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}