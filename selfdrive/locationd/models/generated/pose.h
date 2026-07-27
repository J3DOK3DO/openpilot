#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_494363428253979517);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7744180703950466915);
void pose_H_mod_fun(double *state, double *out_8790605035544908227);
void pose_f_fun(double *state, double dt, double *out_4191169391561892498);
void pose_F_fun(double *state, double dt, double *out_7295826236279740984);
void pose_h_4(double *state, double *unused, double *out_3793117268866733474);
void pose_H_4(double *state, double *unused, double *out_5018797825701000655);
void pose_h_10(double *state, double *unused, double *out_8131512363421803191);
void pose_H_10(double *state, double *unused, double *out_8940915420831957940);
void pose_h_13(double *state, double *unused, double *out_686674294679068388);
void pose_H_13(double *state, double *unused, double *out_8852553289003524679);
void pose_h_14(double *state, double *unused, double *out_4260835658611653154);
void pose_H_14(double *state, double *unused, double *out_8101586257996372951);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}