#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_7616755969345465164);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_2983579217144166569);
void pose_H_mod_fun(double *state, double *out_7561037298851331177);
void pose_f_fun(double *state, double dt, double *out_5713485962747764656);
void pose_F_fun(double *state, double dt, double *out_958271563642232375);
void pose_h_4(double *state, double *unused, double *out_4832992228856902742);
void pose_H_4(double *state, double *unused, double *out_2408518913812250442);
void pose_h_10(double *state, double *unused, double *out_3497927463584229027);
void pose_H_10(double *state, double *unused, double *out_4949237892416765352);
void pose_h_13(double *state, double *unused, double *out_7372319986312258601);
void pose_H_13(double *state, double *unused, double *out_803754911520082359);
void pose_h_14(double *state, double *unused, double *out_1827110187090498104);
void pose_H_14(double *state, double *unused, double *out_1554721942527234087);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}