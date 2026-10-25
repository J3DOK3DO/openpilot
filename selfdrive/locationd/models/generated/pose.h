#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_6672914167572980790);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7750354326522111493);
void pose_H_mod_fun(double *state, double *out_839860879621378337);
void pose_f_fun(double *state, double dt, double *out_4259182462982083528);
void pose_F_fun(double *state, double dt, double *out_3243909512724105051);
void pose_h_4(double *state, double *unused, double *out_4501441890577505558);
void pose_H_4(double *state, double *unused, double *out_957367488565514356);
void pose_h_10(double *state, double *unused, double *out_4701543042744826127);
void pose_H_10(double *state, double *unused, double *out_1475315339015463538);
void pose_h_13(double *state, double *unused, double *out_8766901177225402962);
void pose_H_13(double *state, double *unused, double *out_2254906336766818445);
void pose_h_14(double *state, double *unused, double *out_1552114113674913175);
void pose_H_14(double *state, double *unused, double *out_3005873367773970173);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}