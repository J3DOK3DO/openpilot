#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_4967863734907407968);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_554301816764323460);
void pose_H_mod_fun(double *state, double *out_3047027985808074405);
void pose_f_fun(double *state, double dt, double *out_986492010673501731);
void pose_F_fun(double *state, double dt, double *out_4336070434649428420);
void pose_h_4(double *state, double *unused, double *out_5526642384709914880);
void pose_H_4(double *state, double *unused, double *out_5691168246274914733);
void pose_h_10(double *state, double *unused, double *out_6728942981811315921);
void pose_H_10(double *state, double *unused, double *out_4278506402956144046);
void pose_h_13(double *state, double *unused, double *out_1205451540469147746);
void pose_H_13(double *state, double *unused, double *out_8903442071607247534);
void pose_h_14(double *state, double *unused, double *out_3303339494882182614);
void pose_H_14(double *state, double *unused, double *out_8792334971095152354);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}