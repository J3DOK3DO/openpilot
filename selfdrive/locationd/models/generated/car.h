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
void car_err_fun(double *nom_x, double *delta_x, double *out_7316368395552197740);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1979647693272640270);
void car_H_mod_fun(double *state, double *out_2820666923051649688);
void car_f_fun(double *state, double dt, double *out_830938017298167130);
void car_F_fun(double *state, double dt, double *out_8851408027615256561);
void car_h_25(double *state, double *unused, double *out_7795708739304550937);
void car_H_25(double *state, double *unused, double *out_7724358748236314528);
void car_h_24(double *state, double *unused, double *out_8377130028693208980);
void car_H_24(double *state, double *unused, double *out_8545170901866087115);
void car_h_30(double *state, double *unused, double *out_1351097608283057666);
void car_H_30(double *state, double *unused, double *out_8204052366965988461);
void car_h_26(double *state, double *unused, double *out_5047943909130791480);
void car_H_26(double *state, double *unused, double *out_3982855429362258304);
void car_h_27(double *state, double *unused, double *out_2569801523469225990);
void car_H_27(double *state, double *unused, double *out_1021899106308281419);
void car_h_29(double *state, double *unused, double *out_2294607461184720101);
void car_H_29(double *state, double *unused, double *out_3706893762423098514);
void car_h_28(double *state, double *unused, double *out_2431871744191619655);
void car_H_28(double *state, double *unused, double *out_5670524033988424765);
void car_h_31(double *state, double *unused, double *out_7013585806150978329);
void car_H_31(double *state, double *unused, double *out_3356647327128906828);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}