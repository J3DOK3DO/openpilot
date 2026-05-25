#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_671460305092226609);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_8594657692984849886);
void pose_H_mod_fun(double *state, double *out_6213728924716372500);
void pose_f_fun(double *state, double dt, double *out_5585784149500665013);
void pose_F_fun(double *state, double dt, double *out_3643040962092382423);
void pose_h_4(double *state, double *unused, double *out_8854338774183858135);
void pose_H_4(double *state, double *unused, double *out_8529830693005134694);
void pose_h_10(double *state, double *unused, double *out_5059906078839414114);
void pose_H_10(double *state, double *unused, double *out_3583999604245367895);
void pose_h_13(double *state, double *unused, double *out_7263365611470923251);
void pose_H_13(double *state, double *unused, double *out_6704639555372084121);
void pose_h_14(double *state, double *unused, double *out_7190737918139558978);
void pose_H_14(double *state, double *unused, double *out_5953672524364932393);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}