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
void car_err_fun(double *nom_x, double *delta_x, double *out_1216716447356597110);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_3846971901517960066);
void car_H_mod_fun(double *state, double *out_3686417524826046061);
void car_f_fun(double *state, double dt, double *out_4356782296703109782);
void car_F_fun(double *state, double dt, double *out_8663241758043788496);
void car_h_25(double *state, double *unused, double *out_5968951969417460595);
void car_H_25(double *state, double *unused, double *out_6445211999246796602);
void car_h_24(double *state, double *unused, double *out_6794211406798157438);
void car_H_24(double *state, double *unused, double *out_2462888847849028704);
void car_h_30(double *state, double *unused, double *out_3340074819608239839);
void car_H_30(double *state, double *unused, double *out_5084841732971138259);
void car_h_26(double *state, double *unused, double *out_1661598448052605806);
void car_H_26(double *state, double *unused, double *out_8697006104701954413);
void car_h_27(double *state, double *unused, double *out_8589620342754085887);
void car_H_27(double *state, double *unused, double *out_7259605044771563170);
void car_h_29(double *state, double *unused, double *out_2396564966706577404);
void car_H_29(double *state, double *unused, double *out_8972967771641114203);
void car_h_28(double *state, double *unused, double *out_3587947075093240242);
void car_H_28(double *state, double *unused, double *out_4391377284998906839);
void car_h_31(double *state, double *unused, double *out_1218000935040597734);
void car_H_31(double *state, double *unused, double *out_6475857961123757030);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}