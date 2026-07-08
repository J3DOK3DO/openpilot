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
void car_err_fun(double *nom_x, double *delta_x, double *out_1393219424364542669);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8544281472794776121);
void car_H_mod_fun(double *state, double *out_542719001883324995);
void car_f_fun(double *state, double dt, double *out_9203753821438188332);
void car_F_fun(double *state, double dt, double *out_1821220582526959893);
void car_h_25(double *state, double *unused, double *out_7848411301120641124);
void car_H_25(double *state, double *unused, double *out_6136977117952979916);
void car_h_24(double *state, double *unused, double *out_8292657587405145092);
void car_H_24(double *state, double *unused, double *out_3964327518947480350);
void car_h_30(double *state, double *unused, double *out_1692964105279980995);
void car_H_30(double *state, double *unused, double *out_8655310076460228543);
void car_h_26(double *state, double *unused, double *out_6694637372940826640);
void car_H_26(double *state, double *unused, double *out_2395473799078923692);
void car_h_27(double *state, double *unused, double *out_3658606002300167844);
void car_H_27(double *state, double *unused, double *out_6480546764659803632);
void car_h_29(double *state, double *unused, double *out_3383411940015661955);
void car_H_29(double *state, double *unused, double *out_9165541420774620727);
void car_h_28(double *state, double *unused, double *out_2219679485258547244);
void car_H_28(double *state, double *unused, double *out_4083142403705090153);
void car_h_31(double *state, double *unused, double *out_8123605363405147013);
void car_H_31(double *state, double *unused, double *out_1769265696845572216);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}