#include "car.h"

namespace {
#define DIM 9
#define EDIM 9
#define MEDIM 9
typedef void (*Hfun)(double *, double *, double *);

double mass;

void set_mass(double x){ mass = x;}

double rotational_inertia;

void set_rotational_inertia(double x){ rotational_inertia = x;}

double center_to_front;

void set_center_to_front(double x){ center_to_front = x;}

double center_to_rear;

void set_center_to_rear(double x){ center_to_rear = x;}

double stiffness_front;

void set_stiffness_front(double x){ stiffness_front = x;}

double stiffness_rear;

void set_stiffness_rear(double x){ stiffness_rear = x;}
const static double MAHA_THRESH_25 = 3.8414588206941227;
const static double MAHA_THRESH_24 = 5.991464547107981;
const static double MAHA_THRESH_30 = 3.8414588206941227;
const static double MAHA_THRESH_26 = 3.8414588206941227;
const static double MAHA_THRESH_27 = 3.8414588206941227;
const static double MAHA_THRESH_29 = 3.8414588206941227;
const static double MAHA_THRESH_28 = 3.8414588206941227;
const static double MAHA_THRESH_31 = 3.8414588206941227;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_9081917749595232587) {
   out_9081917749595232587[0] = delta_x[0] + nom_x[0];
   out_9081917749595232587[1] = delta_x[1] + nom_x[1];
   out_9081917749595232587[2] = delta_x[2] + nom_x[2];
   out_9081917749595232587[3] = delta_x[3] + nom_x[3];
   out_9081917749595232587[4] = delta_x[4] + nom_x[4];
   out_9081917749595232587[5] = delta_x[5] + nom_x[5];
   out_9081917749595232587[6] = delta_x[6] + nom_x[6];
   out_9081917749595232587[7] = delta_x[7] + nom_x[7];
   out_9081917749595232587[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_1988639049671275534) {
   out_1988639049671275534[0] = -nom_x[0] + true_x[0];
   out_1988639049671275534[1] = -nom_x[1] + true_x[1];
   out_1988639049671275534[2] = -nom_x[2] + true_x[2];
   out_1988639049671275534[3] = -nom_x[3] + true_x[3];
   out_1988639049671275534[4] = -nom_x[4] + true_x[4];
   out_1988639049671275534[5] = -nom_x[5] + true_x[5];
   out_1988639049671275534[6] = -nom_x[6] + true_x[6];
   out_1988639049671275534[7] = -nom_x[7] + true_x[7];
   out_1988639049671275534[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_7384273333574390060) {
   out_7384273333574390060[0] = 1.0;
   out_7384273333574390060[1] = 0.0;
   out_7384273333574390060[2] = 0.0;
   out_7384273333574390060[3] = 0.0;
   out_7384273333574390060[4] = 0.0;
   out_7384273333574390060[5] = 0.0;
   out_7384273333574390060[6] = 0.0;
   out_7384273333574390060[7] = 0.0;
   out_7384273333574390060[8] = 0.0;
   out_7384273333574390060[9] = 0.0;
   out_7384273333574390060[10] = 1.0;
   out_7384273333574390060[11] = 0.0;
   out_7384273333574390060[12] = 0.0;
   out_7384273333574390060[13] = 0.0;
   out_7384273333574390060[14] = 0.0;
   out_7384273333574390060[15] = 0.0;
   out_7384273333574390060[16] = 0.0;
   out_7384273333574390060[17] = 0.0;
   out_7384273333574390060[18] = 0.0;
   out_7384273333574390060[19] = 0.0;
   out_7384273333574390060[20] = 1.0;
   out_7384273333574390060[21] = 0.0;
   out_7384273333574390060[22] = 0.0;
   out_7384273333574390060[23] = 0.0;
   out_7384273333574390060[24] = 0.0;
   out_7384273333574390060[25] = 0.0;
   out_7384273333574390060[26] = 0.0;
   out_7384273333574390060[27] = 0.0;
   out_7384273333574390060[28] = 0.0;
   out_7384273333574390060[29] = 0.0;
   out_7384273333574390060[30] = 1.0;
   out_7384273333574390060[31] = 0.0;
   out_7384273333574390060[32] = 0.0;
   out_7384273333574390060[33] = 0.0;
   out_7384273333574390060[34] = 0.0;
   out_7384273333574390060[35] = 0.0;
   out_7384273333574390060[36] = 0.0;
   out_7384273333574390060[37] = 0.0;
   out_7384273333574390060[38] = 0.0;
   out_7384273333574390060[39] = 0.0;
   out_7384273333574390060[40] = 1.0;
   out_7384273333574390060[41] = 0.0;
   out_7384273333574390060[42] = 0.0;
   out_7384273333574390060[43] = 0.0;
   out_7384273333574390060[44] = 0.0;
   out_7384273333574390060[45] = 0.0;
   out_7384273333574390060[46] = 0.0;
   out_7384273333574390060[47] = 0.0;
   out_7384273333574390060[48] = 0.0;
   out_7384273333574390060[49] = 0.0;
   out_7384273333574390060[50] = 1.0;
   out_7384273333574390060[51] = 0.0;
   out_7384273333574390060[52] = 0.0;
   out_7384273333574390060[53] = 0.0;
   out_7384273333574390060[54] = 0.0;
   out_7384273333574390060[55] = 0.0;
   out_7384273333574390060[56] = 0.0;
   out_7384273333574390060[57] = 0.0;
   out_7384273333574390060[58] = 0.0;
   out_7384273333574390060[59] = 0.0;
   out_7384273333574390060[60] = 1.0;
   out_7384273333574390060[61] = 0.0;
   out_7384273333574390060[62] = 0.0;
   out_7384273333574390060[63] = 0.0;
   out_7384273333574390060[64] = 0.0;
   out_7384273333574390060[65] = 0.0;
   out_7384273333574390060[66] = 0.0;
   out_7384273333574390060[67] = 0.0;
   out_7384273333574390060[68] = 0.0;
   out_7384273333574390060[69] = 0.0;
   out_7384273333574390060[70] = 1.0;
   out_7384273333574390060[71] = 0.0;
   out_7384273333574390060[72] = 0.0;
   out_7384273333574390060[73] = 0.0;
   out_7384273333574390060[74] = 0.0;
   out_7384273333574390060[75] = 0.0;
   out_7384273333574390060[76] = 0.0;
   out_7384273333574390060[77] = 0.0;
   out_7384273333574390060[78] = 0.0;
   out_7384273333574390060[79] = 0.0;
   out_7384273333574390060[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_853161238105894931) {
   out_853161238105894931[0] = state[0];
   out_853161238105894931[1] = state[1];
   out_853161238105894931[2] = state[2];
   out_853161238105894931[3] = state[3];
   out_853161238105894931[4] = state[4];
   out_853161238105894931[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_853161238105894931[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_853161238105894931[7] = state[7];
   out_853161238105894931[8] = state[8];
}
void F_fun(double *state, double dt, double *out_6707016052586639669) {
   out_6707016052586639669[0] = 1;
   out_6707016052586639669[1] = 0;
   out_6707016052586639669[2] = 0;
   out_6707016052586639669[3] = 0;
   out_6707016052586639669[4] = 0;
   out_6707016052586639669[5] = 0;
   out_6707016052586639669[6] = 0;
   out_6707016052586639669[7] = 0;
   out_6707016052586639669[8] = 0;
   out_6707016052586639669[9] = 0;
   out_6707016052586639669[10] = 1;
   out_6707016052586639669[11] = 0;
   out_6707016052586639669[12] = 0;
   out_6707016052586639669[13] = 0;
   out_6707016052586639669[14] = 0;
   out_6707016052586639669[15] = 0;
   out_6707016052586639669[16] = 0;
   out_6707016052586639669[17] = 0;
   out_6707016052586639669[18] = 0;
   out_6707016052586639669[19] = 0;
   out_6707016052586639669[20] = 1;
   out_6707016052586639669[21] = 0;
   out_6707016052586639669[22] = 0;
   out_6707016052586639669[23] = 0;
   out_6707016052586639669[24] = 0;
   out_6707016052586639669[25] = 0;
   out_6707016052586639669[26] = 0;
   out_6707016052586639669[27] = 0;
   out_6707016052586639669[28] = 0;
   out_6707016052586639669[29] = 0;
   out_6707016052586639669[30] = 1;
   out_6707016052586639669[31] = 0;
   out_6707016052586639669[32] = 0;
   out_6707016052586639669[33] = 0;
   out_6707016052586639669[34] = 0;
   out_6707016052586639669[35] = 0;
   out_6707016052586639669[36] = 0;
   out_6707016052586639669[37] = 0;
   out_6707016052586639669[38] = 0;
   out_6707016052586639669[39] = 0;
   out_6707016052586639669[40] = 1;
   out_6707016052586639669[41] = 0;
   out_6707016052586639669[42] = 0;
   out_6707016052586639669[43] = 0;
   out_6707016052586639669[44] = 0;
   out_6707016052586639669[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_6707016052586639669[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_6707016052586639669[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_6707016052586639669[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_6707016052586639669[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_6707016052586639669[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_6707016052586639669[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_6707016052586639669[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_6707016052586639669[53] = -9.8100000000000005*dt;
   out_6707016052586639669[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_6707016052586639669[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_6707016052586639669[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_6707016052586639669[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_6707016052586639669[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_6707016052586639669[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_6707016052586639669[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_6707016052586639669[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_6707016052586639669[62] = 0;
   out_6707016052586639669[63] = 0;
   out_6707016052586639669[64] = 0;
   out_6707016052586639669[65] = 0;
   out_6707016052586639669[66] = 0;
   out_6707016052586639669[67] = 0;
   out_6707016052586639669[68] = 0;
   out_6707016052586639669[69] = 0;
   out_6707016052586639669[70] = 1;
   out_6707016052586639669[71] = 0;
   out_6707016052586639669[72] = 0;
   out_6707016052586639669[73] = 0;
   out_6707016052586639669[74] = 0;
   out_6707016052586639669[75] = 0;
   out_6707016052586639669[76] = 0;
   out_6707016052586639669[77] = 0;
   out_6707016052586639669[78] = 0;
   out_6707016052586639669[79] = 0;
   out_6707016052586639669[80] = 1;
}
void h_25(double *state, double *unused, double *out_2381998967459310187) {
   out_2381998967459310187[0] = state[6];
}
void H_25(double *state, double *unused, double *out_758660054421155) {
   out_758660054421155[0] = 0;
   out_758660054421155[1] = 0;
   out_758660054421155[2] = 0;
   out_758660054421155[3] = 0;
   out_758660054421155[4] = 0;
   out_758660054421155[5] = 0;
   out_758660054421155[6] = 1;
   out_758660054421155[7] = 0;
   out_758660054421155[8] = 0;
}
void h_24(double *state, double *unused, double *out_8300475326001007063) {
   out_8300475326001007063[0] = state[4];
   out_8300475326001007063[1] = state[5];
}
void H_24(double *state, double *unused, double *out_3981564491343346743) {
   out_3981564491343346743[0] = 0;
   out_3981564491343346743[1] = 0;
   out_3981564491343346743[2] = 0;
   out_3981564491343346743[3] = 0;
   out_3981564491343346743[4] = 1;
   out_3981564491343346743[5] = 0;
   out_3981564491343346743[6] = 0;
   out_3981564491343346743[7] = 0;
   out_3981564491343346743[8] = 0;
   out_3981564491343346743[9] = 0;
   out_3981564491343346743[10] = 0;
   out_3981564491343346743[11] = 0;
   out_3981564491343346743[12] = 0;
   out_3981564491343346743[13] = 0;
   out_3981564491343346743[14] = 1;
   out_3981564491343346743[15] = 0;
   out_3981564491343346743[16] = 0;
   out_3981564491343346743[17] = 0;
}
void h_30(double *state, double *unused, double *out_8301479849429568988) {
   out_8301479849429568988[0] = state[4];
}
void H_30(double *state, double *unused, double *out_6917449001546037910) {
   out_6917449001546037910[0] = 0;
   out_6917449001546037910[1] = 0;
   out_6917449001546037910[2] = 0;
   out_6917449001546037910[3] = 0;
   out_6917449001546037910[4] = 1;
   out_6917449001546037910[5] = 0;
   out_6917449001546037910[6] = 0;
   out_6917449001546037910[7] = 0;
   out_6917449001546037910[8] = 0;
}
void h_26(double *state, double *unused, double *out_2889120507186530919) {
   out_2889120507186530919[0] = state[7];
}
void H_26(double *state, double *unused, double *out_3305284629815221756) {
   out_3305284629815221756[0] = 0;
   out_3305284629815221756[1] = 0;
   out_3305284629815221756[2] = 0;
   out_3305284629815221756[3] = 0;
   out_3305284629815221756[4] = 0;
   out_3305284629815221756[5] = 0;
   out_3305284629815221756[6] = 0;
   out_3305284629815221756[7] = 1;
   out_3305284629815221756[8] = 0;
}
void h_27(double *state, double *unused, double *out_8629601671821540616) {
   out_8629601671821540616[0] = state[3];
}
void H_27(double *state, double *unused, double *out_4742685689745612999) {
   out_4742685689745612999[0] = 0;
   out_4742685689745612999[1] = 0;
   out_4742685689745612999[2] = 0;
   out_4742685689745612999[3] = 1;
   out_4742685689745612999[4] = 0;
   out_4742685689745612999[5] = 0;
   out_4742685689745612999[6] = 0;
   out_4742685689745612999[7] = 0;
   out_4742685689745612999[8] = 0;
}
void h_29(double *state, double *unused, double *out_8904795734106046505) {
   out_8904795734106046505[0] = state[1];
}
void H_29(double *state, double *unused, double *out_3029322962876061966) {
   out_3029322962876061966[0] = 0;
   out_3029322962876061966[1] = 1;
   out_3029322962876061966[2] = 0;
   out_3029322962876061966[3] = 0;
   out_3029322962876061966[4] = 0;
   out_3029322962876061966[5] = 0;
   out_3029322962876061966[6] = 0;
   out_3029322962876061966[7] = 0;
   out_3029322962876061966[8] = 0;
}
void h_28(double *state, double *unused, double *out_6025196351012842965) {
   out_6025196351012842965[0] = state[0];
}
void H_28(double *state, double *unused, double *out_2053076054193468608) {
   out_2053076054193468608[0] = 1;
   out_2053076054193468608[1] = 0;
   out_2053076054193468608[2] = 0;
   out_2053076054193468608[3] = 0;
   out_2053076054193468608[4] = 0;
   out_2053076054193468608[5] = 0;
   out_2053076054193468608[6] = 0;
   out_2053076054193468608[7] = 0;
   out_2053076054193468608[8] = 0;
}
void h_31(double *state, double *unused, double *out_4388836258891040749) {
   out_4388836258891040749[0] = state[8];
}
void H_31(double *state, double *unused, double *out_7077433910566238408) {
   out_7077433910566238408[0] = 0;
   out_7077433910566238408[1] = 0;
   out_7077433910566238408[2] = 0;
   out_7077433910566238408[3] = 0;
   out_7077433910566238408[4] = 0;
   out_7077433910566238408[5] = 0;
   out_7077433910566238408[6] = 0;
   out_7077433910566238408[7] = 0;
   out_7077433910566238408[8] = 1;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_25, H_25, NULL, in_z, in_R, in_ea, MAHA_THRESH_25);
}
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<2, 3, 0>(in_x, in_P, h_24, H_24, NULL, in_z, in_R, in_ea, MAHA_THRESH_24);
}
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_30, H_30, NULL, in_z, in_R, in_ea, MAHA_THRESH_30);
}
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_26, H_26, NULL, in_z, in_R, in_ea, MAHA_THRESH_26);
}
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_27, H_27, NULL, in_z, in_R, in_ea, MAHA_THRESH_27);
}
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_29, H_29, NULL, in_z, in_R, in_ea, MAHA_THRESH_29);
}
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_28, H_28, NULL, in_z, in_R, in_ea, MAHA_THRESH_28);
}
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_31, H_31, NULL, in_z, in_R, in_ea, MAHA_THRESH_31);
}
void car_err_fun(double *nom_x, double *delta_x, double *out_9081917749595232587) {
  err_fun(nom_x, delta_x, out_9081917749595232587);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1988639049671275534) {
  inv_err_fun(nom_x, true_x, out_1988639049671275534);
}
void car_H_mod_fun(double *state, double *out_7384273333574390060) {
  H_mod_fun(state, out_7384273333574390060);
}
void car_f_fun(double *state, double dt, double *out_853161238105894931) {
  f_fun(state,  dt, out_853161238105894931);
}
void car_F_fun(double *state, double dt, double *out_6707016052586639669) {
  F_fun(state,  dt, out_6707016052586639669);
}
void car_h_25(double *state, double *unused, double *out_2381998967459310187) {
  h_25(state, unused, out_2381998967459310187);
}
void car_H_25(double *state, double *unused, double *out_758660054421155) {
  H_25(state, unused, out_758660054421155);
}
void car_h_24(double *state, double *unused, double *out_8300475326001007063) {
  h_24(state, unused, out_8300475326001007063);
}
void car_H_24(double *state, double *unused, double *out_3981564491343346743) {
  H_24(state, unused, out_3981564491343346743);
}
void car_h_30(double *state, double *unused, double *out_8301479849429568988) {
  h_30(state, unused, out_8301479849429568988);
}
void car_H_30(double *state, double *unused, double *out_6917449001546037910) {
  H_30(state, unused, out_6917449001546037910);
}
void car_h_26(double *state, double *unused, double *out_2889120507186530919) {
  h_26(state, unused, out_2889120507186530919);
}
void car_H_26(double *state, double *unused, double *out_3305284629815221756) {
  H_26(state, unused, out_3305284629815221756);
}
void car_h_27(double *state, double *unused, double *out_8629601671821540616) {
  h_27(state, unused, out_8629601671821540616);
}
void car_H_27(double *state, double *unused, double *out_4742685689745612999) {
  H_27(state, unused, out_4742685689745612999);
}
void car_h_29(double *state, double *unused, double *out_8904795734106046505) {
  h_29(state, unused, out_8904795734106046505);
}
void car_H_29(double *state, double *unused, double *out_3029322962876061966) {
  H_29(state, unused, out_3029322962876061966);
}
void car_h_28(double *state, double *unused, double *out_6025196351012842965) {
  h_28(state, unused, out_6025196351012842965);
}
void car_H_28(double *state, double *unused, double *out_2053076054193468608) {
  H_28(state, unused, out_2053076054193468608);
}
void car_h_31(double *state, double *unused, double *out_4388836258891040749) {
  h_31(state, unused, out_4388836258891040749);
}
void car_H_31(double *state, double *unused, double *out_7077433910566238408) {
  H_31(state, unused, out_7077433910566238408);
}
void car_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
void car_set_mass(double x) {
  set_mass(x);
}
void car_set_rotational_inertia(double x) {
  set_rotational_inertia(x);
}
void car_set_center_to_front(double x) {
  set_center_to_front(x);
}
void car_set_center_to_rear(double x) {
  set_center_to_rear(x);
}
void car_set_stiffness_front(double x) {
  set_stiffness_front(x);
}
void car_set_stiffness_rear(double x) {
  set_stiffness_rear(x);
}
}

const EKF car = {
  .name = "car",
  .kinds = { 25, 24, 30, 26, 27, 29, 28, 31 },
  .feature_kinds = {  },
  .f_fun = car_f_fun,
  .F_fun = car_F_fun,
  .err_fun = car_err_fun,
  .inv_err_fun = car_inv_err_fun,
  .H_mod_fun = car_H_mod_fun,
  .predict = car_predict,
  .hs = {
    { 25, car_h_25 },
    { 24, car_h_24 },
    { 30, car_h_30 },
    { 26, car_h_26 },
    { 27, car_h_27 },
    { 29, car_h_29 },
    { 28, car_h_28 },
    { 31, car_h_31 },
  },
  .Hs = {
    { 25, car_H_25 },
    { 24, car_H_24 },
    { 30, car_H_30 },
    { 26, car_H_26 },
    { 27, car_H_27 },
    { 29, car_H_29 },
    { 28, car_H_28 },
    { 31, car_H_31 },
  },
  .updates = {
    { 25, car_update_25 },
    { 24, car_update_24 },
    { 30, car_update_30 },
    { 26, car_update_26 },
    { 27, car_update_27 },
    { 29, car_update_29 },
    { 28, car_update_28 },
    { 31, car_update_31 },
  },
  .Hes = {
  },
  .sets = {
    { "mass", car_set_mass },
    { "rotational_inertia", car_set_rotational_inertia },
    { "center_to_front", car_set_center_to_front },
    { "center_to_rear", car_set_center_to_rear },
    { "stiffness_front", car_set_stiffness_front },
    { "stiffness_rear", car_set_stiffness_rear },
  },
  .extra_routines = {
  },
};

ekf_lib_init(car)
