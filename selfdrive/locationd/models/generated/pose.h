#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_2355293272416553220);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_4800523972292248179);
void pose_H_mod_fun(double *state, double *out_1756056773937278960);
void pose_f_fun(double *state, double dt, double *out_4431905570801982118);
void pose_F_fun(double *state, double dt, double *out_2871178270800665939);
void pose_h_4(double *state, double *unused, double *out_3846978595453462265);
void pose_H_4(double *state, double *unused, double *out_2510217775991991567);
void pose_h_10(double *state, double *unused, double *out_7920856264594772367);
void pose_H_10(double *state, double *unused, double *out_8226281178388112719);
void pose_h_13(double *state, double *unused, double *out_8094608070185368102);
void pose_H_13(double *state, double *unused, double *out_8325895089400859120);
void pose_h_14(double *state, double *unused, double *out_1490158875401441001);
void pose_H_14(double *state, double *unused, double *out_572570656303380729);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}