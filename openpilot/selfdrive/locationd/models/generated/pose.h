#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_6287899668351208780);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_4433323129515526623);
void pose_H_mod_fun(double *state, double *out_3663906507468251580);
void pose_f_fun(double *state, double dt, double *out_4774185451746620342);
void pose_F_fun(double *state, double dt, double *out_5859736115803136918);
void pose_h_4(double *state, double *unused, double *out_4561285742833549430);
void pose_H_4(double *state, double *unused, double *out_389684428677302327);
void pose_h_10(double *state, double *unused, double *out_2497391090579338133);
void pose_H_10(double *state, double *unused, double *out_1020416197739407059);
void pose_h_13(double *state, double *unused, double *out_1021891902817546794);
void pose_H_13(double *state, double *unused, double *out_8000315636994003256);
void pose_h_14(double *state, double *unused, double *out_3304628372857441851);
void pose_H_14(double *state, double *unused, double *out_4352925285016786856);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}